"""
Testes automatizados para o ciclo de vida de migrations Alembic e script de seed.
"""

from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from alembic.config import Config
from alembic import command

from app.db.session import Base
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

        # Segunda execucao deve ser idempotente sem duplicacoes ou erros
        counts_second = seed_database(session)
        assert counts_second["campus"] == counts_first["campus"]
        assert counts_second["usuario"] == counts_first["usuario"]
        assert counts_second["sala"] == counts_first["sala"]

    Base.metadata.drop_all(engine)
