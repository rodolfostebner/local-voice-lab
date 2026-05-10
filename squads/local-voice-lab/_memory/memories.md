# Squad Memory: Local Voice Assistant Lab

## Estilo de Escrita

## Design Visual

## Estrutura de Conteúdo

## Proibições Explícitas

## Técnico (específico do squad)

- **Regra de Governança #9:** Toda milestone funcional deve possuir pelo menos um teste executável independente no diretório `/tests`.
- **Limitação de Hardware/Modelos:** Modelos muito pequenos (ex: qwen2.5:0.5b) podem apresentar baixa confiabilidade factual (alucinações básicas, como errar capitais), mas são temporariamente aceitáveis para validação arquitetural e pipeline síncrono.
- **Piper TTS API:** Na versão 1.4.2+, deve-se usar `synthesize_wav` em vez de `synthesize` para garantir que os headers WAV (channels, sample rate) sejam configurados corretamente.
- **Arquitetura de Observabilidade:** A implementação do `SessionManager` desacoplado permite rastreabilidade total e geração de datasets locais para benchmarking futuro sem poluir a lógica do orquestrador.
- **Benchmark de Modelos (M4.5):** O `gemma3:4b` demonstrou inteligência superior e fidelidade instrucional, sendo o novo modelo 'Premium'. Modelos `qwen2.5` (0.5b/1.5b) demonstraram alucinações persistentes em PT-BR e bias para termos de hardware em instruções de listagem.
- **Latência vs Qualidade:** O uso do Gemma 4B em CPU exige obrigatoriamente processamento via streaming (M5) para manter a experiência de voz aceitável (TTFT > 15s em modo síncrono).
- **Roadmap de Usabilidade (M6+):** O foco mudou de 'realtime puro' para 'UX e Frontend Local'. Prioridades incluem Frontend Web responsivo (acesso LAN/Mobile), State Machine explícita para controle conversacional e seleção dinâmica de modelos.
