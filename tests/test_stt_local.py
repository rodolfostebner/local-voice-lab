import os
import sys

# Adiciona o diretorio 'src' ao path para permitir a importacao dos modulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.stt.whisper_engine import WhisperEngine

def test_stt_functionality():
    """
    Teste independente para validar a funcionalidade de STT local.
    """
    print("--- Teste Independente: Transcricao STT Local ---")
    
    engine = WhisperEngine(model_size="base")
    test_file = "output/test_recording.wav"
    
    if not os.path.exists(test_file):
        print(f"ERRO: Arquivo de teste '{test_file}' nao encontrado.")
        print("Por favor, execute 'python tests/test_audio_capture.py' primeiro.")
        return

    print(f"Validando arquivo: {test_file}")
    try:
        text, processing_time, info = engine.transcribe(test_file)
        
        if text:
            print("\nRESULTADO: SUCESSO")
            print(f"Texto detectado: {text}")
            print(f"Idioma: {info.language}")
        else:
            print("\nRESULTADO: FALHA (Texto vazio)")
            
    except Exception as e:
        print(f"\nRESULTADO: ERRO durante a execucao: {e}")

if __name__ == "__main__":
    test_stt_functionality()
