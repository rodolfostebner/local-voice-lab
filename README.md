# 🎙️ Local Voice Assistant Lab

Um laboratório experimental focado na construção de um assistente de voz **100% local, offline e auditável**, executando grandes modelos de linguagem (LLMs) e motores de processamento de fala (STT/TTS) sem depender de APIs em nuvem.

O projeto implementa uma arquitetura multi-cliente isolada, permitindo que diversos dispositivos na rede local (LAN) se conectem e mantenham sessões independentes simultâneas de voz e texto.

---

## 🎯 Características Principais

*   **Local-First & Offline:** Todos os componentes (Ollama, Faster Whisper, Piper TTS) rodam localmente. Nenhuma voz, áudio ou texto é enviado para a nuvem.
*   **Acesso Mobile/LAN:** Compatibilidade de rede local completa via TLS (`mkcert`) e streaming WebSockets, suportando microfones de smartphones e tablets.
*   **Arquitetura ClientSession:** Cada aba do navegador ou celular possui uma máquina de estados (`StateMachine`), fila de áudio e configurações (modelo, voz) **isoladas e independentes**.
*   **Streaming Incremental (Chunking):** Respostas longas do LLM são fragmentadas em sentenças lógicas e sintetizadas/enviadas sob demanda, reduzindo drasticamente o TTFR (Time to First Response).
*   **Telemetria Embutida:** A cada interação, a plataforma armazena o histórico do LLM, tempos de inferência e metadados, facilitando auditorias estruturadas.

---

## 🚀 Como Iniciar

### 1. Requisitos Prévios
*   Python 3.10+
*   [Ollama](https://ollama.com) instalado e em execução (`qwen2.5:0.5b`, `llama3.2:1b`, etc.).
*   [Piper TTS](https://github.com/rhasspy/piper) executáveis (`piper.exe`).
*   [mkcert](https://github.com/FiloSottile/mkcert) (Apenas para acesso via rede local / mobile).

### 2. Certificados TLS (Obrigatório para Mobile)
Para que os navegadores (especialmente iOS/Android) liberem o acesso ao microfone (`getUserMedia`), é necessário servir o backend via HTTPS seguro.
1. Instale o `mkcert`.
2. Gere os certificados na raiz do projeto:
```bash
mkdir -p models/certs
mkcert -install
mkcert -cert-file models/certs/cert.pem -key-file models/certs/key.pem "127.0.0.1" "localhost" "192.168.x.x"
```
> Substitua `192.168.x.x` pelo IP local da sua máquina.

### 3. Rodando o Laboratório
Para iniciar todos os serviços e o servidor ASGI de forma transparente:
```powershell
.\scripts\run_lab.ps1
```

Acesse no celular ou desktop via: `https://[SEU_IP_AQUI]:8000`

---

## 🧹 Manutenção e Telemetria

O sistema armazena todo o tráfego gerado em `output/sessions/`.
Para evitar que os áudios lotem o disco, utilize o script de manutenção oficial.

**Limpar sessões antigas:**
```powershell
.\scripts\cleanup_sessions.ps1 -DryRun  # Simula a limpeza
.\scripts\cleanup_sessions.ps1          # Executa de verdade
```
*Regras do Cleanup:* Áudios maiores que 7 dias são deletados; textos são preservados por 30 dias; sessões com menos de 2h nunca são tocadas.

---

## 🏗️ Estrutura de Documentação
Para entender a fundo como a plataforma foi projetada, consulte:
*   [PRD (Product Requirements Document)](docs/PRD.md) - Escopo original e roadmap de Milestones.
*   [ARCHITECTURE](docs/ARCHITECTURE.md) - Padrões de engenharia e decisões arquiteturais.

---

## 🧠 Modelos Validados

| Perfil | Modelo |
|---|---|
| Fast | qwen2.5:0.5b |
| Standard | llama3.2:1b |
| Premium | gemma3:4b |

---

Microfone
↓
STT (Whisper)
↓
LLM (Ollama)
↓
Chunking
↓
Piper TTS
↓
Streaming WebSocket
↓
Playback no Navegador