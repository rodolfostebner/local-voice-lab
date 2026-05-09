import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.audio.recorder import AudioRecorder
from src.orchestrator import VoiceOrchestrator
from src.session.session_manager import SessionManager

def test_full_pipeline():
    """
    Teste Ponta a Ponta definitivo para a Milestone M4 (TTS).
    Captura audio do microfone -> STT -> LLM -> TTS -> Reproduz audio.
    Agora com persistencia estruturada em sessoes.
    """
    print("--- Teste E2E Full Pipeline com Observabilidade ---")
    
    # Inicializa Gerenciador de Sessao
    session = SessionManager()
    log_lines = [f"--- Sessao iniciada em {session.timestamp} ---"]
    
    input_file = session.get_path("mic_input")
    output_file = session.get_path("tts_response")
    duration = 5
    
    # Fase 1: Audio In
    msg = "\n[Fase 1] Inicializando microfone..."
    print(msg); log_lines.append(msg)
    
    recorder = AudioRecorder()
    
    msg = f"\nFALE AGORA (voce tem {duration} segundos)..."
    print(msg); log_lines.append(msg)
    
    recorder.start_recording(duration_seconds=duration)
    recorder.save_to_wav(input_file)
    
    if not os.path.exists(input_file):
        msg = f"ERRO: Arquivo de entrada {input_file} nao gerado."
        print(msg); log_lines.append(msg)
        session.save_pipeline_log(log_lines)
        return

    # Fase 2: Orquestracao
    msg = "\n[Fase 2] Iniciando Orquestrador Local..."
    print(msg); log_lines.append(msg)
    
    stt_model = "base"
    llm_model = "qwen2.5:0.5b"
    tts_model = "pt_BR-faber-medium"
    
    orchestrator = VoiceOrchestrator(stt_model=stt_model, llm_model=llm_model, tts_model=tts_model)
    
    try:
        # Nota: Agora o orchestrator retorna o objeto 'info' do Whisper
        transcribed_text, llm_response, stt_time, llm_time, tts_time, stt_info = orchestrator.process_audio(
            input_file, output_audio_path=output_file
        )
        
        # Persistencia de Textos
        session.save_text("stt_transcription", transcribed_text)
        session.save_text("llm_prompt", transcribed_text) # Prompt simplificado para o MVP
        session.save_text("llm_response", llm_response)
        
        # Geracao de Metadata
        lang = getattr(stt_info, "language", "unknown")
        prob = getattr(stt_info, "language_probability", 0.0)
        
        metadata = session.build_metadata(
            stt_model=stt_model, 
            llm_model=llm_model, 
            tts_model=tts_model,
            stt_time=stt_time, 
            llm_time=llm_time, 
            tts_time=tts_time,
            detected_language=lang,
            detected_confidence=prob,
            status="success" if transcribed_text else "empty_transcription",
            transcribed_text=transcribed_text,
            llm_response_text=llm_response
        )
        
        total_time = metadata["timings"]["total_seconds"]
        wav_gerado = os.path.exists(output_file)
        
        # Relatorio no Terminal
        print("\n" + "="*50)
        print(" RELATORIO E2E FULL PIPELINE (SESSAO ESTRUTURADA)")
        print("="*50)
        print(f" SESSAO ID       : {session.timestamp}")
        print(f" LOCAL DA SESSAO : {session.session_dir}")
        print("-" * 50)
        print(f" TEXTO TRANSCRITO : \"{transcribed_text}\" ({lang} {prob*100:.1f}%)")
        print(f" RESPOSTA DO LLM  :\n{llm_response}")
        print("-" * 50)
        print(f" Tempo STT : {stt_time:.2f}s")
        print(f" Tempo LLM : {llm_time:.2f}s")
        print(f" Tempo TTS : {tts_time:.2f}s")
        print(f" TOTAL     : {total_time:.2f}s")
        print("="*50 + "\n")
        
        log_lines.append(f"STT: {transcribed_text}")
        log_lines.append(f"LLM: {llm_response}")
        log_lines.append(f"Total Time: {total_time}s")
        
        if llm_response and wav_gerado:
            print("RESULTADO: SUCESSO. Pipeline fechou o laco completo e persistiu os dados.")
        else:
            print("RESULTADO: FALHA ou Transcricao Vazia.")
            
    except Exception as e:
        msg = f"\nRESULTADO: ERRO durante a execucao: {e}"
        print(msg); log_lines.append(msg)
    finally:
        session.save_pipeline_log(log_lines)

if __name__ == "__main__":
    test_full_pipeline()
