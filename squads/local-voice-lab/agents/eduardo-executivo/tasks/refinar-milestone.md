---
task: "Refinar Milestone"
order: 1
input: |
  - objetivo_usuario: O que o usuário quer alcançar (texto livre).
  - contexto_atual: Estado do repositório ou discussões anteriores.
output: |
  - milestone_id: Identificador único da milestone.
  - objetivo_refinado: Descrição técnica precisa do que será feito.
  - restricoes: O que NÃO será feito neste ciclo.
  - criterio_aceite: Como saberemos que terminou.
---

# Refinar Milestone

Transforma um desejo vago do usuário em uma unidade de trabalho técnica, linear e incremental.

## Process

1. Analisar a solicitação do usuário contra a filosofia do MVP local.
2. Identificar o "caminho crítico" — a menor mudança necessária para atingir o objetivo.
3. Listar explicitamente o que está fora do escopo para evitar complexidade prematura.
4. Definir um teste prático que o usuário possa realizar para validar o resultado.

## Output Format

```yaml
milestone:
  id: "M1-..."
  objetivo: "..."
  nao_objetivo: ["...", "..."]
  criterio_aceite: "O comando X deve retornar Y"
  agente_designado: "mateus-modelos | vitor-voz"
```

## Output Example

> Use as quality reference, not as rigid template.

```yaml
milestone:
  id: "M2-Piper-Basic"
  objetivo: "Implementar saída de voz básica usando Piper TTS local via linha de comando."
  nao_objetivo: 
    - "Streaming de áudio (será feito em milestone futura)"
    - "Múltiplas vozes (usar apenas Lessac-Medium)"
  criterio_aceite: "Ao rodar o script `tests/test_tts.py`, o computador deve falar 'Olá, mundo' usando o Piper local."
  agente_designado: "vitor-voz"
```

## Quality Criteria

- [ ] O objetivo é linear e único?
- [ ] O critério de aceite é testável localmente?
- [ ] A restrição de escopo é clara?

## Veto Conditions

Reject and redo if ANY are true:
1. O objetivo sugere mais de um caminho técnico simultâneo.
2. O escopo inclui integrações externas ou cloud.
