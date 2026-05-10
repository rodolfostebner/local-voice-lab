# Product Requirements Document (PRD)

## 🎯 Objetivo Principal

Construir um laboratório local-first para pesquisa e validação de experiências conversacionais multimodais, priorizando:
- baixa latência percebida
- isolamento multi-cliente
- auditabilidade
- independência de nuvem
- modularidade arquitetural

## 📌 Visão do Produto
O **Local Voice Assistant Lab** é uma plataforma experimental projetada para iterar rapidamente sobre a integração de modelos de linguagem e tecnologias de fala open-source (LLMs, STT, TTS) sem depender de nuvem (Cloud-free).

O diferencial central do laboratório é combinar inferência local, streaming incremental e isolamento multi-cliente em uma arquitetura auditável e extensível.

## 👥 Personas
1. **O Desenvolvedor:** Que precisa plugar ou alterar componentes (novo motor de TTS ou LLM) com atrito zero.
2. **O Operador de UX:** Que utiliza o sistema na rede LAN pelo celular para validar latência e experiência de UX.

## 🛣️ Roadmap Histórico (Milestones Concluídas)

A construção ocorreu em formato incremental, orquestrada por uma *Agile Squad* multi-agente:

*   **M1 - Captura de Áudio Local:** Setup inicial do hardware e captura crua.
*   **M2 - Pipeline STT Local:** Integração do Faster Whisper para transcrever áudio em texto.
*   **M3 - Core LLM Integration:** Acoplamento com Ollama, configurando prompts e extraindo inferências textuais.
*   **M4 - Síntese Local TTS:** Acoplamento com Piper TTS para devolver vozes sintéticas (Edresson, Faber).
*   **M5 - Orquestração Assíncrona:** Adoção de WebSockets e paralelização do processamento.
*   **M6 - Chunking & Streaming TTS:** Quebra orgânica de respostas do LLM (sentences) para início imediato do áudio, derrubando o tempo de espera.
*   **M7 - Governança Conversacional:** Criação da Máquina de Estados (IDLE -> LISTENING -> TRANSCRIBING -> THINKING -> SPEAKING).
*   **M8 - Mobile/LAN Readiness:** Grande Refactor. Isolamento arquitetural via `ClientSession`, HTTPS local via `mkcert`, playback `client-side` pelo navegador. (M8 marcou a transição de protótipo single-client para plataforma distribuída multi-dispositivo.)
*   **M9 - Consolidação Operacional (Atual):** Scripts de limpeza, políticas de retenção e fundação de documentação.

## 📋 Requisitos Não-Funcionais Preservados
- **Local-First:** Sem internet, o sistema tem que continuar conversando.
- **VRAM Control:** Os modelos de IA devem atuar como singletons e nunca se duplicarem entre os clientes.
- **Multi-Client Isolation:** Um cliente pedindo o Qwen não pode alterar o cliente usando Gemma em outro dispositivo.
- Backend as Source of Truth
- Playback exclusivamente client-side
- Streaming orientado a eventos
- Compatibilidade LAN-first

## ✅ Escopo Atual

O laboratório atualmente suporta:
- entrada por voz e texto
- STT local
- LLM local via Ollama
- TTS local via Piper
- streaming incremental
- acesso LAN/mobile
- isolamento por ClientSession
- playback client-side
- auditoria de sessões

## 🚫 Fora de Escopo (Atual)

As seguintes capacidades ainda não fazem parte da plataforma:
- memória persistente conversacional
- VAD contínuo
- full duplex
- interrupção de fala
- agentes autônomos
- sincronização cloud
- execução distribuída