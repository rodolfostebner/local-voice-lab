import sounddevice as sd
import numpy as np
import wave
import os

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, device=2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.recording = None

    def start_recording(self, duration_seconds):
        print(f"Gravando por {duration_seconds} segundos...")
        # Captura síncrona
        self.recording = sd.rec(
            int(duration_seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16',
            device=self.device
        )
        sd.wait()
        print("Gravacao finalizada.")

    def save_to_wav(self, filename):
        if self.recording is None:
            print("Erro: Nenhuma gravacao para salvar.")
            return

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(self.recording.tobytes())
            
        print(f"Arquivo salvo em: {filename}")
