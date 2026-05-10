"""
API Layer - FastAPI (M7: UX Conversacional & Governanca).

Camada fina de HTTP/WebSocket. Nao contem logica de negocio.
Todas as acoes passam pela State Machine (source of truth)
e delegam ao Voice Pipeline Layer.
"""
import os
import sys
import json
import time
import asyncio
import threading
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Garantir imports do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.state_machine import ConversationStateMachine, ConversationState, StateEvent
from src.api.text_sanitizer import sanitize_for_tts
from src.llm.ollama_client import OllamaClient
from src.stt.whisper_engine import WhisperEngine
from src.tts.tts_engine import PiperTTSEngine
from src.session.session_manager import SessionManager

import re

# ─── Conversational Governance ───────────────────────────────
SYSTEM_PROMPT = (
    "Você é um assistente de voz pessoal. "
    "Responda de forma curta, natural e direta, como em uma conversa falada. "
    "Use português brasileiro informal e amigável. "
    "Nunca use formatação markdown, listas numeradas, bullets, negrito ou cabeçalhos. "
    "Não repita o que o usuário disse. "
    "Não use emojis. "
    "Limite suas respostas a no máximo 3 frases, a menos que o usuário peça explicitamente uma explicação detalhada. "
    "Responda como se estivesse falando, não escrevendo."
)

# ─── Natural Chunker ─────────────────────────────────────────
MIN_CHUNK_CHARS = 40
MAX_CHUNK_CHARS = 250

_sentence_split = re.compile(r'(?<=[.!?])\s+')

def chunk_for_tts(text: str) -> list[str]:
    """
    Divide texto sanitizado em chunks otimizados para fala natural.
    Regras:
      - Mínimo MIN_CHUNK_CHARS por chunk (merge frases curtas).
      - Máximo MAX_CHUNK_CHARS (split frases longas demais).
      - Sem chunks triviais ("1.", "Ok.").
    """
    # Sanitizar ANTES do chunking
    clean = sanitize_for_tts(text)
    
    # Split por sentenças
    raw_sentences = _sentence_split.split(clean)
    raw_sentences = [s.strip() for s in raw_sentences if s.strip()]
    
    if not raw_sentences:
        return [clean] if clean else []
    
    chunks = []
    buffer = ""
    
    for sentence in raw_sentences:
        candidate = (buffer + " " + sentence).strip() if buffer else sentence
        
        if len(candidate) > MAX_CHUNK_CHARS and buffer:
            # Flush buffer, start new with current sentence
            chunks.append(buffer)
            buffer = sentence
        else:
            buffer = candidate
    
    if buffer:
        # Se o último chunk é muito curto, merge com o anterior
        if chunks and len(buffer) < MIN_CHUNK_CHARS:
            chunks[-1] = chunks[-1] + " " + buffer
        else:
            chunks.append(buffer)
    
    return chunks


# ─── Available Voices ─────────────────────────────────────────
AVAILABLE_VOICES = {
    "pt_BR-faber-medium": {
        "name": "Faber",
        "lang": "pt-BR",
        "gender": "Masculina",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium/pt_BR-faber-medium",
    },
    "pt_BR-edresson-low": {
        "name": "Edresson",
        "lang": "pt-BR",
        "gender": "Masculina",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/edresson/low/pt_BR-edresson-low",
    },
}


# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app):
    on_state_event._loop = asyncio.get_event_loop()
    yield


