"""
Testes unitários automatizados para modelos de Infraestrutura, Usuário e Salas.
Valida criação de tabelas, integridade relacional, constraints e enums.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import Base
from app.models import (
    Campus, Usuario, PerfilUsuario,
    Sala, TipoSala, Equipamento, SalaEquipamento
)


@pytest.fixture
def db_session():
    """Cria banco SQLite em memória com foreign keys ativadas."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def test_create_tables_infraestrutura(db_session):
    """Garante que as tabelas de infraestrutura e espaços físicos foram criadas."""
    expected_tables = {"campus", "usuario", "equipamento", "sala", "sala_equipamento"}
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))


def test_campus_e_usuario_relacionamento(db_session):
    """Valida persistência e relacionamento 1-N entre Campus e Usuario."""
    campus = Campus(nome="Campus Central", cidade="Cidade A", endereco="Rua 1")
    db_session.add(campus)
    db_session.commit()

    user = Usuario(
        campus_id=campus.id, nome="Admin User", email="admin@sigaas.edu",
        senha_hash="hash_secreta", perfil=PerfilUsuario.ADMIN
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.campus.nome == "Campus Central"
    assert user.ativo is True
    assert campus.usuarios[0].email == "admin@sigaas.edu"


def test_usuario_unique_email(db_session):
    """Valida restrição de unicidade no email do usuário."""
    campus = Campus(nome="Campus 1", cidade="C1", endereco="E1")
    db_session.add(campus)
    db_session.commit()

    u1 = Usuario(campus_id=campus.id, nome="U1", email="dup@sigaas.edu", senha_hash="h1", perfil=PerfilUsuario.ALUNO)
    u2 = Usuario(campus_id=campus.id, nome="U2", email="dup@sigaas.edu", senha_hash="h2", perfil=PerfilUsuario.ALUNO)
    db_session.add(u1)
    db_session.commit()

    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_sala_equipamento_e_unicidade(db_session):
    """Valida sala, associação N-N com equipamento e unicidade de bloco/número."""
    campus = Campus(nome="Campus 1", cidade="C1", endereco="E1")
    db_session.add(campus)
    db_session.commit()

    sala = Sala(
        campus_id=campus.id, bloco="A", numero="101", tipo=TipoSala.REGULAR,
        capacidade=40, turnos_disponiveis=["matutino", "noturno"]
    )
    equip = Equipamento(nome="Projetor HD")
    db_session.add_all([sala, equip])
    db_session.commit()

    assoc = SalaEquipamento(sala_id=sala.id, equipamento_id=equip.id, quantidade=2)
    db_session.add(assoc)
    db_session.commit()

    assert len(sala.equipamentos_associados) == 1
    assert sala.turnos_disponiveis == ["matutino", "noturno"]

    # Teste de unicidade uq_sala_campus_bloco_numero
    sala_dup = Sala(
        campus_id=campus.id, bloco="A", numero="101", tipo=TipoSala.LABORATORIO,
        capacidade=20, turnos_disponiveis=["vespertino"]
    )
    db_session.add(sala_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_sala_capacidade_check_constraint(db_session):
    """Valida CheckConstraint capacidade > 0 na sala."""
    campus = Campus(nome="Campus 1", cidade="C1", endereco="E1")
    db_session.add(campus)
    db_session.commit()

    sala_invalida = Sala(
        campus_id=campus.id, bloco="B", numero="999", tipo=TipoSala.REGULAR,
        capacidade=0, turnos_disponiveis=["matutino"]
    )
    db_session.add(sala_invalida)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
