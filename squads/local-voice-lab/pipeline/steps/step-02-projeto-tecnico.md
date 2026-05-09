---
execution: inline
agent: eduardo-executivo
inputFile: squads/local-voice-lab/output/milestone-definition.yaml
outputFile: squads/local-voice-lab/output/technical-design.yaml
---

# Step 02: Projeto Técnico

## Context Loading

Load these files before executing:
- `squads/local-voice-lab/output/milestone-definition.yaml` — Definição da milestone atual.
- `pipeline/data/research-brief.md` — Padrões técnicos e arquiteturais.

## Instructions

### Process
1. Analisar a milestone definida no passo anterior.
2. Mapear os arquivos e módulos que precisam ser alterados.
3. Definir a lógica técnica (drivers, APIs locais, prompts).
4. Criar o plano de execução para o especialista.

## Output Format

O output deve seguir esta estrutura:
```yaml
design_tecnico:
  milestone_id: "..."
  arquivos:
    - path: "..."
      action: "update | create"
  plano_execucao:
    - "Passo 1..."
    - "Passo 2..."
  validacao: "..."
```

## Output Example

```yaml
design_tecnico:
  milestone_id: "M1-Core-STT"
  arquivos:
    - path: "src/audio/recorder.py"
      action: "create"
    - path: "src/stt/whisper_engine.py"
      action: "create"
  plano_execucao:
    - "Configurar PyAudio para captura de microfone 16kHz mono."
    - "Instanciar Faster Whisper (base model) e processar o buffer."
    - "Implementar loop de detecção de silêncio para encerrar a captura."
  validacao: "python src/stt/whisper_engine.py --test"
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. O plano sugere acoplamento entre domínios diferentes.
2. Não há um comando claro de validação.

## Quality Criteria

- [ ] Plano detalhado o suficiente para execução autônoma.
- [ ] Arquitetura modular respeitada.
