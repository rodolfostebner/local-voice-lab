import os
import time
from faster_whisper import WhisperModel

class WhisperEngine:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Inicializa o motor Faster Whisper.
        Prioriza estabilidade e execucao local.
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        # Log inicial do modelo
        print(f"Carregando modelo Whisper: {model_size} ({device}/{compute_type})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, file_path):
        """
        Transcreve um arquivo de audio (.wav) e retorna o texto.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")

        start_time = time.time()
        
        # O Faster Whisper retorna um gerador de segmentos
        # beam_size=5 para maior precisao
        segments, info = self.model.transcribe(file_path, beam_size=5)
        
        # Converte segmentos em uma string única
        text = " ".join([segment.text for segment in segments]).strip()
        
        end_time = time.time()
        processing_time = end_time - start_time

        # Debug Logs solicitados pelo Rudy
        print("\n" + "="*40)
        print(" RELATORIO DE TRANSCRICAO (STT)")
        print("="*40)
        print(f" - Modelo Utilizado:  {self.model_size}")
        print(f" - Idioma Detectado:  {info.language} ({info.language_probability*100:.1f}%)")
        print(f" - Tempo de Proc.:    {processing_time:.2f} segundos")
        print(f" - Texto Transcrito:  \"{text}\"")
        print("="*40 + "\n")

        return text, processing_time, info

if __name__ == "__main__":
    # Teste explicito solicitado pelo Rudy usando o arquivo gravado anteriormente
    print("--- Teste de Integracao STT Local ---")
    engine = WhisperEngine(model_size="base")
    test_file = "output/test_recording.wav"
    
    if os.path.exists(test_file):
        print(f"Processando arquivo: {test_file}")
        try:
            engine.transcribe(test_file)
            print("Sucesso: Transcricao concluida.")
        except Exception as e:
            print(f"Erro durante a transcricao: {e}")
    else:
        print(f"Aviso: Arquivo '{test_file}' nao encontrado.")
        print("Certifique-se de rodar o teste de captura (tests/test_audio_capture.py) primeiro.")
