import time
from ollama import Client

class OllamaClient:
    def __init__(self, model="qwen2.5:0.5b", host="http://localhost:11434", timeout=60.0):
        """
        Inicializa o cliente Ollama com configuracao explicita conforme
        requisitado no Technical Design da Milestone M3.
        """
        self.model = model
        self.host = host
        self.timeout = timeout
        print(f"Inicializando OllamaClient (Model: {self.model}, Host: {self.host}, Timeout: {self.timeout}s)...")
        # Instancia o cliente passando explicitamente o host
        self.client = Client(host=self.host)

    def generate_response(self, prompt, system_prompt="Você é um assistente prestativo e conciso. Responda diretamente e sem formatação excessiva."):
        """
        Gera uma resposta de forma estritamente sincrona.
        """
        start_time = time.time()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Realiza a chamada sincrona para o Ollama
        response = self.client.chat(model=self.model, messages=messages)
        
        end_time = time.time()
        inference_time = end_time - start_time
        
        response_text = response['message']['content'].strip()
        
        # O debug completo do fluxo sera feito no teste independente,
        # mas mantemos metricas basicas aqui se necessario.
        
        return response_text, inference_time

    def generate_stream(self, prompt, system_prompt="Você é um assistente prestativo e conciso. Responda diretamente e sem formatação excessiva."):
        """
        Gera uma resposta via streaming (Generator).
        Retorna um iterador de tokens.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Realiza a chamada streaming para o Ollama
        for chunk in self.client.chat(model=self.model, messages=messages, stream=True):
            yield chunk['message']['content']

