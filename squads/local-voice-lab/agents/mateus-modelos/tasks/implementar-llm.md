---
task: "Implementar LLM"
order: 1
input: |
  - desenho_tecnico: O plano de Eduardo Executivo.
  - modelo_alvo: Nome do modelo no Ollama (ex: gemma2).
output: |
  - arquivos_modificados: Lista de arquivos com código.
  - log_teste: Resultado da execução do teste local.
  - metricas: Tempo de resposta e consumo de memória.
---

# Implementar LLM

Executa a configuração e integração da camada de inteligência do assistente.

## Process

1. Verificar se o modelo alvo está disponível no Ollama (`ollama list`).
2. Implementar a lógica de conexão e troca de mensagens usando a biblioteca de integração escolhida.
3. Configurar o system prompt conforme as diretrizes de voz da milestone.
4. Criar e rodar um script de teste unitário para validar a resposta do modelo.
5. Reportar resultados de forma objetiva.

## Output Format

```yaml
implementacao:
  status: "success | error"
  detalhes: "O que foi feito"
  teste_local: |
    [Output do script de teste]
  metricas:
    first_token: "..."
    vram: "..."
```

## Output Example

> Use as quality reference, not as rigid template.

```yaml
implementacao:
  status: "success"
  detalhes: "Classe `OllamaClient` atualizada para suportar streaming e novo system prompt otimizado para voz."
  teste_local: |
    Input: 'Olá'
    Output: 'Olá! Como posso ajudar Rudy AI Labs hoje?' (Time: 420ms)
  metricas:
    first_token: "380ms"
    vram: "4.1GB (Gemma2)"
```

## Quality Criteria

- [ ] O código é modular e desacoplado?
- [ ] O tempo de resposta é aceitável para interação por voz?
- [ ] O modelo segue o system prompt estritamente?

## Veto Conditions

Reject and redo if ANY are true:
1. O código faz chamadas para APIs de nuvem.
2. Não foi incluído log de teste funcional.
