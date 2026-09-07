"""
Testes unitários para modelos de Infraestrutura, Usuário e Salas.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, StatementError

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


@pytest.fixture
def campus(db_session):
    """Fixture de campus para testes relacionais."""
    c = Campus(nome="Campus Central", cidade="Cidade A", endereco="Rua 1")
    db_session.add(c)
    db_session.commit()
    return c


def test_create_tables_infraestrutura(db_session):
    expected = {"campus", "usuario", "equipamento", "sala", "sala_equipamento"}
    assert expected.issubset(set(Base.metadata.tables.keys()))


def test_campus_e_usuario_relacionamento(db_session, campus):
    user = Usuario(campus_id=campus.id, nome="Admin", email="admin@sigaas.edu", senha_hash="h", perfil=PerfilUsuario.ADMIN)
    db_session.add(user)
    db_session.commit()

    assert user.id is not None and user.campus.nome == "Campus Central"
    assert user.ativo is True and campus.usuarios[0].email == "admin@sigaas.edu"


def test_usuario_unique_email(db_session, campus):
    u1 = Usuario(campus_id=campus.id, nome="U1", email="dup@sigaas.edu", senha_hash="h", perfil=PerfilUsuario.ALUNO)
    u2 = Usuario(campus_id=campus.id, nome="U2", email="dup@sigaas.edu", senha_hash="h", perfil=PerfilUsuario.ALUNO)
    db_session.add_all([u1, u2])
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_sala_equipamento_e_constraints(db_session, campus):
    sala = Sala(campus_id=campus.id, bloco="A", numero="101", tipo=TipoSala.REGULAR, capacidade=40, turnos_disponiveis=["matutino"])
    equip = Equipamento(nome="Projetor HD")
    db_session.add_all([sala, equip])
    db_session.commit()

    assoc = SalaEquipamento(sala_id=sala.id, equipamento_id=equip.id, quantidade=2)
    db_session.add(assoc)
    db_session.commit()
    assert len(sala.equipamentos_associados) == 1

    # Unicidade bloco/numero no campus
    sala_dup = Sala(campus_id=campus.id, bloco="A", numero="101", tipo=TipoSala.LABORATORIO, capacidade=20, turnos_disponiveis=["matutino"])
    db_session.add(sala_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Capacidade > 0
    sala_inv = Sala(campus_id=campus.id, bloco="B", numero="999", tipo=TipoSala.REGULAR, capacidade=0, turnos_disponiveis=["matutino"])
    db_session.add(sala_inv)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_enum_round_trip_and_validation(db_session, campus):
    user = Usuario(campus_id=campus.id, nome="Prof", email="prof@sigaas.edu", senha_hash="h", perfil=PerfilUsuario.PROFESSOR)
    sala = Sala(campus_id=campus.id, bloco="C", numero="301", tipo=TipoSala.AUDITORIO, capacidade=100, turnos_disponiveis=["matutino"])
    db_session.add_all([user, sala])
    db_session.commit()

    cid, uid, sid = campus.id, user.id, sala.id
    db_session.expunge_all()

    assert db_session.get(Usuario, uid).perfil == PerfilUsuario.PROFESSOR
    assert isinstance(db_session.get(Usuario, uid).perfil, PerfilUsuario)
    assert db_session.get(Sala, sid).tipo == TipoSala.AUDITORIO
    assert isinstance(db_session.get(Sala, sid).tipo, TipoSala)

    # Rejeicao de valor invalido
    u_inv = Usuario(campus_id=cid, nome="Inv", email="inv@sigaas.edu", senha_hash="h", perfil="invalido")
    db_session.add(u_inv)
    with pytest.raises((StatementError, LookupError, IntegrityError, ValueError)):
        db_session.commit()
    db_session.rollback()
