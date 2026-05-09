import os
import sys

# Adiciona o diretorio principal ao path para importar modulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestrator import VoiceOrchestrator

def test_llm_integration():
    """
    Teste independente para validar a integracao STT -> LLM.
    Garante reporte detalhado para debugging e previsibilidade.
    """
    print("--- Teste Independente: Integracao STT -> LLM (Milestone 3) ---")
    
    # Modelos padrao definidos explicitamente
    stt_model = "base"
    llm_model = "qwen2.5:0.5b"
    
    orchestrator = VoiceOrchestrator(stt_model=stt_model, llm_model=llm_model)
    test_file = "output/test_recording.wav"
    
    if not os.path.exists(test_file):
        print(f"ERRO: Arquivo de teste '{test_file}' nao encontrado.")
        print("Certifique-se de gerar o arquivo via 'tests/test_audio_capture.py'.")
        return

    print(f"\nIniciando pipeline com arquivo: {test_file}")
    
    try:
        # Executa o fluxo sincrono
        transcribed_text, llm_response, stt_time, llm_time = orchestrator.process_audio(test_file)
        
        total_time = stt_time + llm_time
        
        # Debug Logs solicitados pelo Rudy (sem emojis/caracteres complexos para evitar charmap issues no Windows)
        print("\n" + "="*50)
        print(" RELATORIO DE PIPELINE (STT -> LLM)")
        print("="*50)
        print(f" MODELO STT Utilizado : {stt_model}")
        print(f" MODELO LLM Utilizado : {llm_model}")
        print("-" * 50)
        print(f" TEXTO TRANSCRITO     : \"{transcribed_text}\"")
        print(f" PROMPT ENVIADO AO LLM: \"{transcribed_text}\"")  # Nesta fase, o prompt eh exatamente o texto
        print("-" * 50)
        print(f" RESPOSTA DO LLM      :\n{llm_response}")
        print("-" * 50)
        print(f" Tempo STT            : {stt_time:.2f}s")
        print(f" Tempo LLM            : {llm_time:.2f}s")
        print(f" TEMPO TOTAL PIPELINE : {total_time:.2f}s")
        print("="*50 + "\n")
        
        if llm_response:
            print("RESULTADO: SUCESSO. Pipeline completo executado perfeitamente.")
        else:
            print("RESULTADO: FALHA. A resposta do LLM esta vazia.")
            
    except Exception as e:
        print(f"\nRESULTADO: ERRO durante a execucao: {e}")

if __name__ == "__main__":
    test_llm_integration()
