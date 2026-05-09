from src.stt.whisper_engine import WhisperEngine
from src.llm.ollama_client import OllamaClient

class VoiceOrchestrator:
    def __init__(self, stt_model="base", llm_model="qwen2.5:0.5b"):
        """
        Coordenador central do fluxo de voz.
        Mantem-se simples para evitar tornar-se um 'God Object'.
        Nesta milestone, opera de forma 100% sincrona.
        """
        print("Inicializando VoiceOrchestrator...")
        self.stt = WhisperEngine(model_size=stt_model)
        self.llm = OllamaClient(model=llm_model)

    def process_audio(self, audio_file_path):
        """
        Executa o fluxo completo: Audio -> STT -> Texto -> LLM -> Resposta.
        Retorna o texto transcrito, a resposta do LLM e os tempos de processamento.
        """
        print("\n[Orchestrator] Iniciando processamento de audio...")
        
        # 1. STT (Speech-to-Text)
        print("[Orchestrator] Transcrevendo audio (STT)...")
        transcribed_text, stt_time, info = self.stt.transcribe(audio_file_path)
        
        # Se a transcricao for vazia ou falhar, aborta o fluxo de forma segura
        if not transcribed_text:
            print("[Orchestrator] Transcricao vazia. Abortando fluxo LLM.")
            return transcribed_text, "", stt_time, 0.0

        # 2. LLM (Inferencia)
        print("[Orchestrator] Enviando texto para o LLM...")
        llm_response, llm_time = self.llm.generate_response(transcribed_text)
        
        print("[Orchestrator] Fluxo concluido com sucesso.")
        
        return transcribed_text, llm_response, stt_time, llm_time
