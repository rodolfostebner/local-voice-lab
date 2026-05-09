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
