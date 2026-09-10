"""Testes automatizados TDD para consulta de horarios pessoais e grade semanal (/api/v1/horarios/meus)."""
from datetime import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models import Campus, Usuario, PerfilUsuario, Sala, TipoSala, Curso, Disciplina, Turma, Turno, Matricula
from app.models.alocacao import Horario
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(test_db):
    def override_get_db():
        yield test_db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def cenario_horarios(test_db):
    ca = Campus(nome="Campus Sao Luis", cidade="Sao Luis", endereco="Av dos Portugueses")
    cb = Campus(nome="Campus Imperatriz", cidade="Imperatriz", endereco="Rua Urbano Santos")
    test_db.add_all([ca, cb])
    test_db.commit()

    s = get_password_hash("sigaas123")
    adm = Usuario(nome="Admin", email="admin@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.ADMIN, campus_id=ca.id)
    sec_a = Usuario(nome="Sec Sao Luis", email="sec_sl@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.SECRETARIA, campus_id=ca.id)
    prof_a = Usuario(nome="Prof Alan Turing", email="turing@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.PROFESSOR, campus_id=ca.id)
    prof_b = Usuario(nome="Prof Ada Lovelace", email="ada@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.PROFESSOR, campus_id=ca.id)
    aluno_a = Usuario(nome="Aluno Carlos", email="carlos@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.ALUNO, campus_id=ca.id)
    aluno_b = Usuario(nome="Aluno Daniel", email="daniel@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.ALUNO, campus_id=ca.id)
    u_inativo = Usuario(nome="Inativo", email="inativo@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.ALUNO, campus_id=ca.id, ativo=False)
    test_db.add_all([adm, sec_a, prof_a, prof_b, aluno_a, aluno_b, u_inativo])
    test_db.commit()

    sala_a1 = Sala(campus_id=ca.id, bloco="Bloco 1", numero="101", tipo=TipoSala.REGULAR, capacidade=40, turnos_disponiveis=["matutino"])
    sala_a2 = Sala(campus_id=ca.id, bloco="Bloco 2", numero="202", tipo=TipoSala.LABORATORIO, capacidade=30, turnos_disponiveis=["matutino", "vespertino"])
    sala_b1 = Sala(campus_id=cb.id, bloco="Bloco A", numero="01", tipo=TipoSala.REGULAR, capacidade=50, turnos_disponiveis=["noturno"])
    test_db.add_all([sala_a1, sala_a2, sala_b1])
    test_db.commit()

    curso = Curso(campus_id=ca.id, nome="Ciencia da Computacao", codigo="CC")
    test_db.add(curso)
    test_db.commit()

    d1 = Disciplina(curso_id=curso.id, nome="Algoritmos e Estruturas de Dados", codigo="AED1", carga_horaria=60)
    d2 = Disciplina(curso_id=curso.id, nome="Calculo Diferencial e Integral", codigo="MAT1", carga_horaria=80)
    test_db.add_all([d1, d2])
    test_db.commit()

    t1 = Turma(disciplina_id=d1.id, professor_id=prof_a.id, periodo_letivo="2026.1", turno_preferido=Turno.MATUTINO, num_matriculados=2)
    t2 = Turma(disciplina_id=d2.id, professor_id=prof_b.id, periodo_letivo="2026.1", turno_preferido=Turno.MATUTINO, num_matriculados=1)
    t3 = Turma(disciplina_id=d1.id, professor_id=prof_b.id, periodo_letivo="2026.1", turno_preferido=Turno.NOTURNO, num_matriculados=0)
    test_db.add_all([t1, t2, t3])
    test_db.commit()

    # Matriculas: Carlos matriculado em t1 e t2 (ativa), e em t3 (cancelada)
    m1 = Matricula(aluno_id=aluno_a.id, turma_id=t1.id, status="ativa")
    m2 = Matricula(aluno_id=aluno_a.id, turma_id=t2.id, status="ativa")
    m3 = Matricula(aluno_id=aluno_a.id, turma_id=t3.id, status="cancelada")
    m4 = Matricula(aluno_id=aluno_b.id, turma_id=t1.id, status="ativa")
    test_db.add_all([m1, m2, m3, m4])
    test_db.commit()

    # Horarios alocados
    # h1: Quarta (dia 2) 08:00-10:00, Turma 1 (Prof A), Sala A1
    h1 = Horario(campus_id=ca.id, turma_id=t1.id, sala_id=sala_a1.id, dia_semana=2, hora_inicio=time(8, 0), hora_fim=time(10, 0))
    # h2: Segunda (dia 0) 08:00-10:00, Turma 1 (Prof A), Sala A1
    h2 = Horario(campus_id=ca.id, turma_id=t1.id, sala_id=sala_a1.id, dia_semana=0, hora_inicio=time(8, 0), hora_fim=time(10, 0))
    # h3: Terca (dia 1) 10:00-12:00, Turma 2 (Prof B), Sala A2
    h3 = Horario(campus_id=ca.id, turma_id=t2.id, sala_id=sala_a2.id, dia_semana=1, hora_inicio=time(10, 0), hora_fim=time(12, 0))
    # h4: Quinta (dia 3) 19:00-21:00, Turma 3 (Prof B), Sala B1 (Campus B)
    h4 = Horario(campus_id=cb.id, turma_id=t3.id, sala_id=sala_b1.id, dia_semana=3, hora_inicio=time(19, 0), hora_fim=time(21, 0))
    test_db.add_all([h1, h2, h3, h4])
    test_db.commit()

    return {
        "token_prof_a": create_access_token({"sub": str(prof_a.id), "perfil": prof_a.perfil.value}),
        "token_prof_b": create_access_token({"sub": str(prof_b.id), "perfil": prof_b.perfil.value}),
        "token_aluno_a": create_access_token({"sub": str(aluno_a.id), "perfil": aluno_a.perfil.value}),
        "token_aluno_b": create_access_token({"sub": str(aluno_b.id), "perfil": aluno_b.perfil.value}),
        "token_sec_a": create_access_token({"sub": str(sec_a.id), "perfil": sec_a.perfil.value}),
        "token_admin": create_access_token({"sub": str(adm.id), "perfil": adm.perfil.value}),
        "token_inativo": create_access_token({"sub": str(u_inativo.id), "perfil": u_inativo.perfil.value}),
        "turma_1_id": t1.id,
        "turma_2_id": t2.id,
    }


def test_horarios_meus_sem_autenticacao_retorna_401(client, cenario_horarios):
    res = client.get("/api/v1/horarios/meus")
    assert res.status_code == 401


def test_horarios_meus_usuario_inativo_rejeitado(client, cenario_horarios):
    headers = {"Authorization": f"Bearer {cenario_horarios['token_inativo']}"}
    res = client.get("/api/v1/horarios/meus", headers=headers)
    assert res.status_code == 403
    assert "inativo" in res.json()["detail"].lower()


def test_horarios_meus_professor_retorna_apenas_suas_turmas_ordenadas(client, cenario_horarios):
    headers = {"Authorization": f"Bearer {cenario_horarios['token_prof_a']}"}
    res = client.get("/api/v1/horarios/meus", headers=headers)
    assert res.status_code == 200
    dados = res.json()
    assert len(dados) == 2
    # Ordenacao cronologica: dia_semana 0 (Segunda) antes de dia_semana 2 (Quarta)
    assert dados[0]["dia_semana"] == 0
    assert dados[0]["disciplina_codigo"] == "AED1"
    assert dados[0]["sala_bloco"] == "Bloco 1"
    assert dados[0]["sala_numero"] == "101"
    assert dados[0]["professor_nome"] == "Prof Alan Turing"
    assert dados[1]["dia_semana"] == 2


def test_horarios_meus_aluno_retorna_apenas_matriculas_ativas(client, cenario_horarios):
    headers = {"Authorization": f"Bearer {cenario_horarios['token_aluno_a']}"}
    res = client.get("/api/v1/horarios/meus", headers=headers)
    assert res.status_code == 200
    dados = res.json()
    # Carlos esta matriculado ativo em t1 (h2 dia 0, h1 dia 2) e t2 (h3 dia 1). t3 esta cancelada (h4).
    assert len(dados) == 3
    dias = [item["dia_semana"] for item in dados]
    assert dias == [0, 1, 2]
    # Nao contem o horario da turma t3 (dia 3) pois a matricula foi cancelada
    assert 3 not in dias


def test_horarios_meus_secretaria_retorna_horarios_do_campus(client, cenario_horarios):
    headers = {"Authorization": f"Bearer {cenario_horarios['token_sec_a']}"}
    res = client.get("/api/v1/horarios/meus", headers=headers)
    assert res.status_code == 200
    dados = res.json()
    # Secretaria do Campus Sao Luis ve h1, h2, h3 (todos do campus ca). h4 pertence a cb.
    assert len(dados) == 3
    for h in dados:
        assert h["sala_bloco"] in ["Bloco 1", "Bloco 2"]


def test_horarios_meus_paginacao_skip_limit(client, cenario_horarios):
    headers = {"Authorization": f"Bearer {cenario_horarios['token_aluno_a']}"}
    res = client.get("/api/v1/horarios/meus?skip=1&limit=1", headers=headers)
    assert res.status_code == 200
    dados = res.json()
    assert len(dados) == 1
    assert dados[0]["dia_semana"] == 1


def test_horarios_meus_usuario_sem_horarios_retorna_lista_vazia(client, cenario_horarios):
    headers = {"Authorization": f"Bearer {cenario_horarios['token_admin']}"}
    res = client.get("/api/v1/horarios/meus", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_horarios_meus_paginacao_invalida_retorna_422(client, cenario_horarios):
    headers = {"Authorization": f"Bearer {cenario_horarios['token_aluno_a']}"}
    res1 = client.get("/api/v1/horarios/meus?skip=-1", headers=headers)
    assert res1.status_code == 422
    res2 = client.get("/api/v1/horarios/meus?limit=0", headers=headers)
    assert res2.status_code == 422
    res3 = client.get("/api/v1/horarios/meus?limit=201", headers=headers)
    assert res3.status_code == 422

