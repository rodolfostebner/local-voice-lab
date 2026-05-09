import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tts.tts_engine import PiperTTSEngine

def test_tts_isolated():
    """
    Teste isolado da camada TTS.
    Valida: geracao do WAV, header, tamanho e reproducao.
    """
    print("--- Teste Isolado: TTS (Piper) ---")
    
    output_file = "output/tts_test_output.wav"
    test_text = "Ola, eu sou o assistente de voz local. Este e um teste de sintese."
    
    print(f"\nTexto de entrada: \"{test_text}\"")
    print(f"Arquivo de saida: {output_file}\n")
    
    try:
        engine = PiperTTSEngine()
        
        # Fase 1: Geracao
        print("[Fase 1] Gerando WAV...")
        tts_time = engine.generate_audio(test_text, output_file)
        
        # Fase 2: Verificacao do arquivo
        print("\n[Fase 2] Verificando arquivo gerado...")
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"ARQUIVO EXISTE: SIM ({file_size} bytes)")
        else:
            print("ARQUIVO EXISTE: NAO")
            print("RESULTADO: FALHA")
            return
        
        # Fase 3: Reproducao
        print("\n[Fase 3] Reproduzindo audio...")
        engine.play_audio(output_file)
        
        print("\n" + "="*50)
        print(" RELATORIO TESTE TTS ISOLADO")
        print("="*50)
        print(f" Modelo TTS   : {engine.model_name}")
        print(f" Texto         : \"{test_text}\"")
        print(f" Arquivo WAV   : {output_file}")
        print(f" Tamanho WAV   : {file_size} bytes")
        print(f" Tempo Geracao : {tts_time:.2f}s")
        print("="*50 + "\n")
        
        print("RESULTADO: SUCESSO. WAV gerado e reproduzido com sucesso.")
        
    except Exception as e:
        print(f"\nRESULTADO: ERRO durante a execucao: {e}")

if __name__ == "__main__":
    test_tts_isolated()
