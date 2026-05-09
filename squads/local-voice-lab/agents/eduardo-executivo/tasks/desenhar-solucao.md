---
task: "Desenhar Solução"
order: 2
input: |
  - milestone_refinada: O output da tarefa anterior.
  - estrutura_arquivos: Listagem de diretórios e arquivos relevantes.
output: |
  - plano_tecnico: Passos exatos de codificação.
  - arquivos_alvo: Quais arquivos serão criados ou editados.
  - integracoes_necessarias: Comandos CLI ou APIs locais a serem usadas.
---

# Desenhar Solução

Cria o blueprint técnico para que o especialista possa executar a tarefa sem dúvidas arquiteturais.

## Process

1. Identificar os pontos de entrada no código atual.
2. Definir a estrutura da nova classe ou módulo (se necessário).
3. Verificar compatibilidade com Ollama, Whisper ou Piper (CLI/API).
4. Escrever o plano de execução passo-a-passo.

## Output Format

```yaml
desenho_tecnico:
  arquivos:
    - path: "src/..."
      action: "create | update"
  plano:
    - "Passo 1..."
    - "Passo 2..."
  validacao_local: "Comando para testar"
```

## Output Example

> Use as quality reference, not as rigid template.

```yaml
desenho_tecnico:
  arquivos:
    - path: "src/audio/tts_engine.py"
      action: "create"
    - path: "src/main.py"
      action: "update"
  plano:
    - "Criar wrapper Python para o binário do Piper."
    - "Implementar método `speak(text)` que gera WAV temporário e reproduz via `aplay`."
    - "Integrar o `speak` no loop principal após o retorno do LLM."
  validacao_local: "python src/audio/tts_engine.py --test 'Testing audio output'"
```

## Quality Criteria

- [ ] O plano segue a arquitetura modular?
- [ ] O especialista tem todas as informações para codar sem perguntar ao usuário?

## Veto Conditions

Reject and redo if ANY are true:
1. O desenho sugere acoplamento forte entre Voz e LLM.
2. Não há uma forma clara de validar a entrega localmente.
