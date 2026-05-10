# Arquitetura Técnica (M9)

Este documento detalha o design interno do laboratório para suportar execuções multi-clientes seguras, assíncronas e state-driven.

## 🏗️ Arquitetura Unidirecional de Estado

O laboratório é fundamentado no padrão onde **o Backend é a única Source of Truth**. O Frontend atua apenas como um "Visualizador" (Thin Client).

### Fluxo de Eventos:
1. O usuário dispara uma ação na interface (grava áudio, digita texto, altera selector).
2. O Frontend (`app.js`) envia o JSON para o Websocket (ação bruta).
3. A `ConversationStateMachine` (isolada por cliente no Backend) valida a transição de estado.
4. Se válida, o Backend notifica o Frontend: `"Mude seu visual para TRANSCRIBING"`.
5. O Frontend apenas obedece aos estados. Não inferimos visualmente.
Isso evita divergência visual, race conditions de UI e estados fantasmas durante streaming e reconexões WebSocket.

## 🧠 Modelos como Singletons vs. Sessões Isoladas

Para não explodir a memória (RAM/VRAM) ao plugar múltiplos celulares ao mesmo tempo:

*   **Motores de Inferência = Singletons Compartilhados:** `get_stt()`, `get_tts()`, `get_llm()` carregam o motor apenas uma vez. Todos os clientes ativos compartilham as instâncias de inferência.
*   **Dados (Sessão) = Isolado:** Cada conexão ganha um objeto `ClientSession` gerido pelo `SessionManager`. Ele contém:
    - Um ID UUID único.
    - Seu próprio diretório `output/sessions/<ID>/`.
    - Sua própria `StateMachine`.
    - Suas preferências ativas de UI (`config` dictionary).

## 🎼 Pipeline de Fila (Inference Worker)

Motores locais de IA são extremamente sensíveis à concorrência na VRAM.
Se dois clientes falarem ao mesmo tempo, paralelizá-los causaria um OOM (Out Of Memory).
Por isso, implementamos uma **Fila de Inferência Assíncrona** (`inference_worker`).
- Apenas um LLM -> TTS ocorre por vez no servidor.
- Os outros ficam no estado `QUEUED`.

## 🔊 Ciclo Híbrido TTS -> Client Playback

Na Milestone 8, migramos a reprodução de áudio. O servidor *nunca* toca sons nas caixas de som locais.
1. O backend gera fragmentos incrementais (Chunks de WAV).
2. O fragmento é salvo em disco (`output/sessions/.../tts/chunks/`).
3. O WebSocket notifica a URL pública do fragmento gerado incluindo o contexto da ClientSession proprietária do chunk.
4. O `app.js` empilha a URL num `AudioQueue` e inicia o download nativo para a caixa de som do celular ou computador do cliente que requisitou.


## 🔄 Fluxo Completo da Conversa

Cliente (Browser/Mobile)
↓
WebSocket Event
↓
ClientSession
↓
StateMachine
↓
Inference Queue
↓
STT / LLM / TTS
↓
Chunk Generator
↓
Static Session Storage
↓
WebSocket Notification
↓
Frontend AudioQueue
↓
Playback Local

## 📐 Princípios Arquiteturais

- Backend é a única source of truth.
- Toda sessão é isolada via ClientSession.
- Inferência pesada nunca roda em paralelo.
- Frontend não mantém estado crítico.
- Playback é sempre client-side.
- Sessões devem ser auditáveis.
- Streaming é incremental e orientado a eventos.