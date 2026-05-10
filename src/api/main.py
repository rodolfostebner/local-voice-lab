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
import re
from typing import List, Optional, Any
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

MODE_MODEL_MAP = {
    "fast": "qwen2.5:0.5b",
    "standard": "llama3.2:1b",
    "premium": "gemma3:4b",
}



# ─── Inference Queue & Worker ────────────────────────────────
request_queue = asyncio.Queue()
reconnect_count = 0  # Global monitor for stability audit

async def inference_worker():
    """Consome a fila de inferência sequencialmente para evitar sobrecarga."""
    print("[Queue] Worker iniciado.")
    while True:
        task = await request_queue.get()
        func, args, kwargs = task
        client_id = kwargs.get("client_id")
        session = manager.get_session(client_id)
        try:
            # Executa a pipeline (bloqueante, em thread para não travar o loop)
            # Mas a fila garante que apenas UM por vez seja processado
            await asyncio.to_thread(func, *args, **kwargs)
        except Exception as e:
            print(f"[Queue] Erro ao processar task: {e}")
            if session:
                session.state_machine.emit_event("error", {"message": str(e)})
        finally:
            # Garante que o estado sempre volta para IDLE após processamento
            if session:
                session.state_machine.reset()
            request_queue.task_done()

# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app):
    lifespan._loop = asyncio.get_event_loop()
    # Inicia o worker de inferência
    worker_task = asyncio.create_task(inference_worker())
    yield
    worker_task.cancel()


# ─── App Setup ───────────────────────────────────────────────
app = FastAPI(title="Voice Lab", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="web"), name="static")
app.mount("/sessions", StaticFiles(directory="output/sessions"), name="sessions")


# ─── Multi-Client Session Management ──────────────────────────
class ClientSession:
    """Encapsula o estado completo de um cliente conectado."""
    def __init__(self, client_id: str, websocket: WebSocket):
        self.client_id = client_id
        self.websocket = websocket
        self.state_machine = ConversationStateMachine()
        self.config = {
            "llm_model": "gemma3:4b",
            "tts_voice": "pt_BR-faber-medium",
            "stt_model": "base",
            "mode": "premium",
            "voice_enabled": True,
        }
        # Registra listener para este cliente específico
        self.state_machine.add_listener(self._on_state_event)

    def _on_state_event(self, event):
        """Envia eventos da State Machine apenas para este cliente via WebSocket."""
        loop = getattr(lifespan, "_loop", None)
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.websocket.send_json(event.to_dict()), loop)

class ConnectionManager:
    def __init__(self):
        self.active_sessions: dict[str, ClientSession] = {}

    def connect(self, client_id: str, websocket: WebSocket) -> ClientSession:
        session = ClientSession(client_id, websocket)
        self.active_sessions[client_id] = session
        return session

    def disconnect(self, client_id: str):
        if client_id in self.active_sessions:
            del self.active_sessions[client_id]

    def get_session(self, client_id: str) -> Optional[ClientSession]:
        return self.active_sessions.get(client_id)

manager = ConnectionManager()


# ─── Global Resources (Shared) ───────────────────────────────
stt_engine = None
llm_client = None
tts_engines: dict[str, PiperTTSEngine] = {}

def get_stt(model_name="base"):
    global stt_engine
    # Se mudar o modelo, reinicializamos o engine (ou inicializa o primeiro)
    if stt_engine is None or getattr(stt_engine, "model_size", None) != model_name:
        stt_engine = WhisperEngine(model_size=model_name)
    return stt_engine

def get_llm(model_name):
    global llm_client
    if llm_client is None or llm_client.model != model_name:
        llm_client = OllamaClient(model=model_name)
    return llm_client

def get_tts(voice_name):
    if voice_name not in tts_engines:
        tts_engines[voice_name] = PiperTTSEngine(model_name=voice_name)
    return tts_engines[voice_name]


# ─── Static Files ────────────────────────────────────────────
web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "web")


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(web_dir, "index.html"))


