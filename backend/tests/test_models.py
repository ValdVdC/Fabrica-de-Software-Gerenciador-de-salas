"""
Testes unitários automatizados para os modelos SQLAlchemy 2.0 do SIGAAS.
Valida criação de tabelas, integridade relacional, constraints e enums.
"""

from datetime import date, time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import Base
from app.models import (
    Campus, Usuario, PerfilUsuario,
    Sala, TipoSala, Equipamento, SalaEquipamento,
    Curso, Disciplina, Turma, Turno, Matricula,
    Horario, Frequencia, PrevisaoFalta,
    SugestaoRemanejamento, StatusSugestao,
    LogAlocacao, TipoEventoLog
)


@pytest.fixture
def db_session():
    """Cria banco SQLite em memória com foreign keys ativadas."""
    engine = create_engine("sqlite:///:memory:")
    # Ativa integridade referencial no SQLite
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def test_create_all_tables(db_session):
    """Garante que todas as 14 tabelas especificadas foram criadas."""
    expected_tables = {
        "campus", "usuario", "equipamento", "sala", "sala_equipamento",
        "curso", "disciplina", "turma", "matricula", "horario",
        "frequencia", "previsao_falta", "sugestao_remanejamento", "log_alocacao"
    }
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


def test_academico_e_matricula_unicidade(db_session):
    """Valida fluxo acadêmico e restrição de unicidade aluno_id + turma_id."""
    campus = Campus(nome="Campus 1", cidade="C1", endereco="E1")
    db_session.add(campus)
    db_session.commit()

    aluno = Usuario(campus_id=campus.id, nome="Aluno 1", email="a1@sigaas.edu", senha_hash="h", perfil=PerfilUsuario.ALUNO)
    curso = Curso(campus_id=campus.id, nome="Engenharia", codigo="ENG01")
    db_session.add_all([aluno, curso])
    db_session.commit()

    disc = Disciplina(curso_id=curso.id, nome="Cálculo I", codigo="MAT101", carga_horaria=60)
    db_session.add(disc)
    db_session.commit()

    turma = Turma(disciplina_id=disc.id, periodo_letivo="2026.1", turno_preferido=Turno.MATUTINO)
    db_session.add(turma)
    db_session.commit()

    m1 = Matricula(aluno_id=aluno.id, turma_id=turma.id)
    db_session.add(m1)
    db_session.commit()

    # Tentativa de matrícula duplicada
    m2 = Matricula(aluno_id=aluno.id, turma_id=turma.id)
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_horario_e_check_constraint(db_session):
    """Valida modelo de horário e CheckConstraint hora_inicio < hora_fim."""
    campus = Campus(nome="Campus 1", cidade="C1", endereco="E1")
    db_session.add(campus)
    db_session.commit()

    sala = Sala(campus_id=campus.id, bloco="B", numero="201", tipo=TipoSala.REGULAR, capacidade=30, turnos_disponiveis=["matutino"])
    curso = Curso(campus_id=campus.id, nome="C1", codigo="C1")
    db_session.add_all([sala, curso])
    db_session.commit()

    disc = Disciplina(curso_id=curso.id, nome="D1", codigo="D1", carga_horaria=30)
    db_session.add(disc)
    db_session.commit()

    turma = Turma(disciplina_id=disc.id, periodo_letivo="2026.1", turno_preferido=Turno.MATUTINO)
    db_session.add(turma)
    db_session.commit()

    h_valido = Horario(
        campus_id=campus.id, turma_id=turma.id, sala_id=sala.id,
        dia_semana=1, hora_inicio=time(8, 0), hora_fim=time(10, 0)
    )
    db_session.add(h_valido)
    db_session.commit()
    assert h_valido.id is not None

    # Horário com início após fim
    h_invalido = Horario(
        campus_id=campus.id, turma_id=turma.id, sala_id=sala.id,
        dia_semana=2, hora_inicio=time(12, 0), hora_fim=time(10, 0)
    )
    db_session.add(h_invalido)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_sugestao_remanejamento_e_log_alocacao(db_session):
    """Valida status pendente padrão e log_alocacao com horario_id anulável."""
    campus = Campus(nome="Campus 1", cidade="C1", endereco="E1")
    db_session.add(campus)
    db_session.commit()

    admin = Usuario(campus_id=campus.id, nome="Admin", email="ad@sigaas.edu", senha_hash="h", perfil=PerfilUsuario.ADMIN)
    s1 = Sala(campus_id=campus.id, bloco="A", numero="1", tipo=TipoSala.REGULAR, capacidade=30, turnos_disponiveis=["matutino"])
    s2 = Sala(campus_id=campus.id, bloco="A", numero="2", tipo=TipoSala.REGULAR, capacidade=50, turnos_disponiveis=["matutino"])
    curso = Curso(campus_id=campus.id, nome="C", codigo="C")
    db_session.add_all([admin, s1, s2, curso])
    db_session.commit()

    disc = Disciplina(curso_id=curso.id, nome="D", codigo="D", carga_horaria=30)
    db_session.add(disc)
    db_session.commit()

    turma = Turma(disciplina_id=disc.id, periodo_letivo="2026.1", turno_preferido=Turno.MATUTINO)
    db_session.add(turma)
    db_session.commit()

    horario = Horario(campus_id=campus.id, turma_id=turma.id, sala_id=s1.id, dia_semana=0, hora_inicio=time(8, 0), hora_fim=time(10, 0))
    db_session.add(horario)
    db_session.commit()

    sugestao = SugestaoRemanejamento(
        horario_id=horario.id, sala_atual_id=s1.id, sala_sugerida_id=s2.id,
        motivo="Probabilidade de falta calculada em 75%",
        justificativa="Aprovado por economia de energia"
    )
    log = LogAlocacao(
        horario_id=horario.id, usuario_responsavel=admin.id,
        tipo_evento=TipoEventoLog.REMANEJAMENTO,
        snapshot_evento={"turma_id": turma.id, "sala_id": s1.id}
    )
    db_session.add_all([sugestao, log])
    db_session.commit()

    assert sugestao.status == StatusSugestao.PENDENTE
    assert sugestao.justificativa == "Aprovado por economia de energia"
    assert log.snapshot_evento["turma_id"] == turma.id
