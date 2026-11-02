"""
Servico de avaliacao de metricas de Machine Learning para predicao de absenteismo (Sprint 09).
Calcula matriz de confusao, acuracia, precisao, recall, F1, ROC-AUC, Brier score,
analise de sensibilidade de limiar (threshold trade-off a 40%) e exportadores de relatorios.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def avaliar_classificacao(
    y_true: Union[np.ndarray, pd.Series, List[int]],
    y_pred: Union[np.ndarray, pd.Series, List[int]],
    y_prob: Optional[Union[np.ndarray, pd.Series, List[float]]] = None,
) -> Dict[str, Any]:
    """Calcula metricas estatisticas completas de classificacao binaria com tratamento de borda."""
    y_true_arr = np.asarray(y_true, dtype=int)
    y_pred_arr = np.asarray(y_pred, dtype=int)

    # Tratamento para vetor vazio evitando NaN e corrupcao de JSON (RFC 8259)
    if len(y_true_arr) == 0:
        return {
            "matriz_confusao": {"tn": 0, "fp": 0, "fn": 0, "tp": 0},
            "acuracia": 0.0,
            "precisao": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "roc_auc": None,
            "brier_score": None,
            "total_amostras": 0,
            "taxa_positivos_real": 0.0,
            "taxa_positivos_predita": 0.0,
        }

    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))

    roc_auc: Optional[float] = None
    brier: Optional[float] = None

    if y_prob is not None:
        y_prob_arr = np.asarray(y_prob, dtype=float)
        # ROC AUC requer pelo menos 2 classes distintas presentes em y_true
        if len(np.unique(y_true_arr)) > 1:
            try:
                roc_auc = float(roc_auc_score(y_true_arr, y_prob_arr))
            except Exception:
                roc_auc = None

        # Indice de Brier e desacoplado de multiclasse (calculado como MSE entre probabilidades e rotulos)
        try:
            brier = float(brier_score_loss(y_true_arr, y_prob_arr))
        except Exception:
            brier = None

    taxa_real = float(np.mean(y_true_arr))
    taxa_pred = float(np.mean(y_pred_arr))

    return {
        "matriz_confusao": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
        },
        "acuracia": round(acc, 4),
        "precisao": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "brier_score": round(brier, 4) if brier is not None else None,
        "total_amostras": len(y_true_arr),
        "taxa_positivos_real": round(taxa_real, 4),
        "taxa_positivos_predita": round(taxa_pred, 4),
    }


def analisar_sensibilidade_limiar(
    y_true: Union[np.ndarray, pd.Series, List[int]],
    y_prob: Union[np.ndarray, pd.Series, List[float]],
    thresholds: Optional[List[float]] = None,
    limiar_recomendado: float = 0.40,
    peso_fp: float = 1.0,
    peso_fn: float = 2.0,
) -> List[Dict[str, Any]]:
    """
    Analisa a sensibilidade de metricas e o trade-off de negocio variando limiares.
    Atribui peso superior a Falsos Negativos (capacidade desperdicada em sala ociosa).
    """
    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_prob, dtype=float)

    if len(y_true_arr) == 0:
        return []

    if thresholds is None:
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    resultados = []
    for th in thresholds:
        y_pred_th = (y_prob_arr >= th).astype(int)
        cm = confusion_matrix(y_true_arr, y_pred_th, labels=[0, 1])
        tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

        prec = float(precision_score(y_true_arr, y_pred_th, zero_division=0))
        rec = float(recall_score(y_true_arr, y_pred_th, zero_division=0))
        f1 = float(f1_score(y_true_arr, y_pred_th, zero_division=0))
        custo = float((fp * peso_fp) + (fn * peso_fn))

        resultados.append({
            "threshold": round(th, 2),
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "precisao": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "custo_operacional": round(custo, 2),
            "recomendado": bool(abs(th - limiar_recomendado) < 1e-4),
        })

    return resultados


def extrair_probabilidade_classe_positiva(
    pipeline: Any,
    X: Union[pd.DataFrame, np.ndarray],
) -> np.ndarray:
    """Extrai com seguranca a probabilidade da classe 1 (falta), tratando estimadores unimodais."""
    if hasattr(pipeline, "predict_proba"):
        probs = pipeline.predict_proba(X)
        if probs.ndim == 2 and probs.shape[1] > 1:
            classes = getattr(pipeline, "classes_", None)
            if classes is not None and 1 in classes:
                pos_1 = int(np.where(classes == 1)[0][0])
                return probs[:, pos_1]
            return probs[:, 1]
        
        # Caso em que o estimador foi treinado com apenas 1 classe presente
        classes = getattr(pipeline, "classes_", None)
        if classes is not None and len(classes) == 1:
            if classes[0] == 0:
                # Se so ha classe 0, a probabilidade da classe 1 e 0.0
                return np.zeros(len(X), dtype=float)
            if classes[0] == 1:
                return np.ones(len(X), dtype=float)
        return probs.ravel()

    if hasattr(pipeline, "decision_function"):
        df_vals = pipeline.decision_function(X)
        return 1.0 / (1.0 + np.exp(-df_vals))

    return np.asarray(pipeline.predict(X), dtype=float)


def avaliar_pipeline_modelo(
    pipeline: Any,
    X: Union[pd.DataFrame, np.ndarray],
    y: Union[pd.Series, np.ndarray],
    threshold: float = 0.40,
) -> Dict[str, Any]:
    """Executa a avaliacao ponta a ponta de um estimador treinado com limiar operacional."""
    y_prob = extrair_probabilidade_classe_positiva(pipeline, X)
    y_pred = (y_prob >= threshold).astype(int)

    metricas = avaliar_classificacao(y, y_pred, y_prob)
    sensibilidade = analisar_sensibilidade_limiar(y, y_prob, limiar_recomendado=threshold)

    return {
        "limiar_operacional": round(threshold, 2),
        "metricas": metricas,
        "sensibilidade": sensibilidade,
    }


def gerar_relatorio_markdown(
    metricas: Dict[str, Any],
    sensibilidade: List[Dict[str, Any]],
) -> str:
    """Gera relatorio formatado em Markdown com tabelas para documentacao tecnica."""
    cm = metricas.get("matriz_confusao", {})
    roc_str = f"{metricas['roc_auc']:.4f}" if metricas.get("roc_auc") is not None else "N/A"
    brier_str = f"{metricas['brier_score']:.4f}" if metricas.get("brier_score") is not None else "N/A"

    linhas = [
        "## Relatorio de Avaliacao de Machine Learning — Predicao de Absenteismo",
        "",
        "### 1. Metricas Consolidadas de Desempenho",
        "",
        "| Metrica | Valor | Descricao |",
        "| :--- | :---: | :--- |",
        f"| Acuracia | {metricas.get('acuracia', 0.0):.4f} | Proporcao global de acertos |",
        f"| Precisao | {metricas.get('precisao', 0.0):.4f} | Turmas previstas com absenteismo que realmente faltaram |",
        f"| Recall (Sensibilidade) | {metricas.get('recall', 0.0):.4f} | Cobertura real das turmas que necessitavam remanejamento |",
        f"| F1-Score | {metricas.get('f1_score', 0.0):.4f} | Media harmonica balanceada entre precisao e recall |",
        f"| AUC-ROC | {roc_str} | Capacidade discriminativa do estimador |",
        f"| Indice de Brier | {brier_str} | Calibracao probabilistica (quanto menor, mais calibrado) |",
        f"| Total de Amostras | {metricas.get('total_amostras', 0)} | Tamanho do dataset avaliado |",
        "",
        "### 2. Matriz de Confusao",
        "",
        "| Real \\ Predito | Nao Falta (0) | Falta (1) |",
        "| :--- | :---: | :---: |",
        f"| **Nao Falta (0)** | TN: {cm.get('tn', 0)} | FP: {cm.get('fp', 0)} |",
        f"| **Falta (1)** | FN: {cm.get('fn', 0)} | TP: {cm.get('tp', 0)} |",
        "",
        "### 3. Sensibilidade por Limiar e Justificativa do Limiar de 40%",
        "",
        "| Limiar | Precisao | Recall | F1-Score | FP | FN | Custo Operacional | Status |",
        "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]

    for s in sensibilidade:
        status = "Recomendado (Oficial)" if s.get("recomendado") else "Alternativo"
        linhas.append(
            f"| {s['threshold']:.2f} | {s['precisao']:.4f} | {s['recall']:.4f} | "
            f"{s['f1_score']:.4f} | {s['fp']} | {s['fn']} | {s['custo_operacional']:.1f} | {status} |"
        )

    linhas.extend([
        "",
        "> **Justificativa Tecnica do Limiar de 40%:** O custo operacional de um Falso Negativo (sala ociosa com capacidade desperdicada) "
        "e substancialmente superior ao de um Falso Positivo (remanejar sem necessidade estrita). O limiar de 0.40 antecipa a "
        "identificacao de ociosidade critica preservando recall elevado sem saturar a coordenacao com falsos alarmes.",
    ])

    return "\n".join(linhas)


def gerar_relatorio_json(
    metricas: Dict[str, Any],
    sensibilidade: List[Dict[str, Any]],
    filepath: Optional[Union[str, Path]] = None,
) -> str:
    """Serializa os resultados de avaliacao em formato JSON estruturado compativel com RFC 8259."""
    payload = {
        "metricas": metricas,
        "sensibilidade": sensibilidade,
    }
    conteudo = json.dumps(payload, indent=2)

    if filepath is not None:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(conteudo, encoding="utf-8")

    return conteudo
