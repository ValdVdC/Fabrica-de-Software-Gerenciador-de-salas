"""
Testes automatizados TDD para o modulo de avaliacao de metricas de Machine Learning (Sprint 09).
Valida calculo de matriz de confusao, metricas de classificacao, calibracao probabilistica (Brier),
analise de sensibilidade de limiares (threshold trade-off a 40%) e exportadores de relatorio.
Inclui cobertura estrita contra condicoes de borda (vetores vazios, classes unicas, serializacao RFC 8259).
"""

import json
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression

from app.services.ml_evaluator import (
    analisar_sensibilidade_limiar,
    avaliar_classificacao,
    avaliar_pipeline_modelo,
    extrair_probabilidade_classe_positiva,
    gerar_relatorio_json,
    gerar_relatorio_markdown,
)


@pytest.fixture
def dados_teste_binarios():
    """Dataset sintetico com classes balanceadas e probabilidades calibradas para teste."""
    y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    y_prob = np.array([0.05, 0.15, 0.35, 0.45, 0.20, 0.42, 0.65, 0.80, 0.90, 0.38])
    return y_true, y_prob


def test_avaliar_classificacao_metricas_basicas(dados_teste_binarios):
    """Garante calculo exato e deterministico das metricas estatisticas."""
    y_true, y_prob = dados_teste_binarios
    y_pred = (y_prob >= 0.40).astype(int)

    metricas = avaliar_classificacao(y_true, y_pred, y_prob)

    assert "matriz_confusao" in metricas
    cm = metricas["matriz_confusao"]
    assert cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"] == len(y_true)
    assert cm["tp"] == 4  # indices 5, 6, 7, 8
    assert cm["fn"] == 1  # indice 9 (prob 0.38 < 0.40)
    assert cm["fp"] == 1  # indice 3 (prob 0.45 >= 0.40)
    assert cm["tn"] == 4  # indices 0, 1, 2, 4

    assert metricas["total_amostras"] == 10
    # Assercoes exatas baseadas na matriz de confusao (TP=4, TN=4, FP=1, FN=1)
    assert metricas["acuracia"] == 0.8000
    assert metricas["precisao"] == 0.8000
    assert metricas["recall"] == 0.8000
    assert metricas["f1_score"] == 0.8000
    assert metricas["roc_auc"] == 0.9200
    assert metricas["brier_score"] is not None
    assert metricas["brier_score"] == 0.1283


def test_avaliar_classificacao_vetor_vazio_rfc8259():
    """Garante que entrada vazia nao emita NaN e gere JSON estritamente compativel com RFC 8259."""
    metricas = avaliar_classificacao([], [], [])
    assert metricas["total_amostras"] == 0
    assert metricas["acuracia"] == 0.0
    assert metricas["precisao"] == 0.0
    assert metricas["recall"] == 0.0
    assert metricas["f1_score"] == 0.0
    assert metricas["roc_auc"] is None
    assert metricas["brier_score"] is None

    sensibilidade = analisar_sensibilidade_limiar([], [])
    assert sensibilidade == []

    # Validacao estrita contra presenca de literais NaN
    json_str = gerar_relatorio_json(metricas, sensibilidade)
    assert "NaN" not in json_str
    parsed = json.loads(json_str)
    assert parsed["metricas"]["acuracia"] == 0.0


def test_avaliar_classificacao_sem_probabilidades():
    """Valida comportamento quando apenas predicoes discretas estao disponiveis."""
    y_true = np.array([0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 1])

    metricas = avaliar_classificacao(y_true, y_pred)
    assert metricas["roc_auc"] is None
    assert metricas["brier_score"] is None
    assert metricas["acuracia"] == 0.75
    assert metricas["matriz_confusao"]["tp"] == 2
    assert metricas["matriz_confusao"]["fp"] == 1


def test_avaliar_classificacao_casos_borda_divisao_zero():
    """Garante que cenarios com zero positivos preditos nao lancem ZeroDivisionError."""
    y_true = np.array([0, 0, 0])
    y_pred = np.array([0, 0, 0])
    y_prob = np.array([0.1, 0.2, 0.15])

    metricas = avaliar_classificacao(y_true, y_pred, y_prob)
    assert metricas["precisao"] == 0.0
    assert metricas["recall"] == 0.0
    assert metricas["f1_score"] == 0.0
    assert metricas["roc_auc"] is None  # Apenas 1 classe em y_true anula ROC-AUC
    # Brier score deve ser calculado mesmo com apenas 1 classe (MSE das probabilidades com zeros)
    assert metricas["brier_score"] is not None
    assert metricas["brier_score"] == pytest.approx(0.0241, abs=1e-3)


