---
task: "Configurar Áudio"
order: 1
input: |
  - desenho_tecnico: O plano de Eduardo Executivo.
  - componente: "STT | TTS | WakeWord"
output: |
  - arquivos_modificados: Lista de arquivos com código.
  - metricas_audio: Latência, qualidade e consumo de CPU.
  - log_teste: Validação de áudio/transcrição.
---

# Configurar Áudio

Implementa e otimiza a camada de percepção e vocalização do assistente.

## Process

1. Validar a instalação das dependências (Whisper ou Piper) no ambiente.
2. Criar ou atualizar a classe responsável pelo componente de áudio designado.
3. Configurar os parâmetros de hardware (device index, sample rate).
4. Implementar testes de captura (se STT) ou reprodução (se TTS).
5. Executar teste local e medir a latência entre a entrada/saída de dados.

## Output Format

```yaml
configuracao_audio:
  status: "success | error"
  componente: "..."
  teste_executado: |
    [Logs de execução]
  metricas:
    latencia_ms: 0
    cpu_usage: "..."
```

## Output Example

> Use as quality reference, not as rigid template.

```yaml
configuracao_audio:
  status: "success"
  componente: "TTS (Piper)"
  teste_executado: |
    Generated audio for 'Hello Rudy'. 
    Playing via sounddevice... Success.
  metricas:
    latencia_ms: 290
    cpu_usage: "12% Peak"
```

## Quality Criteria

- [ ] O processamento é totalmente offline?
- [ ] A classe de áudio é independente da lógica de negócio?
- [ ] Os recursos de hardware são liberados após o uso?

## Veto Conditions

Reject and redo if ANY are true:
1. Uso de bibliotecas que exigem internet para síntese/transcrição.
2. Latência acima do dobro do benchmark definido sem justificativa técnica.
