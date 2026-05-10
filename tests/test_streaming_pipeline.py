import os
from src.audio.recorder import AudioRecorder
from src.orchestrator_streaming import VoiceOrchestratorStreaming
from src.session.session_manager import SessionManager

def test_streaming_pipeline():
    """
    Teste E2E para a Milestone M5 (Streaming Incremental).
    Foco: Reduzir TTFT e TTFS usando Gemma 3 4B.
    """
    print("--- Teste E2E Streaming Incremental (M5) ---")
    
    # Inicializa Gerenciador de Sessao
    session = SessionManager()
    log_lines = [f"--- Sessao Streaming iniciada em {session.timestamp} ---"]
    
    input_file = session.get_path("mic_input")
    duration = 5
    
    # Fase 1: Audio In
    msg = "\n[Fase 1] Capturando audio do microfone..."
    print(msg); log_lines.append(msg)
    
    recorder = AudioRecorder()
    print(f"FALE AGORA (voce tem {duration} segundos)...")
    recorder.start_recording(duration_seconds=duration)
    recorder.save_to_wav(input_file)
    
    if not os.path.exists(input_file):
        print("ERRO: Audio de entrada nao gerado."); return

    # Fase 2: Orquestracao de Streaming
    msg = "\n[Fase 2] Iniciando Orquestrador de Streaming (Gemma 4B)..."
    print(msg); log_lines.append(msg)
    
    stt_model = "base"
    llm_model = "gemma3:4b" # O modelo "lento" que queremos tornar "rapido"
    tts_model = "pt_BR-faber-medium"
    
    orchestrator = VoiceOrchestratorStreaming(stt_model=stt_model, llm_model=llm_model, tts_model=tts_model)
    
    try:
        # Processamento Incremental
        transcribed_text, full_response, stt_time, llm_time, ttft, ttfs, chunks, stt_info = orchestrator.process_audio(
            input_file, session_manager=session
        )
        
        # Persistencia Final
        session.save_text("stt_transcription", transcribed_text)
        session.save_text("llm_prompt", transcribed_text)
        session.save_text("llm_response", full_response)
        
        lang = getattr(stt_info, "language", "unknown")
        prob = getattr(stt_info, "language_probability", 0.0)
        
        metadata = session.build_metadata(
            stt_model=stt_model, 
            llm_model=llm_model, 
            tts_model=tts_model,
            stt_time=stt_time, 
            llm_time=llm_time, 
            tts_time=0, # No streaming, o tempo de TTS e distribuido
            detected_language=lang,
            detected_confidence=prob,
            status="success",
            transcribed_text=transcribed_text,
            llm_response_text=full_response,
            ttft=ttft,
            ttfs=ttfs,
            chunks=chunks
        )
        
        # Relatorio no Terminal
        print("\n" + "="*50)
        print(" RELATORIO E2E STREAMING PIPELINE (M5)")
        print("="*50)
        print(f" SESSAO ID       : {session.timestamp}")
        print(f" MODELO LLM      : {llm_model}")
        print("-" * 50)
        print(f" TTFT (1o Token) : {ttft:.2f}s  <-- ALVO: < 2s")
        print(f" TTFS (1o Audio) : {ttfs:.2f}s  <-- ALVO: < 4s")
        print(f" Tempo STT       : {stt_time:.2f}s")
        print(f" Tempo Total LLM : {llm_time:.2f}s")
        print(f" Chunks Gerados  : {len(chunks)}")
        print("-" * 50)
        print(f" TEXTO FINAL     : \"{full_response[:100]}...\"")
        print("="*50 + "\n")
        
        if ttft < 2.5:
            print("RESULTADO: SUCESSO. Latencia inicial reduzida drasticamente via Streaming.")
        else:
            print("RESULTADO: OK, mas latencia inicial acima do ideal.")
            
    except Exception as e:
        msg = f"\nRESULTADO: ERRO durante a execucao: {e}"
        print(msg); log_lines.append(msg)
    finally:
        session.save_pipeline_log(log_lines)

if __name__ == "__main__":
    test_streaming_pipeline()
