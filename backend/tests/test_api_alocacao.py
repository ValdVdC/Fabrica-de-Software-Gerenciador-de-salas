"""
Testes automatizados TDD para endpoints de alocacao inteligente (Sprint 05).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.session import Base, get_db
from app.main import app as fastapi_app
from app.models import (
    Campus,
    Curso,
    Disciplina,
    Horario,
    LogAlocacao,
    PerfilUsuario,
    Sala,
    TipoEventoLog,
    TipoSala,
    Turma,
    Turno,
    Usuario,
)


@pytest.fixture
def test_db():
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
def client(test_db):
    def override_get_db():
        yield test_db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def setup_cenario(test_db):
    campus = Campus(nome="Campus Central", cidade="Petrolina", endereco="Av. Integracao")
    test_db.add(campus)
    test_db.commit()

    senha = get_password_hash("sigaas123")
    admin = Usuario(nome="Admin Sigaas", email="admin@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ADMIN, campus_id=campus.id)
    coord = Usuario(nome="Coordenador", email="coord@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR, campus_id=campus.id)
    prof = Usuario(nome="Professor", email="prof@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR, campus_id=campus.id)
    aluno = Usuario(nome="Aluno", email="aluno@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO, campus_id=campus.id)
    test_db.add_all([admin, coord, prof, aluno])
    test_db.commit()

    curso = Curso(campus_id=campus.id, nome="Engenharia de Computacao", codigo="ENGCOMP")
    test_db.add(curso)
    test_db.commit()

    disc1 = Disciplina(curso_id=curso.id, nome="Algoritmos e Estruturas de Dados", codigo="CC101", carga_horaria=60)
    disc2 = Disciplina(curso_id=curso.id, nome="Laboratorio de Circuitos", codigo="LAB201", carga_horaria=60)
    disc3 = Disciplina(curso_id=curso.id, nome="Banco de Dados I", codigo="BD301", carga_horaria=60)
    test_db.add_all([disc1, disc2, disc3])
    test_db.commit()

    turma1 = Turma(disciplina_id=disc1.id, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=35, turno_preferido=Turno.MATUTINO)
    turma2 = Turma(disciplina_id=disc2.id, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=25, turno_preferido=Turno.MATUTINO)
    turma3 = Turma(disciplina_id=disc3.id, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=40, turno_preferido=Turno.VESPERTINO)
    test_db.add_all([turma1, turma2, turma3])
    test_db.commit()

    sala1 = Sala(campus_id=campus.id, bloco="Bloco A", numero="101", tipo=TipoSala.REGULAR, capacidade=45, turnos_disponiveis=["matutino", "vespertino"])
    sala2 = Sala(campus_id=campus.id, bloco="Bloco Lab", numero="Lab 01", tipo=TipoSala.LABORATORIO, capacidade=30, turnos_disponiveis=["matutino", "vespertino"])
    sala3 = Sala(campus_id=campus.id, bloco="Bloco B", numero="201", tipo=TipoSala.REGULAR, capacidade=60, turnos_disponiveis=["matutino", "vespertino"])
    test_db.add_all([sala1, sala2, sala3])
    test_db.commit()

    return {
        "campus": campus,
        "token_admin": create_access_token({"sub": str(admin.id), "perfil": admin.perfil.value}),
        "token_coord": create_access_token({"sub": str(coord.id), "perfil": coord.perfil.value}),
        "token_prof": create_access_token({"sub": str(prof.id), "perfil": prof.perfil.value}),
        "token_aluno": create_access_token({"sub": str(aluno.id), "perfil": aluno.perfil.value}),
        "turmas": [turma1, turma2, turma3],
        "salas": [sala1, sala2, sala3],
    }


def test_endpoint_otimizar_sucesso(client, test_db, setup_cenario):
    token = setup_cenario["token_admin"]
    campus_id = setup_cenario["campus"].id

    payload = {
        "periodo_letivo": "2026.1",
        "campus_id": campus_id,
        "max_threads": 4,
        "salvar_no_banco": True,
    }

    resp = client.post(
        "/api/v1/alocacao/otimizar",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["sucesso"] is True
    assert "Alocacao executada" in data["mensagem"]
    assert "metricas" in data
    assert data["metricas"]["threads"] == 4
    assert data["metricas"]["total_turmas"] == 3
    assert data["metricas"]["alocadas"] == 3
    assert data["metricas"]["conflitos"] == 0
    assert len(data["alocacoes"]) == 3

    # Verificar persistencia no banco de dados
    horarios_salvos = test_db.scalars(select(Horario).where(Horario.campus_id == campus_id)).all()
    assert len(horarios_salvos) == 3

    # Verificar registro de auditoria na tabela log_alocacao
    logs = test_db.scalars(select(LogAlocacao)).all()
    assert len(logs) >= 1
    assert logs[0].tipo_evento == TipoEventoLog.CRIACAO
    assert "Alocacao inteligente OpenMP" in logs[0].detalhes


def test_endpoint_otimizar_permissao(client, setup_cenario):
    # Aluno tentando acionar otimizacao
    token_aluno = setup_cenario["token_aluno"]
    payload = {
        "periodo_letivo": "2026.1",
        "campus_id": setup_cenario["campus"].id,
        "max_threads": 4,
        "salvar_no_banco": False,
    }

    resp = client.post(
        "/api/v1/alocacao/otimizar",
        json=payload,
        headers={"Authorization": f"Bearer {token_aluno}"},
    )
    assert resp.status_code == 403

    # Professor tentando acionar otimizacao
    token_prof = setup_cenario["token_prof"]
    resp_prof = client.post(
        "/api/v1/alocacao/otimizar",
        json=payload,
        headers={"Authorization": f"Bearer {token_prof}"},
    )
    assert resp_prof.status_code == 403


def test_endpoint_otimizar_sem_turmas(client, setup_cenario):
    token = setup_cenario["token_coord"]
    campus_id = setup_cenario["campus"].id

    payload = {
        "periodo_letivo": "2099.2",  # Periodo sem turmas
        "campus_id": campus_id,
        "max_threads": 2,
        "salvar_no_banco": False,
    }

    resp = client.post(
        "/api/v1/alocacao/otimizar",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["metricas"]["total_turmas"] == 0
    assert data["metricas"]["alocadas"] == 0


def test_endpoint_benchmark(client, setup_cenario):
    token = setup_cenario["token_admin"]

    payload = {
        "cenario": "medio",
        "threads": 4,
    }

    resp = client.post(
        "/api/v1/alocacao/benchmark",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cenario"] == "medio"
    assert data["num_turmas"] == 100
    assert data["num_salas"] == 40
    assert data["metricas"]["threads"] == 4
    assert data["metricas"]["speedup"] >= 1.0
    assert data["metricas"]["eficiencia_pct"] > 0
