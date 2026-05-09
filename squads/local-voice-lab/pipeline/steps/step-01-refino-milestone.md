---
execution: inline
agent: eduardo-executivo
outputFile: squads/local-voice-lab/output/milestone-definition.yaml
---

# Step 01: Refino de Milestone

## Context Loading

Load these files before executing:
- `_opensquad/_memory/company.md` — Perfil da Rudy AI Labs.
- `pipeline/data/domain-framework.md` — Metodologia de desenvolvimento.

## Instructions

### Process
1. Receber o objetivo atual do usuário para o assistente.
2. Analisar se o objetivo é incremental e focado no MVP local.
3. Definir o que será feito e o que será deixado para depois.
4. Identificar qual especialista (Mateus ou Vitor) será o executor primário deste ciclo.
5. Produzir o documento de definição da milestone.

## Output Format

O output deve seguir a estrutura YAML abaixo:
```yaml
milestone:
  id: "M[N]-[Nome]"
  objetivo: "..."
  nao_objetivo: ["...", "..."]
  criterio_aceite: "..."
  executor: "mateus-modelos | vitor-voz"
```

## Output Example

```yaml
milestone:
  id: "M1-Core-STT"
  objetivo: "Implementar captura básica de áudio e transcrição via Faster Whisper local."
  nao_objetivo: 
    - "Integração com LLM (será na M2)"
    - "Interface gráfica"
  criterio_aceite: "Ao falar no microfone, o texto transcrito deve aparecer no terminal em menos de 1.5s."
  executor: "vitor-voz"
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. O objetivo envolve serviços de nuvem.
2. A milestone é muito grande (ex: "Construir o assistente inteiro").

## Quality Criteria

- [ ] Foco total em execução local.
- [ ] Critério de aceite claro e testável.