# ─── App Setup ───────────────────────────────────────────────
app = FastAPI(title="Voice Lab", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global State ────────────────────────────────────────────
state_machine = ConversationStateMachine()
connected_clients: List[WebSocket] = []

# Pipeline components (lazy init)
stt_engine = None
llm_client = None
tts_engines: dict[str, PiperTTSEngine] = {}

# Config
current_config = {
    "llm_model": "gemma3:4b",
    "tts_voice": "pt_BR-faber-medium",
    "stt_model": "base",
    "mode": "premium",
    "voice_enabled": True,
}

MODE_MODEL_MAP = {
    "fast": "qwen2.5:0.5b",
    "standard": "llama3.2:1b",
    "premium": "gemma3:4b",
}


def get_stt():
    global stt_engine
    if stt_engine is None:
        stt_engine = WhisperEngine(model_size=current_config["stt_model"])
    return stt_engine


def get_llm():
    global llm_client
    if llm_client is None or llm_client.model != current_config["llm_model"]:
        llm_client = OllamaClient(model=current_config["llm_model"])
    return llm_client


def get_tts(voice_name: str = None):
    voice = voice_name or current_config["tts_voice"]
    if voice not in tts_engines:
        tts_engines[voice] = PiperTTSEngine(model_name=voice)
    return tts_engines[voice]


# ─── WebSocket Event Broadcasting ────────────────────────────
async def broadcast_event(event: dict):
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


def on_state_event(event: StateEvent):
    loop = getattr(on_state_event, '_loop', None)
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_event(event.to_dict()), loop)


state_machine.add_listener(on_state_event)


# ─── Static Files ────────────────────────────────────────────
web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "web")


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(web_dir, "index.html"))


app.mount("/static", StaticFiles(directory=web_dir), name="static")


# ─── REST Endpoints ──────────────────────────────────────────
@app.get("/api/status")
async def get_status():
    return {"state": state_machine.state.value, "config": current_config}


@app.get("/api/models")
async def get_models():
    return {
        "llm": list(MODE_MODEL_MAP.values()),
        "modes": list(MODE_MODEL_MAP.keys()),
        "tts_voices": {k: v for k, v in AVAILABLE_VOICES.items()},
    }


@app.post("/api/config")
async def update_config(config: dict):
    global llm_client
    if "mode" in config:
        current_config["mode"] = config["mode"]
        current_config["llm_model"] = MODE_MODEL_MAP.get(config["mode"], current_config["llm_model"])
        llm_client = None
    if "llm_model" in config:
        current_config["llm_model"] = config["llm_model"]
        llm_client = None
    if "tts_voice" in config and config["tts_voice"] in AVAILABLE_VOICES:
        current_config["tts_voice"] = config["tts_voice"]
    if "voice_enabled" in config:
        current_config["voice_enabled"] = bool(config["voice_enabled"])
    return {"status": "ok", "config": current_config}


