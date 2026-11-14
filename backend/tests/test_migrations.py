"""
Testes automatizados para o ciclo de vida de migrations Alembic, paridade de schema e script de seed.
"""

from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from alembic.config import Config
from alembic import command

from app.db.session import Base
import app.models  # noqa: F401
from scripts.seed_db import seed_database


@pytest.fixture
def sqlite_db_path(tmp_path):
    return tmp_path / "test_mig.db"


@pytest.fixture
def alembic_cfg(sqlite_db_path):
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{sqlite_db_path}")
    return cfg


def test_alembic_upgrade_and_downgrade_cycle(alembic_cfg, sqlite_db_path):
    """Valida o ciclo completo de upgrade(head) e downgrade(base) via Alembic."""
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(f"sqlite:///{sqlite_db_path}")
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = {
        "campus", "usuario", "equipamento", "sala", "sala_equipamento",
        "curso", "disciplina", "turma", "matricula", "horario",
        "log_alocacao", "frequencia", "previsao_falta", "sugestao_remanejamento"
    }
    assert expected_tables.issubset(set(tables))

    # Downgrade para base deve remover todas as tabelas da aplicacao
    command.downgrade(alembic_cfg, "base")
    inspector = inspect(engine)
    tables_after = inspector.get_table_names()
    for table in expected_tables:
        assert table not in tables_after


def test_seed_database_idempotency():
    """Valida criacao de dados sinteticos e garantia de idempotencia na segunda execucao."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        counts_first = seed_database(session)
        assert counts_first["campus"] >= 2
        assert counts_first["usuario"] >= 5
        assert counts_first["sala"] >= 4
        assert counts_first["horario"] >= 3
        assert counts_first["frequencia"] >= 1

        # Segunda execucao deve ser idempotente sem duplicacoes ou erros
        counts_second = seed_database(session)
        assert counts_second == counts_first

    Base.metadata.drop_all(engine)


def test_schema_parity_alembic_models(alembic_cfg, sqlite_db_path):
    """Valida paridade estrutural 100% entre Base.metadata e alembic upgrade head."""
    command.upgrade(alembic_cfg, "head")
    engine = create_engine(f"sqlite:///{sqlite_db_path}")
    inspector = inspect(engine)

    migrated_tables = set(inspector.get_table_names()) - {"alembic_version"}
    model_tables = set(Base.metadata.tables.keys())
    assert migrated_tables == model_tables, (
        f"Divergencia de tabelas. Migrated - Models: {migrated_tables - model_tables}, "
        f"Models - Migrated: {model_tables - migrated_tables}"
    )

    for table_name, table in Base.metadata.tables.items():
        migrated_cols = {col["name"]: col for col in inspector.get_columns(table_name)}
        model_cols = {col.name: col for col in table.columns}
        assert set(migrated_cols.keys()) == set(model_cols.keys()), (
            f"Divergencia de colunas em '{table_name}': "
            f"{set(migrated_cols.keys()) ^ set(model_cols.keys())}"
        )
        for col_name, model_col in model_cols.items():
            assert migrated_cols[col_name]["nullable"] == model_col.nullable, (
                f"Divergencia de nullable em '{table_name}.{col_name}'"
            )

        migrated_indexes = {
            (idx["name"], tuple(idx["column_names"]), bool(idx["unique"]))
            for idx in inspector.get_indexes(table_name)
            if idx["name"] and not idx["name"].startswith("sqlite_autoindex_")
        }
        model_indexes = {
            (idx.name, tuple(col.name for col in idx.columns), bool(idx.unique))
            for idx in table.indexes
        }
        assert migrated_indexes == model_indexes, (
            f"Divergencia de indices em '{table_name}'. "
            f"Migrated - Models: {migrated_indexes - model_indexes}, "
            f"Models - Migrated: {model_indexes - migrated_indexes}"
        )

    expected_composite_indexes = {
        "horario": {
            "ix_horario_turma_dia_hora",
            "ix_horario_sala_dia_hora",
            "ix_horario_campus_dia_hora",
        },
        "frequencia": {"ix_frequencia_horario_data"},
        "log_alocacao": {"ix_log_alocacao_campus_id_timestamp"},
        "sugestao_remanejamento": {"ix_sugestao_remanejamento_status_criado_em"},
        "previsao_falta": {"ix_previsao_falta_horario_data"},
    }
    for table_name, expected_names in expected_composite_indexes.items():
        actual_names = {idx["name"] for idx in inspector.get_indexes(table_name)}
        assert expected_names.issubset(actual_names), (
            f"Indices compostos ausentes em '{table_name}': {expected_names - actual_names}"
        )

    # Valida reversibilidade da ultima migration (downgrade -1 e upgrade head)
    command.downgrade(alembic_cfg, "-1")
    inspector_after_down = inspect(engine)
    horario_idx_down = {idx["name"] for idx in inspector_after_down.get_indexes("horario")}
    assert "ix_horario_turma_dia_hora" not in horario_idx_down

    command.upgrade(alembic_cfg, "head")
    inspector_after_up = inspect(engine)
    horario_idx_up = {idx["name"] for idx in inspector_after_up.get_indexes("horario")}
    assert "ix_horario_turma_dia_hora" in horario_idx_up
