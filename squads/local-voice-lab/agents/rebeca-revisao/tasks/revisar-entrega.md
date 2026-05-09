---
task: "Revisar Entrega"
order: 1
input: |
  - desenho_eduardo: O blueprint original.
  - entrega_especialista: O código e logs do agente executor.
  - arquivos_modificados: Lista de arquivos alterados.
output: |
  - veredito: APPROVE | REJECT
  - justificativa: 1-2 sentenças explicando a decisão.
  - acoes_corretivas: O que deve ser mudado (se REJECT).
---

# Revisar Entrega

Valida a conformidade técnica e a aderência à governança do squad.

## Process

1. Comparar a lista de `arquivos_modificados` com o domínio do especialista (Mateus=LLM/Prompt, Vitor=Áudio/Hardware).
2. Verificar se o código implementado atende aos `criterio_aceite` definidos por Eduardo.
3. Checar por acoplamentos proibidos ou chamadas de API externas.
4. Emitir o veredito final com base nos `criterios_qualidade` do squad.

## Output Format

```yaml
review:
  veredito: "..."
  justificativa: "..."
  detalhes:
    respeito_dominio: "Sim | Não"
    fidelidade_ao_plano: "Sim | Não"
    modularidade: "Sim | Não"
  acoes_requeridas: []
```

## Output Example

> Use as quality reference, not as rigid template.

```yaml
review:
  veredito: "REJECT"
  justificativa: "O especialista Mateus Modelos alterou o arquivo `src/audio/driver.py`, violando as fronteiras de domínio."
  detalhes:
    respeito_dominio: "Não"
    fidelidade_ao_plano: "Sim"
    modularidade: "Não"
  acoes_requeridas:
    - "Remover alterações em `src/audio/driver.py`."
    - "Mover a lógica de prompt para `src/models/prompts.py`."
```

## Quality Criteria

- [ ] A revisão detectou violações de domínio?
- [ ] A justificativa é técnica e imparcial?
- [ ] O caminho para aprovação é claro?

## Veto Conditions

Reject and redo if ANY are true:
1. A revisora deu sugestões estéticas ou de "estilo" em vez de focar na governança.
2. O veredito de aprovação foi dado mesmo com violação de domínio óbvia.
