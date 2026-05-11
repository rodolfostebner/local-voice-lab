import os
import json
import glob
from typing import Dict, Optional, List

class VoiceManager:
    """
    Registry puramente declarativo para perfis de voz (Voice Profiles).
    Desacopla as personas dos motores físicos TTS.
    """
    def __init__(self, config_dir: str = "config/voices"):
        self.config_dir = config_dir
        self.voices: Dict[str, dict] = {}
        self.load_voices()

    def load_voices(self):
        """Descobre e carrega dinamicamente todos os perfis JSON."""
        self.voices.clear()
        
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            return

        pattern = os.path.join(self.config_dir, "*.json")
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "id" in data:
                        self.voices[data["id"]] = data
            except Exception as e:
                print(f"[VoiceManager] Erro ao carregar {file_path}: {e}")
                
        print(f"[VoiceManager] Carregados {len(self.voices)} perfis de voz.")

    def get_voice(self, voice_id: str) -> Optional[dict]:
        """Retorna o profile declarativo."""
        return self.voices.get(voice_id)

    def list_voices(self) -> List[dict]:
        """Lista otimizada para envio ao frontend."""
        return [
            {
                "id": v["id"],
                "display_name": v.get("display_name", v["id"]),
                "engine": v.get("engine", "piper")
            }
            for v in self.voices.values()
        ]
