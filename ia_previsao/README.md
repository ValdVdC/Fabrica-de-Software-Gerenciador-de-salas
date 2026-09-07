# SIGAAS IA — Previsão de Falta e Sugestão de Remanejamento

Módulo de Machine Learning utilizando **scikit-learn** para estimar a probabilidade de baixa frequência em horários de aulas e propor sugestões de remanejamento de salas.

## Diretrizes Invioláveis (`AGENTS.md`)
1. O modelo roda fora do ciclo de requisição HTTP (via job em background no FastAPI ou script agendado).
2. **NUNCA troca uma sala diretamente**. O modelo apenas insere uma `SugestaoRemanejamento` com status `pendente`.
3. A alteração de alocação de sala só é efetivada após aprovação humana explícita por um Admin/Coordenação via endpoint `PATCH /sugestoes/{id}`.

## Estrutura
- `/dados`: Datasets brutos e processados (dados históricos, públicos e sintéticos).
- `/scripts`: Scripts de extração de features, treinamento e validação de hiperparâmetros.
- `/modelos`: Modelos serializados (`.joblib`).
