import sys
import os

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.audio.recorder import AudioRecorder

def test_mic_capture():
    print("--- Teste de Captura de Audio ---")
    recorder = AudioRecorder()
    
    output_file = "output/test_recording.wav"
    
    try:
        recorder.start_recording(duration_seconds=5)
        recorder.save_to_wav(output_file)
        
        if os.path.exists(output_file):
            print(f"Sucesso: O arquivo '{output_file}' foi gerado.")
        else:
            print(f"Erro: O arquivo '{output_file}' nao foi encontrado.")
            
    except Exception as e:
        print(f"Ocorreu um erro durante o teste: {e}")

if __name__ == "__main__":
    test_mic_capture()
