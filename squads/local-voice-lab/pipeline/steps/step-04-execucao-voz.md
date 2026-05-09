---
execution: subagent
agent: vitor-voz
inputFile: squads/local-voice-lab/output/technical-design.yaml
outputFile: squads/local-voice-lab/output/voice-implementation.yaml
model_tier: powerful
---

# Step 04: Execução Especialista (Voz/Áudio)

## Context Loading

Load these files before executing:
- `squads/local-voice-lab/output/technical-design.yaml` — Blueprint técnico.
- `pipeline/data/anti-patterns.md` — O que evitar.

## Instructions

### Process
1. Verificar se a tarefa designada é do domínio Voz/Áudio. Se não for, pule este passo.
2. Implementar mudanças nos módulos de STT (Whisper) ou TTS (Piper).
3. Ajustar parâmetros de hardware e drivers.
4. Validar a captura/reprodução rodando o comando de teste.
5. Coletar métricas de latência sonora.

## Output Format

```yaml
entrega:
  agente: "vitor-voz"
  status: "complete | partial | error"
  detalhes: "..."
  arquivos_alterados: ["...", "..."]
  resultado_teste: "..."
  metricas:
    audio_latency: "..."
    cpu_load: "..."
```

## Output Example

```yaml
entrega:
  agente: "vitor-voz"
  status: "complete"
  detalhes: "VAD (Voice Activity Detection) implementado para reduzir ruído de fundo."
  arquivos_alterados: ["src/audio/vad.py", "src/stt/engine.py"]
  resultado_teste: "Captura inicia apenas com fala. Falsos positivos reduzidos em 80%."
  metricas:
    audio_latency: "150ms"
    cpu_load: "8% Peak"
```

## Veto Conditions

Reject and redo if ANY are true:
1. O agente alterou a lógica do LLM ou prompts.
2. O código usa serviços de transcrição na nuvem.

## Quality Criteria

- [ ] Latência mínima.
- [ ] Liberação correta de recursos de áudio.
