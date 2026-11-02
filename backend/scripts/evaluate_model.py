#!/usr/bin/env python3
"""
Script CLI para avaliacao de metricas do modelo preditivo de absenteismo (Sprint 09).
Calcula matriz de confusao, acuracia, precisao, recall, F1, AUC-ROC e calibracao probabilistica.
Gera relatorios em formato JSON e Markdown para inclusao nas entregas academicas.
"""

import argparse
import sys
from pathlib import Path
from sklearn.model_selection import train_test_split

# Adiciona o diretorio backend ao sys.path para importacao dos modulos da aplicacao
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.services.ia_service import (  # noqa: E402
    carregar_ou_inicializar_modelo,
    extrair_dataset_frequencias,
)
from app.services.ml_evaluator import (  # noqa: E402
    avaliar_pipeline_modelo,
    gerar_relatorio_json,
    gerar_relatorio_markdown,
)


def main():
    parser = argparse.ArgumentParser(
        description="Avaliacao estatistica e analise de threshold do modelo preditivo de absenteismo."
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default=str(BACKEND_DIR / "app" / "ml" / "relatorio_metricas_ml.md"),
        help="Caminho para salvar o relatorio em Markdown.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=str(BACKEND_DIR / "app" / "ml" / "relatorio_metricas_ml.json"),
        help="Caminho para salvar o relatorio em JSON.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.40,
        help="Limiar operacional de probabilidade para sugestao de remanejamento (padrao: 0.40).",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.20,
        help="Proporcao da particao de teste (padrao: 0.20).",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("SIGAAS — Pipeline de Avaliacao Estatistica de Machine Learning")
    print("=" * 70)

    try:
        # Context manager garante fechamento deterministico da conexao sem vazamentos no pool
        with SessionLocal() as db:
            X, y = extrair_dataset_frequencias(db)
            modelo = carregar_ou_inicializar_modelo(db)
    except Exception as e:
        print(f"[AVISO] Nao foi possivel conectar ao banco ({e}). Utilizando priors sinteticos.")
        from app.services.ia_service import _gerar_dados_sinteticos_priors, criar_pipeline_absenteismo
        X, y = _gerar_dados_sinteticos_priors()
        modelo = criar_pipeline_absenteismo(calibrar=True)
        modelo.fit(X, y)

    # Particao estratificada se houver amostras suficientes
    if len(X) >= 10 and len(set(y)) > 1:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=42, stratify=y
        )
    else:
        X_test, y_test = X, y

    resultado = avaliar_pipeline_modelo(modelo, X_test, y_test, threshold=args.threshold)
    metricas = resultado["metricas"]
    sensibilidade = resultado["sensibilidade"]

    md_content = gerar_relatorio_markdown(metricas, sensibilidade)
    gerar_relatorio_json(metricas, sensibilidade, filepath=args.output_json)

    output_md_path = Path(args.output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(md_content, encoding="utf-8")

    print(f"\nAmostras avaliadas: {metricas['total_amostras']}")
    print(f"Acuracia:          {metricas['acuracia']:.4f}")
    print(f"Precisao:          {metricas['precisao']:.4f}")
    print(f"Recall:            {metricas['recall']:.4f}")
    print(f"F1-Score:          {metricas['f1_score']:.4f}")
    if metricas.get("roc_auc") is not None:
        print(f"ROC-AUC:           {metricas['roc_auc']:.4f}")
    if metricas.get("brier_score") is not None:
        print(f"Indice de Brier:   {metricas['brier_score']:.4f}")
    print(f"\nRelatorio Markdown gerado em: {args.output_md}")
    print(f"Relatorio JSON gerado em:     {args.output_json}")
    print("=" * 70)


if __name__ == "__main__":
    main()