def test_estimador_treinado_apenas_classe_zero():
    """Garante que estimador treinado apenas com classe 0 nao atribua prob 100% para falta."""
    X = pd.DataFrame({"feat1": [1, 2, 3], "feat2": [0, 0, 0]})
    y = np.array([0, 0, 0])

    clf = DummyClassifier(strategy="most_frequent")
    clf.fit(X, y)
    assert len(clf.classes_) == 1
    assert clf.classes_[0] == 0

    probs_falta = extrair_probabilidade_classe_positiva(clf, X)
    # Se so ha classe 0, a probabilidade de falta deve ser estritamente zero
    assert np.all(probs_falta == 0.0)

    resultado = avaliar_pipeline_modelo(clf, X, y, threshold=0.40)
    # Zero falsos positivos devem ser disparados
    assert resultado["metricas"]["matriz_confusao"]["fp"] == 0
    assert resultado["metricas"]["matriz_confusao"]["tp"] == 0


def test_analisar_sensibilidade_limiar(dados_teste_binarios):
    """Testa a analise de trade-off de negocio variando thresholds e limiar recomendado customizado."""
    y_true, y_prob = dados_teste_binarios
    limiares = [0.2, 0.4, 0.6, 0.8]

    sensibilidade = analisar_sensibilidade_limiar(y_true, y_prob, thresholds=limiares, limiar_recomendado=0.40)

    assert len(sensibilidade) == len(limiares)
    item_40 = next(item for item in sensibilidade if abs(item["threshold"] - 0.40) < 1e-4)
    assert item_40["tp"] == 4
    assert item_40["fp"] == 1
    assert item_40["recall"] == 0.8
    assert item_40["custo_operacional"] == 3.0  # FP(1)*1.0 + FN(1)*2.0 = 3.0
    assert item_40["recomendado"] is True

    # Teste de limiar customizado
    sens_custom = analisar_sensibilidade_limiar(y_true, y_prob, thresholds=[0.3, 0.5], limiar_recomendado=0.50)
    assert sens_custom[0]["recomendado"] is False
    assert sens_custom[1]["recomendado"] is True


def test_avaliar_pipeline_modelo_integrado():
    """Testa a avaliacao integrada de um estimador treinado com X e y pandas."""
    X = pd.DataFrame({"feat1": [1, 2, 3, 4, 5, 6, 7, 8], "feat2": [0, 1, 0, 1, 0, 1, 0, 1]})
    y = pd.Series([0, 0, 0, 0, 1, 1, 1, 1])

    clf = LogisticRegression()
    clf.fit(X, y)

    resultado = avaliar_pipeline_modelo(clf, X, y, threshold=0.40)

    assert "metricas" in resultado
    assert "sensibilidade" in resultado
    assert "limiar_operacional" in resultado
    assert resultado["limiar_operacional"] == 0.40
    assert resultado["metricas"]["acuracia"] >= 0.7


def test_exportacao_relatorios_markdown_e_json(dados_teste_binarios, tmp_path):
    """Valida geracao de relatorio formatado em Markdown e JSON estruturado."""
    y_true, y_prob = dados_teste_binarios
    y_pred = (y_prob >= 0.40).astype(int)

    metricas = avaliar_classificacao(y_true, y_pred, y_prob)
    sensibilidade = analisar_sensibilidade_limiar(y_true, y_prob, thresholds=[0.3, 0.4, 0.5])

    md = gerar_relatorio_markdown(metricas, sensibilidade)
    assert "## Relatorio de Avaliacao de Machine Learning" in md
    assert "Matriz de Confusao" in md
    assert "Sensibilidade por Limiar" in md
    assert "0.40" in md

    # Exportacao JSON
    json_path = tmp_path / "metricas_ml.json"
    json_str = gerar_relatorio_json(metricas, sensibilidade, filepath=json_path)
    assert json_path.is_file()

    parsed = json.loads(json_str)
    assert "metricas" in parsed
    assert "sensibilidade" in parsed
    assert parsed["metricas"]["total_amostras"] == 10
