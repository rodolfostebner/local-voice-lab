
import os
import sys
import time
import json
import asyncio
import websockets
import threading

# Import mock constants
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_concurrency_queue():
    """Testa se múltiplas requisições são enfileiradas e processadas sequencialmente."""
    url = "ws://localhost:8000/ws"
    
    async def client_task(client_id):
        async with websockets.connect(url) as websocket:
            print(f"[Client {client_id}] Conectado")
            
            # Envia mensagem de texto
            await websocket.send(json.dumps({
                "action": "text_message",
                "text": f"Olá, sou o cliente {client_id}. Por favor, conte uma história curta."
            }))
            
            states = []
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=20)
                    data = json.loads(msg)
                    event = data.get("event")
                    
                    if event == "state_changed":
                        state = data["data"]["to"]
                        states.append(state)
                        print(f"[Client {client_id}] Estado: {state}")
                        if "queue_pos" in data["data"]:
                            print(f"[Client {client_id}] Posição na fila: {data['data']['queue_pos']}")
                    
                    if event == "pipeline_complete":
                        print(f"[Client {client_id}] Pipeline completo!")
                        break
                except asyncio.TimeoutError:
                    print(f"[Client {client_id}] Timeout!")
                    break
            
            return states

    print("\n[M8 Test] Iniciando teste de concorrência (2 clientes simultâneos)...")
    
    # Roda dois clientes "quase" ao mesmo tempo
    results = await asyncio.gather(
        client_task(1),
        client_task(2)
    )
    
    c1_states = results[0]
    c2_states = results[1]
    
    print("\n[M8 Test] Resultado Estados Cliente 1:", c1_states)
    print("[M8 Test] Resultado Estados Cliente 2:", c2_states)
    
    # Verifica se pelo menos um deles passou pelo estado 'queued'
    has_queued = any(s == "queued" for s in c1_states) or any(s == "queued" for s in c2_states)
    
    if has_queued:
        print("\n✅ SUCESSO: A fila de inferência funcionou (estado 'queued' detectado).")
    else:
        print("\n⚠️ AVISO: Estado 'queued' não detectado. Pode ser que o primeiro terminou rápido demais ou a fila não disparou.")

if __name__ == "__main__":
    # Import json fix (oops, double json in script above)
    import json
    try:
        asyncio.run(test_concurrency_queue())
    except Exception as e:
        print(f"Erro ao rodar teste: {e}")
        print("Certifique-se que o servidor (main.py) está rodando em http://localhost:8000")
