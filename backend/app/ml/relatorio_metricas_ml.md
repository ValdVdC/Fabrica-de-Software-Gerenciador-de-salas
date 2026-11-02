## Relatorio de Avaliacao de Machine Learning — Predicao de Absenteismo

### 1. Metricas Consolidadas de Desempenho

| Metrica | Valor | Descricao |
| :--- | :---: | :--- |
| Acuracia | 0.5000 | Proporcao global de acertos |
| Precisao | 0.5000 | Turmas previstas com absenteismo que realmente faltaram |
| Recall (Sensibilidade) | 1.0000 | Cobertura real das turmas que necessitavam remanejamento |
| F1-Score | 0.6667 | Media harmonica balanceada entre precisao e recall |
| AUC-ROC | 0.5000 | Capacidade discriminativa do estimador |
| Indice de Brier | 0.2500 | Calibracao probabilistica (quanto menor, mais calibrado) |
| Total de Amostras | 2 | Tamanho do dataset avaliado |

### 2. Matriz de Confusao

| Real \ Predito | Nao Falta (0) | Falta (1) |
| :--- | :---: | :---: |
| **Nao Falta (0)** | TN: 0 | FP: 1 |
| **Falta (1)** | FN: 0 | TP: 1 |

### 3. Sensibilidade por Limiar e Justificativa do Limiar de 40%

| Limiar | Precisao | Recall | F1-Score | FP | FN | Custo Operacional | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 0.10 | 0.5000 | 1.0000 | 0.6667 | 1 | 0 | 1.0 | Alternativo |
| 0.20 | 0.5000 | 1.0000 | 0.6667 | 1 | 0 | 1.0 | Alternativo |
| 0.30 | 0.5000 | 1.0000 | 0.6667 | 1 | 0 | 1.0 | Alternativo |
| 0.40 | 0.5000 | 1.0000 | 0.6667 | 1 | 0 | 1.0 | Recomendado (Oficial) |
| 0.50 | 0.5000 | 1.0000 | 0.6667 | 1 | 0 | 1.0 | Alternativo |
| 0.60 | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2.0 | Alternativo |
| 0.70 | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2.0 | Alternativo |
| 0.80 | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2.0 | Alternativo |
| 0.90 | 0.0000 | 0.0000 | 0.0000 | 0 | 1 | 2.0 | Alternativo |

> **Justificativa Tecnica do Limiar de 40%:** O custo operacional de um Falso Negativo (sala ociosa com capacidade desperdicada) e substancialmente superior ao de um Falso Positivo (remanejar sem necessidade estrita). O limiar de 0.40 antecipa a identificacao de ociosidade critica preservando recall elevado sem saturar a coordenacao com falsos alarmes.