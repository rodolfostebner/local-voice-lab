---
execution: subagent
agent: rebeca-revisao
inputFile: squads/local-voice-lab/output/technical-design.yaml
outputFile: squads/local-voice-lab/output/review-verdict.yaml
on_reject: 3
model_tier: powerful
---

# Step 05: Revisão de Governança

## Context Loading

Load these files before executing:
- `squads/local-voice-lab/output/technical-design.yaml` — O plano original.
- `squads/local-voice-lab/output/llm-implementation.yaml` — Entrega do LLM (se houver).
- `squads/local-voice-lab/output/voice-implementation.yaml` — Entrega de Voz (se houver).

## Instructions

### Process
1. Analisar as entregas dos especialistas contra o desenho técnico.
2. Verificar se houve "invasão de domínio" (agente mexendo em arquivos fora de sua especialidade).
3. Avaliar se a arquitetura modular foi mantida.
4. Emitir veredito binário (APPROVE ou REJECT).

## Output Format

```yaml
review:
  veredito: "APPROVE | REJECT"
  justificativa: "..."
  pontos_falha: []
```

## Output Example

```yaml
review:
  veredito: "REJECT"
  justificativa: "Violação de domínio detectada."
  pontos_falha:
    - "Vitor Voz alterou `src/models/prompts.py`, que pertence ao domínio do Mateus Modelos."
    - "O plano técnico não previa alterações neste arquivo."
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. A revisora deu aprovação para código que quebra a modularidade.
2. A justificativa é subjetiva (estilo) em vez de baseada em governança.

## Quality Criteria

- [ ] Veredito 100% alinhado com as regras do squad.
- [ ] Detecção precisa de desvios de domínio.
