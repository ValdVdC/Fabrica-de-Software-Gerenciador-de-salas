---
name: ml-production-pipeline
description: >-
  Production machine learning pipeline with scikit-learn, preventing temporal data leakage
  in academic attendance, handling imbalanced classes, calibrated probability outputs,
  and adhering to human-in-the-loop remanejamento rules. Use when developing or training the absenteeism model.
---

# ML Production Pipeline: Tabular Prediction with scikit-learn

Engineering practices for the predictive absenteeism and room reallocation suggestion model in SIGAAS.

## 1. Inviolable Rule: Suggestions Only (Human-in-the-Loop)

- The ML model and background job **NEVER** modify room allocations (`Horario.sala_id`) directly.
- The pipeline only inserts rows into `SugestaoRemanejamento` with `status = 'pendente'`, accompanied by `probabilidade_absenteismo`, `motivo_predicao` e `sala_sugerida_id`.
- Real swaps occur exclusively via explicit human approval (`PATCH /api/v1/sugestoes/{id}`).

## 2. Preventing Temporal Data Leakage

Academic attendance data is inherently sequential:
- **Never use random `train_test_split`**: Random splitting leaks future behavior into past training sets.
- **Use TimeSeriesSplit**: Always partition by academic term, semester, or temporal threshold (e.g. Train: Semestre 2025.1-2025.2; Test: Semestre 2026.1).
- Compute lag features (e.g. historical absence rate over the last 4 weeks) strictly without looking into future dates.

## 3. Imbalanced Classification & Metrics

Absenteeism is a minority class event:
- Do not rely on plain Accuracy (a model predicting 0% absence would achieve 85% accuracy but be useless).
- Optimize for **F1-Score**, **Precision-Recall AUC (PR-AUC)**, and **Recall** of actual high-risk absence events.
- Calibrate model probabilities using `CalibratedClassifierCV` so that a predicted probability of 0.8 actually corresponds to an 80% likelihood of under-occupancy.

## 4. Pipeline Serialization & Background Execution

- Encapsulate preprocessing and classification in a single scikit-learn `Pipeline`:
  ```python
  from sklearn.pipeline import Pipeline
  from sklearn.preprocessing import StandardScaler, OneHotEncoder
  from sklearn.compose import ColumnTransformer
  from sklearn.ensemble import HistGradientBoostingClassifier
  import joblib

  pipeline = Pipeline(steps=[
      ('preprocessor', preprocessor),
      ('classifier', HistGradientBoostingClassifier(random_state=42))
  ])
  pipeline.fit(X_train, y_train)
  joblib.dump(pipeline, "backend/app/ml/modelo_absenteismo.joblib")
  ```
- Background execution runs via `APScheduler` inside FastAPI with try/except logging to prevent scheduler crashes.