app.mount("/static", StaticFiles(directory=web_dir), name="static")


# ─── REST Endpoints ──────────────────────────────────────────
@app.get("/api/status")
async def get_status():
    """Status global simplificado."""
    return {"status": "operational", "active_clients": len(manager.active_sessions)}


@app.get("/api/models")
async def get_models():
    return {
        "llm": list(MODE_MODEL_MAP.values()),
        "modes": list(MODE_MODEL_MAP.keys()),
        "tts_voices": {k: v for k, v in AVAILABLE_VOICES.items()},
    }


# REMOVED: update_config REST endpoint (now handled via WebSocket per-client)


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


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    import uuid
    await ws.accept()
    client_id = str(uuid.uuid4())
    session = manager.connect(client_id, ws)
    print(f"[WS] Cliente conectado ({client_id}). Total: {len(manager.active_sessions)}")

    await ws.send_json({
        "event": "connected",
        "data": {
            "state": session.state_machine.state.value,
            "config": session.config,
            "voices": {k: v for k, v in AVAILABLE_VOICES.items()},
        },
        "timestamp": time.time(),
    })

    try:
        while True:
            msg = await ws.receive_json()
            action = msg.get("action")

            if action == "start_listening":
                if session.state_machine.transition_to(ConversationState.LISTENING):
                    await ws.send_json({"event": "ack", "data": {"action": "start_listening"}, "timestamp": time.time()})

            elif action == "audio_data":
                audio_b64 = msg.get("audio")
                if audio_b64 and session.state_machine.state == ConversationState.LISTENING:
                    session.state_machine.transition_to(ConversationState.TRANSCRIBING)
                    threading.Thread(target=process_voice_pipeline, args=(audio_b64, client_id), daemon=True).start()

            elif action == "text_message":
                text = msg.get("text", "").strip()
                if text and session.state_machine.state == ConversationState.IDLE:
                    session.state_machine.transition_to(ConversationState.LISTENING)
                    session.state_machine.transition_to(ConversationState.TRANSCRIBING)
                    session.state_machine.emit_event("transcription_complete", {"text": text, "language": "text", "stt_time": 0})
                    threading.Thread(target=process_text_pipeline, args=(text, client_id), daemon=True).start()

            elif action == "config":
                if "mode" in msg:
                    session.config["mode"] = msg["mode"]
                    session.config["llm_model"] = MODE_MODEL_MAP.get(msg["mode"], session.config["llm_model"])
                if "tts_voice" in msg:
                    session.config["tts_voice"] = msg["tts_voice"]
                if "voice_enabled" in msg:
                    session.config["voice_enabled"] = bool(msg["voice_enabled"])

            elif action == "cancel":
                session.state_machine.reset()
                
            elif action == "clear_chat":
                session.state_machine.reset()
                await ws.send_json({"event": "chat_cleared", "timestamp": time.time()})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS] Conexão encerrada inesperadamente: {e}")
    finally:
        manager.disconnect(client_id)
        print(f"[WS] Cliente desconectado ({client_id}). Total: {len(manager.active_sessions)}")


# ─── Pipeline: Text Input (skip STT) ─────────────────────────
def process_text_pipeline(user_text: str, client_id: str):
    """Pipeline para input de texto — skip STT, vai direto ao LLM."""
    session_obj = manager.get_session(client_id)
    if not session_obj: return

    session_data = SessionManager()
    
    # Se já houver alguém na fila, avisamos o usuário
    if request_queue.qsize() > 0:
        session_obj.state_machine.transition_to(ConversationState.QUEUED, {"queue_pos": request_queue.qsize()})

    # Adiciona à fila de inferência
    asyncio.run_coroutine_threadsafe(
        request_queue.put((_run_llm_tts_pipeline, (session_data, user_text, 0, None), {"client_id": client_id})),
        lifespan._loop
    )


