# Baseline Tecnico v1 - Analise de Modelos Locais

Este documento consolida os resultados do benchmark rigoroso realizado na Milestone M4.5, comparando performance objetiva e qualidade subjetiva dos modelos `qwen2.5:0.5b` e `llama3.2:1b`.

## 1. Metricas Objetivas (Performance)

| Modelo | Latencia Media (s) | Tokens/s (Media) | RAM Peak (MB) | Estabilidade (Desvio Padrão) |
|--------|--------------------|------------------|---------------|-----------------------------|
| **qwen2.5:0.5b** | 2.78s | 39.81 | ~6785 MB | 1.53s |
| **llama3.2:1b** | 2.98s | 16.46 | ~7115 MB | 1.82s |

### Observacoes:
- O **Qwen 0.5B** e extremamente veloz (~40 t/s), mas o tempo total e inflado por respostas longas e repetitivas.
- O **Llama 3.2 1B** e significativamente mais lento (~16 t/s), mas tende a ser mais conciso.

## 2. Metricas Subjetivas (Qualidade e Factualidade)

| Categoria | qwen2.5:0.5b | llama3.2:1b | Veredito |
|-----------|--------------|-------------|----------|
| Factualidade Simples | **FALHA** (Nara) | **SUCESSO** (Toquio) | Llama superior |
| Raciocinio Curto | **FALHA** (7 macas) | **FALHA** (0 macas) | Ambos falharam |
| Resumo | **REGULAR** (Verborragico) | **BOM** (Conciso) | Llama superior |
| Instrucao | **FALHA** (Listou CPUs) | **REGULAR** (Nao seguiu linhas) | Llama melhorado |
| Portugues Natural | **BOM** | **BOM** | Empate |
| Alucinacao (1492) | **CRITICO** (Colombo) | **FALHA** (Rei da Espanha) | Ambos alucinaram |

## 3. Conclusao e Modelo de Referencia

O modelo **qwen2.5:0.5b**, apesar de ser o atual baseline do projeto, provou-se **inadequado** para aplicacoes que exigem o minimo de precisao factual ou logica. Suas alucinacoes sao agressivas e confusas.

O modelo **llama3.2:1b** apresenta uma inteligencia sensivelmente superior para fatos e resumos, embora ainda sofra com logica matematica e alucinacoes historicas complexas.

### Decisao para M5:
Utilizaremos o **llama3.2:1b** como novo baseline para testes de voz, pois a qualidade da resposta justifica a perda de velocidade. 

> [!IMPORTANT]
> Para a Milestone M5 (Streaming), o foco sera reduzir a latencia percebida do Llama 3.2 1B, que apesar de mais lento, entrega um conteudo minimamente utilizavel.

---
*Dados baseados na sessao de benchmark: 20260509_200541*
