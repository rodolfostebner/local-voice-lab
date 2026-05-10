import os
import time
import threading
import queue
import re
from src.stt.whisper_engine import WhisperEngine
from src.llm.ollama_client import OllamaClient
from src.tts.tts_engine import PiperTTSEngine

class VoiceOrchestratorStreaming:
    def __init__(self, stt_model="base", llm_model="gemma3:4b", tts_model="pt_BR-faber-medium"):
        print(f"[Orchestrator-Streaming] Inicializando (LLM: {llm_model})...")
        self.stt = WhisperEngine(model_size=stt_model)
        self.llm = OllamaClient(model=llm_model)
        self.tts = PiperTTSEngine(model_name=tts_model)
        
        # Fila para reproducao ordenada
        self.playback_queue = queue.Queue()
        self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()
        
        # Regex para detectar limites de sentenca
        self.sentence_regex = re.compile(r'[^.!?\n]+[.!?\n]+')

    def _playback_worker(self):
        """Thread dedicada a reproduzir audio da fila de forma sequencial."""
        while True:
            audio_path = self.playback_queue.get()
            if audio_path is None: break # Sentinel para encerrar
            
            print(f"[Playback] Reproduzindo chunk: {os.path.basename(audio_path)}")
            self.tts.play_audio(audio_path)
            self.playback_queue.task_done()

    def process_audio(self, input_audio_path, session_manager=None):
        """
        Fluxo Incremental: Mic -> STT -> LLM Stream -> Buffer -> TTS Chunk -> Playback Queue.
        """
        print("\n[Orchestrator] Iniciando processamento incremental...")
        
        # 1. STT (Sincrono, pois audio de entrada ja foi gravado)
        transcribed_text, stt_time, stt_info = self.stt.transcribe(input_audio_path)
        if not transcribed_text.strip():
            return "", "", stt_time, 0, 0, stt_info, []

        print(f"[STT] Texto: \"{transcribed_text}\"")
        
        # 2. LLM Streaming + Buffer + TTS
        full_response = ""
        current_buffer = ""
        chunks_metadata = []
        
        ttft = None # Time to First Token
        ttfs = None # Time to First Sound (TTS synthesis start for first chunk)
        
        start_llm_time = time.time()
        
        # Pasta temporaria para chunks de audio da sessao
        if session_manager:
            tts_dir = os.path.join(session_manager.session_dir, "tts", "chunks")
        else:
            tts_dir = "output/temp/"
        
        os.makedirs(tts_dir, exist_ok=True)

        chunk_count = 0
        
        print("[LLM] Iniciando stream...")
        for token in self.llm.generate_stream(transcribed_text):
            if ttft is None:
                ttft = time.time() - start_llm_time
                print(f"[Métrica] TTFT: {ttft:.2f}s")
            
            full_response += token
            current_buffer += token
            
            # Tenta encontrar uma sentenca completa no buffer
            match = self.sentence_regex.search(current_buffer)
            if match:
                sentence = match.group().strip()
                current_buffer = current_buffer[match.end():]
                
                if sentence:
                    chunk_count += 1
                    chunk_path = os.path.join(tts_dir, f"chunk_{chunk_count:03d}.wav")
                    
                    # 3. TTS Synthesis do Chunk (Pode ser feito em thread se quisermos mais agressividade)
                    # Por enquanto, fazemos sequencial para garantir estabilidade do worker de TTS
                    print(f"[TTS] Sintetizando chunk {chunk_count}: \"{sentence[:30]}...\"")
                    
                    chunk_start_time = time.time()
                    self.tts.generate_audio(sentence, chunk_path)
                    chunk_gen_duration = time.time() - chunk_start_time
                    
                    if ttfs is None:
                        ttfs = (time.time() - start_llm_time)
                        print(f"[Métrica] TTFS (Inicio Audio): {ttfs:.2f}s")
                    
                    # 4. Envia para Fila de Playback
                    self.playback_queue.put(chunk_path)
                    
                    chunks_metadata.append({
                        "id": chunk_count,
                        "text": sentence,
                        "path": chunk_path,
                        "gen_time": round(chunk_gen_duration, 3)
                    })

        # Processa o que sobrou no buffer no final do stream
        if current_buffer.strip():
            chunk_count += 1
            chunk_path = os.path.join(tts_dir, f"chunk_{chunk_count:03d}.wav")
            self.tts.generate_audio(current_buffer.strip(), chunk_path)
            self.playback_queue.put(chunk_path)
            chunks_metadata.append({
                "id": chunk_count,
                "text": current_buffer.strip(),
                "path": chunk_path,
                "gen_time": 0
            })

        total_llm_time = time.time() - start_llm_time
        
        # Espera o playback terminar
        self.playback_queue.join()
        
        return transcribed_text, full_response, stt_time, total_llm_time, ttft, ttfs, chunks_metadata, stt_info