# ─── Pipeline: Voice Input ────────────────────────────────────
def process_voice_pipeline(audio_b64: str, client_id: str):
    """Pipeline completo: Audio → STT → LLM → TTS."""
    import base64
    import subprocess

    session_obj = manager.get_session(client_id)
    if not session_obj: return

    session_data = SessionManager()
    input_path = session_data.get_path("mic_input")

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
            session_obj.state_machine.emit_event("error", {"message": f"Falha na conversão de audio: {result.stderr.decode()[:200]}"})
            session_obj.state_machine.reset()
            return

        # Cleanup temp webm
        try:
            if os.path.exists(webm_path):
                os.remove(webm_path)
        except Exception: pass

        stt = get_stt(session_obj.config["stt_model"])
        transcribed_text, stt_time, stt_info = stt.transcribe(input_path)

        if not transcribed_text.strip():
            session_obj.state_machine.emit_event("error", {"message": "Nenhum texto detectado no audio."})
            session_obj.state_machine.reset()
            return

        session_obj.state_machine.emit_event("transcription_complete", {
            "text": transcribed_text,
            "language": getattr(stt_info, "language", "unknown"),
            "stt_time": round(stt_time, 3),
        })

        # Se já houver alguém na fila, avisamos o usuário
        if request_queue.qsize() > 0:
            session_obj.state_machine.transition_to(ConversationState.QUEUED, {"queue_pos": request_queue.qsize()})

        # Adiciona à fila de inferência
        asyncio.run_coroutine_threadsafe(
            request_queue.put((_run_llm_tts_pipeline, (session_data, transcribed_text, stt_time, stt_info), {"client_id": client_id})),
            lifespan._loop
        )

    except Exception as e:
        session_obj.state_machine.emit_event("error", {"message": str(e)})
        print(f"[Pipeline] ERRO: {e}")


