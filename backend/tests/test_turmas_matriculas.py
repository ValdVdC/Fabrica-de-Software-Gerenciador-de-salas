"""Testes automatizados TDD para gestao de turmas e matriculas com integridade e isolamento multi-campus."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models import Campus, Usuario, PerfilUsuario
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
def setup_cenario(test_db):
    campus_a = Campus(nome="Campus Sao Luis", cidade="Sao Luis", endereco="Av dos Portugueses")
    campus_b = Campus(nome="Campus Imperatriz", cidade="Imperatriz", endereco="Rua Urbano Santos")
    test_db.add_all([campus_a, campus_b])
    test_db.commit()

    senha = get_password_hash("sigaas123")
    admin = Usuario(nome="Admin", email="admin@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ADMIN, campus_id=campus_a.id)
    sec_a = Usuario(nome="Sec A", email="sec_a@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.SECRETARIA, campus_id=campus_a.id)
    prof_a = Usuario(nome="Prof A", email="prof_a@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR, campus_id=campus_a.id)
    prof_b = Usuario(nome="Prof B", email="prof_b@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR, campus_id=campus_b.id)
    aluno_a = Usuario(nome="Aluno A", email="aluno_a@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO, campus_id=campus_a.id)
    aluno_b = Usuario(nome="Aluno B", email="aluno_b@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO, campus_id=campus_b.id)
    test_db.add_all([admin, sec_a, prof_a, prof_b, aluno_a, aluno_b])
    test_db.commit()

    return {
        "campus_a": campus_a,
        "campus_b": campus_b,
        "admin": admin,
        "sec_a": sec_a,
        "prof_a": prof_a,
        "prof_b": prof_b,
        "aluno_a": aluno_a,
        "aluno_b": aluno_b,
        "token_admin": create_access_token({"sub": str(admin.id), "perfil": admin.perfil.value}),
        "token_sec_a": create_access_token({"sub": str(sec_a.id), "perfil": sec_a.perfil.value}),
        "token_prof_a": create_access_token({"sub": str(prof_a.id), "perfil": prof_a.perfil.value}),
        "token_aluno_a": create_access_token({"sub": str(aluno_a.id), "perfil": aluno_a.perfil.value}),
    }


def _criar_curso_e_disciplina(client, token, campus_id, codigo_curso="CC", codigo_disc="POO"):
    c_resp = client.post("/api/v1/cursos", json={"campus_id": campus_id, "nome": f"Curso {codigo_curso}", "codigo": codigo_curso}, headers={"Authorization": f"Bearer {token}"})
    curso_id = c_resp.json()["id"]
    d_resp = client.post("/api/v1/disciplinas", json={"curso_id": curso_id, "nome": f"Disciplina {codigo_disc}", "codigo": codigo_disc, "carga_horaria": 60}, headers={"Authorization": f"Bearer {token}"})
    return curso_id, d_resp.json()["id"]


def test_criar_turma_sucesso_inicializacao_matriculados(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_a_id = setup_cenario["campus_a"].id
    _, disc_id = _criar_curso_e_disciplina(client, token, campus_a_id, "CC01", "POO01")

    payload = {
        "disciplina_id": disc_id,
        "professor_id": setup_cenario["prof_a"].id,
        "periodo_letivo": "2026.1",
        "turno_preferido": "matutino",
    }
    resp = client.post("/api/v1/turmas", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    dados = resp.json()
    assert dados["num_matriculados"] == 0
    assert dados["periodo_letivo"] == "2026.1"
    assert dados["disciplina_id"] == disc_id


def test_criar_turma_disciplina_campus_alheio_rejeitado(client, setup_cenario):
    token_admin = setup_cenario["token_admin"]
    token_sec_a = setup_cenario["token_sec_a"]
    campus_b_id = setup_cenario["campus_b"].id
    _, disc_b_id = _criar_curso_e_disciplina(client, token_admin, campus_b_id, "MED", "ANAT")

    payload = {
        "disciplina_id": disc_b_id,
        "periodo_letivo": "2026.1",
        "turno_preferido": "vespertino",
    }
    resp = client.post("/api/v1/turmas", json=payload, headers={"Authorization": f"Bearer {token_sec_a}"})
    assert resp.status_code == 404


def test_criar_turma_professor_invalido_ou_campus_alheio(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_a_id = setup_cenario["campus_a"].id
    _, disc_id = _criar_curso_e_disciplina(client, token, campus_a_id, "ENG", "FIS1")

    resp_aluno = client.post("/api/v1/turmas", json={"disciplina_id": disc_id, "professor_id": setup_cenario["aluno_a"].id, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {token}"})
    assert resp_aluno.status_code == 400

    resp_prof_b = client.post("/api/v1/turmas", json={"disciplina_id": disc_id, "professor_id": setup_cenario["prof_b"].id, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {token}"})
    assert resp_prof_b.status_code == 404


def test_matricular_aluno_incremento_contagem_e_duplicidade(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_a_id = setup_cenario["campus_a"].id
    _, disc_id = _criar_curso_e_disciplina(client, token, campus_a_id, "MAT", "CALC1")

    t_resp = client.post("/api/v1/turmas", json={"disciplina_id": disc_id, "periodo_letivo": "2026.1", "turno_preferido": "noturno"}, headers={"Authorization": f"Bearer {token}"})
    turma_id = t_resp.json()["id"]

    matr_payload = {"aluno_id": setup_cenario["aluno_a"].id, "turma_id": turma_id}
    m_resp = client.post("/api/v1/matriculas", json=matr_payload, headers={"Authorization": f"Bearer {token}"})
    assert m_resp.status_code == 201
    assert m_resp.json()["status"] == "ativa"

    t_check = client.get(f"/api/v1/turmas/{turma_id}", headers={"Authorization": f"Bearer {token}"})
    assert t_check.status_code == 200
    assert t_check.json()["num_matriculados"] == 1

    dup_resp = client.post("/api/v1/matriculas", json=matr_payload, headers={"Authorization": f"Bearer {token}"})
    assert dup_resp.status_code == 409

    t_check_after = client.get(f"/api/v1/turmas/{turma_id}", headers={"Authorization": f"Bearer {token}"})
    assert t_check_after.json()["num_matriculados"] == 1


def test_matricular_aluno_campus_alheio_rejeitado(client, setup_cenario):
    token_sec_a = setup_cenario["token_sec_a"]
    token_admin = setup_cenario["token_admin"]
    campus_a_id = setup_cenario["campus_a"].id
    _, disc_id = _criar_curso_e_disciplina(client, token_sec_a, campus_a_id, "DIR", "DCONST")

    t_resp = client.post("/api/v1/turmas", json={"disciplina_id": disc_id, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {token_sec_a}"})
    turma_id = t_resp.json()["id"]

    resp_sec = client.post("/api/v1/matriculas", json={"aluno_id": setup_cenario["aluno_b"].id, "turma_id": turma_id}, headers={"Authorization": f"Bearer {token_sec_a}"})
    assert resp_sec.status_code == 404

    resp_admin = client.post("/api/v1/matriculas", json={"aluno_id": setup_cenario["aluno_b"].id, "turma_id": turma_id}, headers={"Authorization": f"Bearer {token_admin}"})
    assert resp_admin.status_code == 400


def test_listar_turmas_e_matriculas_paginacao_e_filtros(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_a_id = setup_cenario["campus_a"].id
    _, disc_id = _criar_curso_e_disciplina(client, token, campus_a_id, "HIS", "HIST1")

    client.post("/api/v1/turmas", json={"disciplina_id": disc_id, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/api/v1/turmas", json={"disciplina_id": disc_id, "periodo_letivo": "2026.2", "turno_preferido": "noturno"}, headers={"Authorization": f"Bearer {token}"})

    list_turmas = client.get("/api/v1/turmas?skip=0&limit=10", headers={"Authorization": f"Bearer {token}"})
    assert list_turmas.status_code == 200
    turmas = list_turmas.json()
    assert len(turmas) >= 2

    turma_id = turmas[0]["id"]
    client.post("/api/v1/matriculas", json={"aluno_id": setup_cenario["aluno_a"].id, "turma_id": turma_id}, headers={"Authorization": f"Bearer {token}"})

    list_matr = client.get(f"/api/v1/matriculas?turma_id={turma_id}", headers={"Authorization": f"Bearer {token}"})
    assert list_matr.status_code == 200
    assert len(list_matr.json()) == 1


def test_rbac_aluno_e_professor_bloqueados_em_turmas_e_matriculas(client, setup_cenario):
    aluno_token = setup_cenario["token_aluno_a"]
    prof_token = setup_cenario["token_prof_a"]
    t_payload = {"disciplina_id": 1, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}
    m_payload = {"aluno_id": 1, "turma_id": 1}

    assert client.post("/api/v1/turmas", json=t_payload, headers={"Authorization": f"Bearer {aluno_token}"}).status_code == 403
    assert client.post("/api/v1/turmas", json=t_payload, headers={"Authorization": f"Bearer {prof_token}"}).status_code == 403
    assert client.post("/api/v1/matriculas", json=m_payload, headers={"Authorization": f"Bearer {aluno_token}"}).status_code == 403
    assert client.post("/api/v1/matriculas", json=m_payload, headers={"Authorization": f"Bearer {prof_token}"}).status_code == 403


def test_validacoes_defensivas_turma_e_matricula(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_a_id = setup_cenario["campus_a"].id
    _, disc_id = _criar_curso_e_disciplina(client, token, campus_a_id, "LET", "PORT1")

    resp1 = client.post("/api/v1/turmas", json={"disciplina_id": disc_id, "periodo_letivo": "   ", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == 422

    resp2 = client.post("/api/v1/turmas", json={"disciplina_id": disc_id, "periodo_letivo": "20", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 422

    resp3 = client.post("/api/v1/turmas", json={"disciplina_id": disc_id, "periodo_letivo": "2026.1", "turno_preferido": "matutino", "campo_extra": "hack"}, headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 422

    resp4 = client.post("/api/v1/matriculas", json={"aluno_id": 1, "turma_id": 1, "campo_extra": "hack"}, headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 422
