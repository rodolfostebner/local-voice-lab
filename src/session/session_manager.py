import os
import json
from datetime import datetime

class SessionManager:
    """
    Gerencia sessoes estruturadas de execucao do pipeline.
    Cada sessao possui uma estrutura fixa de diretorios para
    persistencia, auditoria e rastreabilidade.
    
    Desacoplado da logica de orquestracao para manter
    o principio de responsabilidade unica.
    """
    
    def __init__(self, base_dir="output/sessions"):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.abspath(os.path.join(base_dir, self.timestamp))
        self._paths = {}
        self._create_structure()

    def _create_structure(self):
        """Cria a arvore de diretorios da sessao."""
        subdirs = [
            "input",
            "llm",
            "tts",
            "logs",
        ]
        for subdir in subdirs:
            os.makedirs(os.path.join(self.session_dir, subdir), exist_ok=True)
        
        # Define os paths fixos da sessao
        self._paths = {
            "mic_input":          os.path.join(self.session_dir, "input", "mic_input.wav"),
            "stt_transcription":  os.path.join(self.session_dir, "input", "stt_transcription.txt"),
            "llm_prompt":         os.path.join(self.session_dir, "llm", "prompt.txt"),
            "llm_response":       os.path.join(self.session_dir, "llm", "response.txt"),
            "llm_metadata":       os.path.join(self.session_dir, "llm", "metadata.json"),
            "tts_response":       os.path.join(self.session_dir, "tts", "response.wav"),
            "pipeline_log":       os.path.join(self.session_dir, "logs", "pipeline.log"),
        }
        
        print(f"[Session] Sessao criada: {self.session_dir}")

    def get_path(self, key):
        """Retorna o path absoluto para um recurso da sessao."""
        return self._paths.get(key)

    def save_text(self, key, content):
        """Salva conteudo textual em um arquivo da sessao."""
        path = self.get_path(key)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    def save_metadata(self, metadata_dict):
        """Salva o metadata.json completo da sessao."""
        path = os.path.join(self.session_dir, "llm", "metadata.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

    def save_pipeline_log(self, log_lines):
        """Salva o log completo do pipeline."""
        path = self.get_path("pipeline_log")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))

    def build_metadata(self, stt_model, llm_model, tts_model,
                       stt_time, llm_time, tts_time,
                       detected_language, detected_confidence,
                       status, transcribed_text, llm_response_text):
        """Constroi e salva o metadata.json padronizado."""
        total_time = stt_time + llm_time + tts_time
        metadata = {
            "session_id": self.timestamp,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "models": {
                "stt": stt_model,
                "llm": llm_model,
                "tts": tts_model,
            },
            "timings": {
                "stt_seconds": round(stt_time, 3),
                "llm_seconds": round(llm_time, 3),
                "tts_seconds": round(tts_time, 3),
                "total_seconds": round(total_time, 3),
            },
            "detection": {
                "language": detected_language,
                "confidence": detected_confidence,
            },
            "content": {
                "transcription": transcribed_text,
                "llm_response": llm_response_text,
            },
            "paths": {
                "mic_input": self.get_path("mic_input"),
                "stt_transcription": self.get_path("stt_transcription"),
                "llm_prompt": self.get_path("llm_prompt"),
                "llm_response": self.get_path("llm_response"),
                "tts_response": self.get_path("tts_response"),
                "pipeline_log": self.get_path("pipeline_log"),
            },
        }
        self.save_metadata(metadata)
        return metadata