@app.get("/api/sessions")
async def get_sessions():
    sessions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "sessions")
    if not os.path.exists(sessions_dir):
        return {"sessions": []}
    dirs = sorted(os.listdir(sessions_dir), reverse=True)[:20]
    sessions = []
    for d in dirs:
        meta_path = os.path.join(sessions_dir, d, "llm", "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                sessions.append(json.load(f))
        else:
            sessions.append({"session_id": d, "status": "incomplete"})
    return {"sessions": sessions}


# ─── WebSocket ────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    print(f"[WS] Cliente conectado. Total: {len(connected_clients)}")

    await ws.send_json({
        "event": "connected",
        "data": {
            "state": state_machine.state.value,
            "config": current_config,
            "voices": {k: v for k, v in AVAILABLE_VOICES.items()},
        },
        "timestamp": time.time(),
    })

    try:
        while True:
            msg = await ws.receive_json()
            action = msg.get("action")

            if action == "start_listening":
                if state_machine.transition_to(ConversationState.LISTENING):
                    await ws.send_json({"event": "ack", "data": {"action": "start_listening"}, "timestamp": time.time()})

            elif action == "audio_data":
                audio_b64 = msg.get("audio")
                if audio_b64 and state_machine.state == ConversationState.LISTENING:
                    state_machine.transition_to(ConversationState.TRANSCRIBING)
                    threading.Thread(target=process_voice_pipeline, args=(audio_b64,), daemon=True).start()

            elif action == "text_message":
                text = msg.get("text", "").strip()
                if text and state_machine.state == ConversationState.IDLE:
                    state_machine.transition_to(ConversationState.LISTENING)
                    state_machine.transition_to(ConversationState.TRANSCRIBING)
                    state_machine.emit_event("transcription_complete", {"text": text, "language": "text", "stt_time": 0})
                    threading.Thread(target=process_text_pipeline, args=(text,), daemon=True).start()

            elif action == "config":
                if "mode" in msg:
                    current_config["mode"] = msg["mode"]
                    current_config["llm_model"] = MODE_MODEL_MAP.get(msg["mode"], current_config["llm_model"])
                    global llm_client
                    llm_client = None
                if "tts_voice" in msg:
                    current_config["tts_voice"] = msg["tts_voice"]
                if "voice_enabled" in msg:
                    current_config["voice_enabled"] = bool(msg["voice_enabled"])

            elif action == "cancel":
                state_machine.reset()

    except WebSocketDisconnect:
        pass
    finally:
        if ws in connected_clients:
            connected_clients.remove(ws)
        print(f"[WS] Cliente desconectado. Total: {len(connected_clients)}")


# ─── Pipeline: Text Input (skip STT) ─────────────────────────
def process_text_pipeline(user_text: str):
    """Pipeline para input de texto — skip STT, vai direto ao LLM."""
    session = SessionManager()
    try:
        _run_llm_tts_pipeline(session, user_text, stt_time=0, stt_info=None)
    except Exception as e:
        state_machine.emit_event("error", {"message": str(e)})
        print(f"[Pipeline] ERRO: {e}")
    finally:
        state_machine.reset()


# ─── Pipeline: Voice Input ────────────────────────────────────
def process_voice_pipeline(audio_b64: str):
    """Pipeline completo: Audio → STT → LLM → TTS."""
    import base64
    import subprocess

    session = SessionManager()
    input_path = session.get_path("mic_input")

    try:
        audio_bytes = base64.b64decode(audio_b64)
        webm_path = input_path.replace(".wav", ".webm")
        with open(webm_path, "wb") as f:
            f.write(audio_bytes)

        result = subprocess.run(
            ["ffmpeg", "-y", "-i", webm_path, "-ar", "16000", "-ac", "1", "-f", "wav", input_path],
            capture_output=True, timeout=15,
        )
        if result.returncode != 0:
            state_machine.emit_event("error", {"message": f"Falha na conversão de audio: {result.stderr.decode()[:200]}"})
            state_machine.reset()
            return

        stt = get_stt()
        transcribed_text, stt_time, stt_info = stt.transcribe(input_path)

        if not transcribed_text.strip():
            state_machine.emit_event("error", {"message": "Nenhum texto detectado no audio."})
            state_machine.reset()
            return

        state_machine.emit_event("transcription_complete", {
            "text": transcribed_text,
            "language": getattr(stt_info, "language", "unknown"),
            "stt_time": round(stt_time, 3),
        })

        _run_llm_tts_pipeline(session, transcribed_text, stt_time, stt_info)

    except Exception as e:
        state_machine.emit_event("error", {"message": str(e)})
        print(f"[Pipeline] ERRO: {e}")
    finally:
        state_machine.reset()


# ─── Shared LLM → TTS Pipeline ───────────────────────────────
def _run_llm_tts_pipeline(session, user_text: str, stt_time: float, stt_info):
    """Core pipeline compartilhado entre voice e text input."""
    state_machine.transition_to(ConversationState.THINKING)

    llm = get_llm()
    tts = get_tts()

    full_response = ""
    ttft = None
    ttfs = None
    chunks_meta = []
    chunk_count = 0
    llm_start = time.time()

    tts_dir = os.path.join(session.session_dir, "tts", "chunks")
    os.makedirs(tts_dir, exist_ok=True)

    # Buffer for natural chunking — accumulate raw text, detect sentences
    raw_buffer = ""
    # Regex: match text ending with sentence terminators
    _sentence_end = re.compile(r'[.!?]\s*$')

    print(f"[LLM] Streaming com system prompt otimizado para voz...")
    for token in llm.generate_stream(user_text, system_prompt=SYSTEM_PROMPT):
        if ttft is None:
            ttft = time.time() - llm_start
            state_machine.emit_event("metrics_updated", {"ttft": round(ttft, 3)})

        full_response += token
        raw_buffer += token

        # Emit partial text (original, com markdown se houver)
        state_machine.emit_event("llm_chunk", {"token": token, "full_text": full_response})

        # Detect sentence boundary in buffer
        if _sentence_end.search(raw_buffer) and len(raw_buffer.strip()) >= MIN_CHUNK_CHARS:
            # Sanitize the completed sentence(s)
            clean_chunk = sanitize_for_tts(raw_buffer).strip()
            raw_buffer = ""

            if clean_chunk and current_config["voice_enabled"]:
                if not state_machine.state == ConversationState.SPEAKING:
                    state_machine.transition_to(ConversationState.SPEAKING)

                chunk_count += 1
                chunk_path = os.path.join(tts_dir, f"chunk_{chunk_count:03d}.wav")
                tts_start = time.time()
                tts.generate_audio(clean_chunk, chunk_path)
                tts_gen_time = time.time() - tts_start

                if ttfs is None:
                    ttfs = time.time() - llm_start
                    state_machine.emit_event("metrics_updated", {"ttfs": round(ttfs, 3)})

                state_machine.emit_event("tts_chunk_ready", {"chunk_id": chunk_count, "text": clean_chunk, "gen_time": round(tts_gen_time, 3)})
                tts.play_audio(chunk_path)
                state_machine.emit_event("playback_finished", {"chunk_id": chunk_count})

                chunks_meta.append({"id": chunk_count, "text": clean_chunk, "path": chunk_path, "gen_time": round(tts_gen_time, 3)})

    # Flush remaining buffer
    remaining = sanitize_for_tts(raw_buffer).strip()
    if remaining and current_config["voice_enabled"]:
        if not state_machine.state == ConversationState.SPEAKING:
            state_machine.transition_to(ConversationState.SPEAKING)
        chunk_count += 1
        chunk_path = os.path.join(tts_dir, f"chunk_{chunk_count:03d}.wav")
        tts.generate_audio(remaining, chunk_path)
        tts.play_audio(chunk_path)
        chunks_meta.append({"id": chunk_count, "text": remaining, "path": chunk_path, "gen_time": 0})

    total_llm_time = time.time() - llm_start

    # If voice was disabled, still transition through states
    if not current_config["voice_enabled"] and state_machine.state == ConversationState.THINKING:
        state_machine.transition_to(ConversationState.SPEAKING)

    # Persist
    session.save_text("stt_transcription", user_text)
    session.save_text("llm_prompt", user_text)
    session.save_text("llm_response", full_response)

    lang = getattr(stt_info, "language", "text") if stt_info else "text"
    prob = getattr(stt_info, "language_probability", 0.0) if stt_info else 0.0

    session.build_metadata(
        stt_model=current_config["stt_model"],
        llm_model=current_config["llm_model"],
        tts_model=current_config["tts_voice"],
        stt_time=stt_time,
        llm_time=total_llm_time,
        tts_time=0,
        detected_language=lang,
        detected_confidence=prob,
        status="success",
        transcribed_text=user_text,
        llm_response_text=full_response,
        ttft=ttft,
        ttfs=ttfs,
        chunks=chunks_meta,
    )

    state_machine.emit_event("pipeline_complete", {
        "session_id": session.timestamp,
        "transcription": user_text,
        "response": full_response,
        "ttft": round(ttft, 3) if ttft else None,
        "ttfs": round(ttfs, 3) if ttfs else None,
        "total_time": round(total_llm_time, 3),
        "chunks_count": chunk_count,
        "model": current_config["llm_model"],
        "voice_enabled": current_config["voice_enabled"],
    })


# ─── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("[VoiceLab] Iniciando servidor em http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
