import os
import requests
import wave
import time
import soundfile as sf
import sounddevice as sd
from piper.voice import PiperVoice

class PiperTTSEngine:
    def __init__(self, model_name="pt_BR-faber-medium", model_dir="models/tts/piper"):
        self.model_name = model_name
        self.model_dir = os.path.abspath(model_dir)
        self.model_path = os.path.join(self.model_dir, f"{model_name}.onnx")
        self.config_path = os.path.join(self.model_dir, f"{model_name}.onnx.json")
        
        self._ensure_model_exists()
        
        print(f"[TTSEngine] Carregando modelo Piper TTS: {self.model_name}...")
        self.voice = PiperVoice.load(self.model_path, config_path=self.config_path)

    def _ensure_model_exists(self):
        """Verifica se o modelo existe localmente e faz o download se necessario."""
        if os.path.exists(self.model_path) and os.path.exists(self.config_path):
            return

        print(f"[TTSEngine] Modelo '{self.model_name}' nao encontrado localmente.")
        print("[TTSEngine] Iniciando download automatico. Isso pode demorar alguns minutos...")
        
        os.makedirs(self.model_dir, exist_ok=True)
        
        base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium/{self.model_name}"
        
        try:
            self._download_file(f"{base_url}.onnx", self.model_path)
            self._download_file(f"{base_url}.onnx.json", self.config_path)
            print("[TTSEngine] Download concluido com sucesso.")
        except Exception as e:
            # Em caso de falha, remove arquivos parciais para nao corromper
            if os.path.exists(self.model_path): os.remove(self.model_path)
            if os.path.exists(self.config_path): os.remove(self.config_path)
            raise RuntimeError(f"Falha ao baixar modelo TTS: {e}. Verifique sua conexao e tente novamente.")

    def _download_file(self, url, dest_path):
        """Metodo auxiliar para download de arquivos."""
        print(f"Baixando {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def generate_audio(self, text, output_path):
        """Gera o arquivo de audio WAV a partir do texto."""
        start_time = time.time()
        
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        print(f"[TTSEngine] Gerando audio para: \"{text[:60]}...\"" if len(text) > 60 else f"[TTSEngine] Gerando audio para: \"{text}\"")
        
        with wave.open(output_path, 'wb') as wf:
            # synthesize_wav() configura automaticamente os headers WAV
            # (channels, sample_rate, sample_width) a partir do modelo
            self.voice.synthesize_wav(text, wf)
            
        elapsed_time = time.time() - start_time
        
        # Validacao pos-geracao
        self._validate_wav(output_path)
        
        print(f"[TTSEngine] Audio gerado em {elapsed_time:.2f}s -> {output_path}")
        return elapsed_time
    
    def _validate_wav(self, wav_path):
        """Valida se o WAV gerado possui um header valido e tamanho razoavel."""
        file_size = os.path.getsize(wav_path)
        print(f"[TTSEngine] Validando WAV: {wav_path} ({file_size} bytes)")
        
        if file_size < 100:
            raise RuntimeError(f"WAV corrompido: tamanho muito pequeno ({file_size} bytes)")
        
        with wave.open(wav_path, 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            nframes = wf.getnframes()
            print(f"[TTSEngine] WAV Header: channels={channels}, sample_width={sample_width}, framerate={framerate}, frames={nframes}")
            
            if channels == 0 or framerate == 0 or nframes == 0:
                raise RuntimeError(f"WAV invalido: channels={channels}, framerate={framerate}, frames={nframes}")

    def play_audio(self, wav_path):
        """Reproduz o arquivo de audio gerado usando sounddevice."""
        if not os.path.exists(wav_path):
            print(f"[TTSEngine] ERRO: Arquivo {wav_path} nao encontrado para reproducao.")
            return

        # Carrega o arquivo usando soundfile
        data, fs = sf.read(wav_path)
        
        # Toca usando sounddevice
        sd.play(data, fs)
        sd.wait() # Bloqueia ate terminar de tocar