# ─── Shared LLM → TTS Pipeline ───────────────────────────────
def _run_llm_tts_pipeline(session_data, user_text: str, stt_time: float, stt_info, **kwargs):
    """Core pipeline compartilhado entre voice e text input."""
    client_id = kwargs.get("client_id")
    session_obj = manager.get_session(client_id)
    if not session_obj: return

    session_obj.state_machine.transition_to(ConversationState.THINKING)

    llm = get_llm(session_obj.config["llm_model"])
    tts = get_tts(session_obj.config["tts_voice"])

    full_response = ""
    ttft = None
    ttfs = None
    chunks_meta = []
    chunk_count = 0
    llm_start = time.time()

    tts_dir = os.path.join(session_data.session_dir, "tts", "chunks")
    os.makedirs(tts_dir, exist_ok=True)

    # Buffer for natural chunking — accumulate raw text, detect sentences
    raw_buffer = ""
    # Regex: match text ending with sentence terminators
    _sentence_end = re.compile(r'[.!?]\s*$')

    print(f"[LLM] Streaming com system prompt otimizado para voz...")
    for token in llm.generate_stream(user_text, system_prompt=SYSTEM_PROMPT):
        if ttft is None:
            ttft = time.time() - llm_start
            session_obj.state_machine.emit_event("metrics_updated", {"ttft": round(ttft, 3)})

        full_response += token
        raw_buffer += token

        # Emit partial text (original, com markdown se houver)
        session_obj.state_machine.emit_event("llm_chunk", {"token": token, "full_text": full_response})

        # Detect sentence boundary in buffer
        if _sentence_end.search(raw_buffer) and len(raw_buffer.strip()) >= MIN_CHUNK_CHARS:
            # Sanitize the completed sentence(s)
            clean_chunk = sanitize_for_tts(raw_buffer).strip()
            raw_buffer = ""

            if clean_chunk and session_obj.config["voice_enabled"]:
                if not session_obj.state_machine.state == ConversationState.SPEAKING:
                    session_obj.state_machine.transition_to(ConversationState.SPEAKING)

                chunk_count += 1
                chunk_path = os.path.join(tts_dir, f"chunk_{chunk_count:03d}.wav")
                tts_start = time.time()
                tts.generate_audio(clean_chunk, chunk_path)
                tts_gen_time = time.time() - tts_start

                if ttfs is None:
                    ttfs = time.time() - llm_start
                    session_obj.state_machine.emit_event("metrics_updated", {"ttfs": round(ttfs, 3)})

                session_obj.state_machine.emit_event("tts_chunk_ready", {
                    "chunk_id": chunk_count, 
                    "text": clean_chunk, 
                    "gen_time": round(tts_gen_time, 3),
                    "audio_url": f"/sessions/{session_data.timestamp}/tts/chunks/chunk_{chunk_count:03d}.wav"
                })
                # REMOVED: tts.play_audio(chunk_path)
                # state_machine.emit_event("playback_finished", {"chunk_id": chunk_count})

                chunks_meta.append({"id": chunk_count, "text": clean_chunk, "path": chunk_path, "gen_time": round(tts_gen_time, 3)})

    # Flush remaining buffer
    remaining = sanitize_for_tts(raw_buffer).strip()
    if remaining and session_obj.config["voice_enabled"]:
        if not session_obj.state_machine.state == ConversationState.SPEAKING:
            session_obj.state_machine.transition_to(ConversationState.SPEAKING)
        chunk_count += 1
        chunk_path = os.path.join(tts_dir, f"chunk_{chunk_count:03d}.wav")
        tts.generate_audio(remaining, chunk_path)
        
        session_obj.state_machine.emit_event("tts_chunk_ready", {
            "chunk_id": chunk_count, 
            "text": remaining, 
            "gen_time": 0,
            "audio_url": f"/sessions/{session_data.timestamp}/tts/chunks/chunk_{chunk_count:03d}.wav"
        })
        # REMOVED: tts.play_audio(chunk_path)
        chunks_meta.append({"id": chunk_count, "text": remaining, "path": chunk_path, "gen_time": 0})

    # Metrics calculation
    total_llm_time = time.time() - llm_start
    queue_pos = kwargs.get("queue_pos", 0) # Track if it was queued

    # Persist

    # If voice was disabled, still transition through states
    if not session_obj.config["voice_enabled"] and session_obj.state_machine.state == ConversationState.THINKING:
        session_obj.state_machine.transition_to(ConversationState.IDLE)

    # Persist
    session_data.save_text("stt_transcription", user_text)
    session_data.save_text("llm_prompt", user_text)
    session_data.save_text("llm_response", full_response)

    lang = getattr(stt_info, "language", "text") if stt_info else "text"
    prob = getattr(stt_info, "language_probability", 0.0) if stt_info else 0.0

    session_data.build_metadata(
        stt_model=session_obj.config["stt_model"],
        llm_model=session_obj.config["llm_model"],
        tts_model=session_obj.config["tts_voice"],
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

    session_obj.state_machine.emit_event("pipeline_complete", {
        "session_id": session_data.timestamp,
        "transcription": user_text,
        "response": full_response,
        "ttft": round(ttft, 3) if ttft else None,
        "ttfs": round(ttfs, 3) if ttfs else None,
        "total_time": round(total_llm_time, 3),
        "chunks_count": chunk_count,
        "model": session_obj.config["llm_model"],
        "voice_enabled": session_obj.config["voice_enabled"],
    })


# ─── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    
    # Configuração TLS (M8)
    cert_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models", "certs", "cert.pem")
    key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models", "certs", "key.pem")
    
    ssl_config = {}
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"\n[VoiceLab] ✅ HTTPS ATIVO: https://192.168.68.110:8000")
        print(f"[VoiceLab] ✅ Acesso LAN: https://192.168.68.110:8000")
        print("[VoiceLab] 💡 IMPORTANTE: No celular, aceite o 'Aviso de Segurança' para habilitar o microfone.\n")
        ssl_config = {
            "ssl_certfile": cert_path,
            "ssl_keyfile": key_path
        }
    else:
        print("[VoiceLab] ⚠️ TLS NÃO detectado. Iniciando em http://0.0.0.0:8000")
        print("[VoiceLab] ⚠️ AVISO: Microfone mobile pode não funcionar sem HTTPS.")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", **ssl_config)
