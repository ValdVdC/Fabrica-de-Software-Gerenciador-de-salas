"""
Testes unitarios para modelos academicos, alocacao de horarios e IA.
"""

from datetime import date, time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, StatementError

from app.db.session import Base
from app.models import (
    Campus, Usuario, Sala, PerfilUsuario, TipoSala,
    Curso, Disciplina, Turma, Matricula,
    Horario, LogAlocacao, Frequencia, PrevisaoFalta, SugestaoRemanejamento,
    Turno, StatusSugestao, TipoEventoLog
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def base_fixtures(db_session):
    c = Campus(nome="Campus 1", cidade="C1", endereco="E1")
    p = Usuario(campus=c, nome="P1", email="p1@sigaas.edu", senha_hash="h", perfil=PerfilUsuario.PROFESSOR)
    a = Usuario(campus=c, nome="A1", email="a1@sigaas.edu", senha_hash="h", perfil=PerfilUsuario.ALUNO)
    s1 = Sala(campus=c, bloco="A", numero="101", tipo=TipoSala.REGULAR, capacidade=40, turnos_disponiveis=["matutino"])
    s2 = Sala(campus=c, bloco="A", numero="102", tipo=TipoSala.REGULAR, capacidade=40, turnos_disponiveis=["matutino"])
    db_session.add_all([c, p, a, s1, s2])
    db_session.commit()
    return {"campus": c, "prof": p, "aluno": a, "sala1": s1, "sala2": s2}


def test_create_all_academic_and_ia_tables(db_session):
    expected = {
        "campus", "usuario", "equipamento", "sala", "sala_equipamento",
        "curso", "disciplina", "turma", "matricula",
        "horario", "log_alocacao", "frequencia", "previsao_falta", "sugestao_remanejamento"
    }
    assert expected.issubset(set(Base.metadata.tables.keys()))


def test_academic_flow_and_constraints(db_session, base_fixtures):
    campus, prof, aluno = base_fixtures["campus"], base_fixtures["prof"], base_fixtures["aluno"]
    curso = Curso(campus_id=campus.id, nome="Eng Soft", codigo="ES-01")
    db_session.add(curso)
    db_session.commit()

    disc = Disciplina(curso_id=curso.id, nome="Algo", codigo="ALG-1", carga_horaria=60)
    turma = Turma(disciplina=disc, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=1, turno_preferido=Turno.MATUTINO)
    mat = Matricula(aluno_id=aluno.id, turma=turma)
    db_session.add_all([disc, turma, mat])
    db_session.commit()
    assert mat.id is not None and mat.status == "ativa"

    # Restricao de unicidade aluno x turma
    db_session.add(Matricula(aluno_id=aluno.id, turma_id=turma.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_horario_and_log_alocacao(db_session, base_fixtures):
    campus, prof, sala1 = base_fixtures["campus"], base_fixtures["prof"], base_fixtures["sala1"]
    curso = Curso(campus_id=campus.id, nome="CC", codigo="CC-01")
    disc = Disciplina(curso=curso, nome="BD", codigo="BD-1", carga_horaria=60)
    turma = Turma(disciplina=disc, professor_id=prof.id, periodo_letivo="2026.1", turno_preferido=Turno.NOTURNO)
    horario = Horario(campus_id=campus.id, turma=turma, sala_id=sala1.id, dia_semana=1, hora_inicio=time(8, 0), hora_fim=time(10, 0))
    log = LogAlocacao(horario=horario, tipo_evento=TipoEventoLog.CRIACAO, usuario_responsavel=prof.id, detalhes="Inicial")
    db_session.add_all([curso, disc, turma, horario, log])
    db_session.commit()
    assert horario.id is not None and log.id is not None

    # Check constraint hora_inicio < hora_fim
    db_session.add(Horario(campus_id=campus.id, turma=turma, sala_id=sala1.id, dia_semana=1, hora_inicio=time(10, 0), hora_fim=time(8, 0)))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_ia_models_and_sugestao_round_trip(db_session, base_fixtures):
    campus, prof, aluno, s1, s2 = base_fixtures["campus"], base_fixtures["prof"], base_fixtures["aluno"], base_fixtures["sala1"], base_fixtures["sala2"]
    curso = Curso(campus_id=campus.id, nome="Mat", codigo="MAT-01")
    disc = Disciplina(curso=curso, nome="Calc", codigo="CALC-1", carga_horaria=80)
    turma = Turma(disciplina=disc, professor_id=prof.id, periodo_letivo="2026.1", turno_preferido=Turno.MATUTINO)
    mat = Matricula(aluno_id=aluno.id, turma=turma)
    horario = Horario(campus_id=campus.id, turma=turma, sala_id=s1.id, dia_semana=2, hora_inicio=time(14, 0), hora_fim=time(16, 0))
    freq = Frequencia(matricula=mat, horario=horario, data=date(2026, 3, 10), presente=True)
    prev = PrevisaoFalta(turma=turma, horario=horario, data_prevista=date(2026, 3, 17), prob_ausencia=0.75, versao_modelo="v1")
    sug = SugestaoRemanejamento(horario=horario, sala_atual_id=s1.id, sala_sugerida_id=s2.id, motivo="Superlotacao", status=StatusSugestao.PENDENTE)
    db_session.add_all([curso, disc, turma, mat, horario, freq, prev, sug])
    db_session.commit()

    hid, s1_id, s2_id, sug_id = horario.id, s1.id, s2.id, sug.id
    db_session.expunge_all()

    loaded_sug = db_session.get(SugestaoRemanejamento, sug_id)
    assert loaded_sug.status == StatusSugestao.PENDENTE
    assert isinstance(loaded_sug.status, StatusSugestao)

    # Rejeicao de valor invalido de enum
    db_session.add(SugestaoRemanejamento(horario_id=hid, sala_atual_id=s1_id, sala_sugerida_id=s2_id, motivo="Inv", status="invalido"))
    with pytest.raises((StatementError, LookupError, IntegrityError, ValueError)):
        db_session.commit()
    db_session.rollback()
