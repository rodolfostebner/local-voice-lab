import os
import sys

# Adiciona o diretorio principal ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.audio.recorder import AudioRecorder
from src.orchestrator import VoiceOrchestrator

def test_e2e_pipeline():
    """
    Teste Ponta a Ponta (End-to-End) real para a Milestone 3.
    Captura audio do microfone -> STT -> LLM -> Resposta.
    """
    print("--- Teste E2E Real: Captura -> STT -> LLM ---")
    
    output_file = "output/e2e_test_recording.wav"
    duration = 5 # segundos
    
    # 1. Captura de Audio
    print("\n[Fase 1] Inicializando microfone...")
    recorder = AudioRecorder()
    
    print("\nFALE AGORA (voce tem 5 segundos)...")
    recorder.start_recording(duration_seconds=duration)
    recorder.save_to_wav(output_file)
    
    if not os.path.exists(output_file):
        print(f"ERRO: O arquivo {output_file} nao foi gerado.")
        return

    # 2. Orquestracao (STT -> LLM)
    print("\n[Fase 2] Iniciando Orquestrador Local...")
    stt_model = "base"
    llm_model = "qwen2.5:0.5b"
    orchestrator = VoiceOrchestrator(stt_model=stt_model, llm_model=llm_model)
    
    try:
        transcribed_text, llm_response, stt_time, llm_time = orchestrator.process_audio(output_file)
        total_time = stt_time + llm_time
        
        print("\n" + "="*50)
        print(" RELATORIO E2E PIPELINE (MIC -> STT -> LLM)")
        print("="*50)
        print(f" MODELO STT Utilizado : {stt_model}")
        print(f" MODELO LLM Utilizado : {llm_model}")
        print("-" * 50)
        print(f" TEXTO TRANSCRITO     : \"{transcribed_text}\"")
        print(f" PROMPT ENVIADO AO LLM: \"{transcribed_text}\"")
        print("-" * 50)
        print(f" RESPOSTA DO LLM      :\n{llm_response}")
        print("-" * 50)
        print(f" Tempo STT            : {stt_time:.2f}s")
        print(f" Tempo LLM            : {llm_time:.2f}s")
        print(f" TEMPO TOTAL PIPELINE : {total_time:.2f}s")
        print("="*50 + "\n")
        
        if llm_response:
            print("RESULTADO: SUCESSO. Teste Ponta a Ponta executado perfeitamente.")
        else:
            print("RESULTADO: FALHA. A resposta do LLM esta vazia.")
            
    except Exception as e:
        print(f"\nRESULTADO: ERRO durante a execucao: {e}")

if __name__ == "__main__":
    test_e2e_pipeline()
