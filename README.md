# Calculadora de Esforco e Tempo

Kit simples para estimar demandas com escala de 0 a 5 por criterio.

## Objetivo

Ter uma estimativa mais realista para devolutivas ao cliente, combinando:
- Esforco tecnico e de comunicacao
- Incerteza/risco da demanda

## Contexto operacional aplicado

- Time com 2 analistas (voce e sua colega)
- 2 frentes de atuacao em paralelo (1 analista por frente)
- Sem analise de logs de servidor
- Diagnostico por consultas SQL manuais
- Suporte e debug em servico SOAP construido em C#

## O que foi criado

- `calculadora_estimativa.py`: programa em Python (terminal) com score, horas base e buffer de risco.
- `calculadora_frontend.py`: interface visual desktop (Tkinter) em tema dark com selecao por botoes 0 a 5.
- `template_estimativa.csv`: planilha-base para Excel/Google Sheets com formulas.

## Criterios recomendados (0 a 5) e pesos

Os criterios foram ajustados para refletir sua rotina real de suporte.

| Criterio | Peso | Tipo |
|---|---:|---|
| Analise do problema geral | 20 | Esforco |
| Investigacao SQL manual | 20 | Esforco |
| Complexidade de debug no servico C# | 25 | Esforco |
| Esforco de testes no servico SOAP | 15 | Esforco |
| Dependencias externas | 10 | Risco |
| Incerteza tecnica | 10 | Risco |

Soma dos pesos: 100.

## Formula

- Score ponderado (0 a 100):

  `score = soma(nota * peso) / 5`

- Horas base:

  `horas_base = 2 + (score * 0.60)`

- Buffer de risco (8% a 35%):

  `buffer_pct = 0.08 + ((media_risco / 5) * 0.27)`

- Horas finais:

  `horas_finais = horas_base * (1 + buffer_pct)`

- Prazo em dias uteis por frente (1 analista):

  `prazo_frente = horas_finais / 6`

- Prazo em dias uteis com apoio (2 analistas):

  `prazo_apoio = horas_finais / 12`

## Faixas de complexidade

- 0 a 20: Muito baixa
- 21 a 40: Baixa
- 41 a 60: Media
- 61 a 80: Alta
- 81 a 100: Muito alta

## Faixas de confianca da estimativa

- Buffer ate 16%: Confianca alta
- Buffer ate 24%: Confianca media
- Buffer acima de 24%: Confianca baixa

## Como usar o programa Python

1. Abra um terminal na pasta do projeto.
2. Execute:

   ```bash
   python calculadora_estimativa.py
   ```

3. Informe as notas de 0 a 5 para cada criterio.
4. Leia o resumo com score, complexidade, horas e prazo em dias uteis.

## Como usar o frontend (recomendado)

1. Abra um terminal na pasta do projeto.
2. Execute:

  ```bash
  python calculadora_frontend.py
  ```

3. Selecione notas de 0 a 5 usando os botoes de cada criterio.
4. Opcional: use os presets `Baixo`, `Medio` ou `Alto` para preenchimento rapido.
5. Clique em `Calcular estimativa` para ver horas e prazo por frente.

## Como usar a planilha

1. Abra `template_estimativa.csv` no Excel ou Google Sheets.
2. Preencha as colunas de nota de `AnaliseProblemaGeral` ate `IncertezaTecnica`.
3. As colunas de `Score`, `HorasBase`, `BufferRisco`, `HorasFinais` e `PrazoDias` calculam automaticamente.

## Estrutura de analise para lideranca tecnica

Para melhorar assertividade, use os criterios em 3 blocos:

1. Complexidade tecnica
2. Esforco de investigacao e testes
3. Incerteza e dependencias

Essa divisao evita estimativa otimista quando o codigo parece simples, mas exige muito alinhamento e validacao.

## Dica de calibracao (essencial)

Depois de 2 a 4 semanas, compare estimado x realizado e ajuste:
- fator de horas (0.60)
- percentual minimo/maximo de buffer (8% / 35%)
- pesos dos criterios

Assim a previsao fica progressivamente mais aderente ao seu time.
