# Baseline Tecnico v2 - Analise de Modelos Locais (Expandido)

Este documento consolida os resultados do benchmark expandido (M4.5), comparando os modelos `qwen2.5:0.5b`, `qwen2.5:1.5b`, `llama3.2:1b` e `gemma3:4b`.

## 1. Metricas Objetivas (Performance & Recursos)

| Modelo | Latencia Media (s) | Tokens/s (Media) | RAM Peak (MB) | Estabilidade (Desvio) |
|--------|--------------------|------------------|---------------|-----------------------|
| **qwen2.5:0.5b** | 3.29s | 39.75 | ~6407 MB | 3.17s |
| **qwen2.5:1.5b** | 9.17s | 17.42 | ~7106 MB | 10.56s |
| **llama3.2:1b** | 8.39s | 16.47 | ~6735 MB | 14.46s |
| **gemma3:4b** | 19.33s | 6.85 | **~7234 MB** | 17.92s |

### Observacoes:
- **Gemma 3 4B** e o mais lento (~7 t/s), o que pode ser desafiador para voz síncrona sem streaming.
- **Llama 3.2 1B** e **Qwen 1.5B** tem performance similar em tokens/s, mas o Llama e mais eficiente em RAM.
- Os tempos de latência média foram afetados por categorias de "Respostas Longas".

## 2. Metricas Subjetivas (Qualidade & Inteligencia)

| Categoria | qwen 0.5b | qwen 1.5b | llama 1b | gemma 4b | Veredito |
|-----------|-----------|-----------|----------|----------|----------|
| Factualidade | FALHA | BOM | BOM | **EXCELENTE** | Gemma superior |
| Raciocinio | FALHA | FALHA | FALHA | **FALHA** | Todos falharam no 3+2-1 |
| Instrucao | CRITICO | CRITICO | REGULAR | **EXCELENTE** | Gemma seguiu formatação |
| Alucinacao | CRITICO | CRITICO | FALHA | **SUCESSO** | Gemma detectou anacronismo |
| Multi-turn | BOM | BOM | BOM | **BOM** | Todos lembraram o nome |
| Naturalidade | BOM | BOM | BOM | **EXCELENTE** | Gemma e o mais amigavel |

## 3. Conclusao e Modelo de Referencia

### O Salto Qualitativo do Gemma 3 4B
O modelo **Gemma 3 4B** apresentou um salto qualitativo **gigantesco**. Foi o único a não alucinar sobre o presidente do Brasil em 1492 e o único a seguir rigorosamente instruções de formatação ("um por linha, sem numeração"). Sua naturalidade conversacional e formatação são de nível premium.

### O Problema da Latencia
Com ~7 tokens/s no hardware atual (CPU), o Gemma 4B leva ~15-20 segundos para respostas médias. Para uso em tempo real, isso exige obrigatoriamente a Milestone M5 (Streaming).

### Modelo Recomendado por Perfil:
1.  **Modo Premium (Qualidade):** `gemma3:4b`. Inigualável em inteligência para este porte.
2.  **Modo Standard (Equilíbrio):** `llama3.2:1b`. Inteligência aceitável com latência menor.
3.  **Modo Fast (Captura/Simples):** `qwen2.5:0.5b` (apenas para comandos curtos, devido às alucinações).

### Decisao para M5:
Iniciaremos a M5 focando na implementação de **Streaming** para o **gemma3:4b**, visando tornar o modelo "Premium" utilizável em voz através da redução da latência percebida.

---
*Dados baseados na sessao de benchmark: 20260509_201437*
