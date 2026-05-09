---
execution: subagent
agent: mateus-modelos
inputFile: squads/local-voice-lab/output/technical-design.yaml
outputFile: squads/local-voice-lab/output/llm-implementation.yaml
model_tier: powerful
---

# Step 03: Execução Especialista (LLM/Contexto)

## Context Loading

Load these files before executing:
- `squads/local-voice-lab/output/technical-design.yaml` — Blueprint técnico.
- `pipeline/data/anti-patterns.md` — O que evitar.

## Instructions

### Process
1. Verificar se a tarefa designada é do domínio LLM/Contexto. Se não for, pule este passo.
2. Implementar as mudanças de código nos arquivos alvo.
3. Configurar modelos no Ollama conforme necessário.
4. Validar a implementação rodando o comando de teste definido no design.
5. Coletar métricas de performance (latência, VRAM).

## Output Format

```yaml
entrega:
  agente: "mateus-modelos"
  status: "complete | partial | error"
  detalhes: "..."
  arquivos_alterados: ["...", "..."]
  resultado_teste: "..."
  metricas:
    latency: "..."
    memory: "..."
```

## Output Example

```yaml
entrega:
  agente: "mateus-modelos"
  status: "complete"
  detalhes: "Lógica de RAG local integrada com Ollama para busca de contexto."
  arquivos_alterados: ["src/models/rag.py", "src/config/ollama.json"]
  resultado_teste: "Contexto recuperado com sucesso. Resposta gerada em 1.1s."
  metricas:
    latency: "1.1s"
    memory: "6.2GB VRAM"
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. O agente alterou arquivos de áudio/hardware.
2. Não há evidência de teste local.

## Quality Criteria

- [ ] Código modular e limpo.
- [ ] Uso eficiente de recursos locais.
