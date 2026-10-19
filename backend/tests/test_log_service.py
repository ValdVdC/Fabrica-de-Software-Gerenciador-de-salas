"""
Testes automatizados unitarios e de integracao para o servico de log (log_service).
Cobre o registro padronizado de eventos em log_alocacao com snapshot_evento,
rastreabilidade de usuario, campus_id e tipos de eventos do dominio.
"""

from datetime import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models import (
    Campus,
    Curso,
    Disciplina,
    Horario,
    PerfilUsuario,
    Sala,
    TipoEventoLog,
    TipoSala,
    Turma,
    Turno,
    Usuario,
)
from app.services.log_service import registrar_evento


@pytest.fixture
def db_session():
    """Sessao SQLite isolada em memoria para os testes do servico."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def dados_cenario(db_session: Session):
    """Cria entidades basicas para associacao nos testes de log."""
    campus1 = Campus(nome="Campus Central", cidade="Petrolina", endereco="Av. Integracao, 100")
    campus2 = Campus(nome="Campus Juazeiro", cidade="Juazeiro", endereco="Av. Brasil, 200")
    db_session.add_all([campus1, campus2])
    db_session.flush()

    user = Usuario(
        campus_id=campus1.id,
        nome="Coordenador Teste",
        email="coord@teste.com",
        senha_hash="hash_placeholder",
        perfil=PerfilUsuario.COORDENADOR,
    )
    db_session.add(user)
    db_session.flush()

    sala = Sala(
        campus_id=campus1.id,
        bloco="A",
        numero="101",
        tipo=TipoSala.REGULAR,
        capacidade=50,
        turnos_disponiveis=["matutino", "vespertino"],
    )
    db_session.add(sala)
    db_session.flush()

    curso = Curso(campus_id=campus1.id, nome="Engenharia de Software", codigo="ES")
    db_session.add(curso)
    db_session.flush()

    disciplina = Disciplina(curso_id=curso.id, nome="Arquitetura de Software", codigo="ES101", carga_horaria=60)
    db_session.add(disciplina)
    db_session.flush()

    turma = Turma(
        disciplina_id=disciplina.id,
        professor_id=None,
        periodo_letivo="2026.1",
        num_matriculados=30,
        turno_preferido=Turno.MATUTINO,
    )
    db_session.add(turma)
    db_session.flush()

    horario = Horario(
        campus_id=campus1.id,
        turma_id=turma.id,
        sala_id=sala.id,
        dia_semana=0,
        hora_inicio=time(8, 0),
        hora_fim=time(10, 0),
    )
    db_session.add(horario)
    db_session.commit()

    return {
        "campus1": campus1,
        "campus2": campus2,
        "user": user,
        "sala": sala,
        "turma": turma,
        "horario": horario,
    }


def test_registrar_evento_criacao_sala(db_session: Session, dados_cenario: dict):
    """Valida registro de log para evento de criacao de sala com campus_id e snapshot."""
    user = dados_cenario["user"]
    sala = dados_cenario["sala"]

    log = registrar_evento(
        db=db_session,
        tipo=TipoEventoLog.CRIACAO,
        usuario=user,
        campus_id=sala.campus_id,
        entidade="sala",
        entidade_id=sala.id,
        detalhes="Criacao de sala pelo coordenador",
    )
    db_session.commit()

    assert log.id is not None
    assert log.campus_id == sala.campus_id
    assert log.tipo_evento == TipoEventoLog.CRIACAO
    assert log.usuario_responsavel == user.id
    assert log.snapshot_evento == {"entidade": "sala", "entidade_id": sala.id}
    assert log.detalhes == "Criacao de sala pelo coordenador"
    assert log.timestamp is not None


def test_registrar_evento_alteracao_turma(db_session: Session, dados_cenario: dict):
    """Valida registro de alteracao de turma com metadados adicionais."""
    user = dados_cenario["user"]
    turma = dados_cenario["turma"]

    log = registrar_evento(
        db=db_session,
        tipo=TipoEventoLog.ALTERACAO,
        usuario=user.id,
        campus_id=dados_cenario["campus1"].id,
        entidade="turma",
        entidade_id=turma.id,
        detalhes="Alteracao de turno da turma",
        snapshot_extra={"turno_anterior": "matutino", "novo_turno": "noturno"},
    )
    db_session.commit()

    assert log.campus_id == dados_cenario["campus1"].id
    assert log.tipo_evento == TipoEventoLog.ALTERACAO
    assert log.usuario_responsavel == user.id
    assert log.snapshot_evento == {
        "entidade": "turma",
        "entidade_id": turma.id,
        "turno_anterior": "matutino",
        "novo_turno": "noturno",
    }


def test_registrar_evento_remocao_usuario(db_session: Session, dados_cenario: dict):
    """Valida registro de remocao de entidade reutilizando TipoEventoLog.CANCELAMENTO."""
    user = dados_cenario["user"]

    log = registrar_evento(
        db=db_session,
        tipo=TipoEventoLog.CANCELAMENTO,
        usuario=user,
        campus_id=dados_cenario["campus1"].id,
        entidade="usuario",
        entidade_id=999,
        detalhes="Remocao de usuario inativo",
    )
    db_session.commit()

    assert log.tipo_evento == TipoEventoLog.CANCELAMENTO
    assert log.snapshot_evento == {"entidade": "usuario", "entidade_id": 999}
    assert log.detalhes == "Remocao de usuario inativo"


def test_registrar_evento_infere_campus_de_horario(db_session: Session, dados_cenario: dict):
    """Verifica que quando campus_id e omitido mas horario_id e passado, infere o campus."""
    user = dados_cenario["user"]
    horario = dados_cenario["horario"]

    log = registrar_evento(
        db=db_session,
        tipo="alteracao",
        usuario=user,
        campus_id=None,
        horario_id=horario.id,
        detalhes="Remanejamento de horario pontual",
    )
    db_session.commit()

    assert log.campus_id == horario.campus_id
    assert log.horario_id == horario.id
    assert log.tipo_evento == TipoEventoLog.ALTERACAO
