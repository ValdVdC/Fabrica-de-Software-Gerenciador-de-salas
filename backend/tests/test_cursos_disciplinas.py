"""Testes automatizados TDD para gestao de cursos e disciplinas com isolamento multi-campus."""
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
    aluno_a = Usuario(nome="Aluno A", email="aluno_a@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO, campus_id=campus_a.id)
    test_db.add_all([admin, sec_a, prof_a, aluno_a])
    test_db.commit()

    return {
        "campus_a": campus_a,
        "campus_b": campus_b,
        "token_admin": create_access_token({"sub": str(admin.id), "perfil": admin.perfil.value}),
        "token_sec_a": create_access_token({"sub": str(sec_a.id), "perfil": sec_a.perfil.value}),
        "token_prof_a": create_access_token({"sub": str(prof_a.id), "perfil": prof_a.perfil.value}),
        "token_aluno_a": create_access_token({"sub": str(aluno_a.id), "perfil": aluno_a.perfil.value}),
    }


def test_criar_e_listar_curso_secretaria(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_id = setup_cenario["campus_a"].id
    payload = {"campus_id": campus_id, "nome": "Engenharia de Software", "codigo": "ES01"}
    resp = client.post("/api/v1/cursos", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201 and resp.json()["codigo"] == "ES01"

    list_resp = client.get("/api/v1/cursos?skip=0&limit=10", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200 and len(list_resp.json()) == 1
    assert client.get("/api/v1/cursos?skip=1&limit=10", headers={"Authorization": f"Bearer {token}"}).json() == []

    adm_token = setup_cenario["token_admin"]
    assert len(client.get(f"/api/v1/cursos?campus_id={campus_id}", headers={"Authorization": f"Bearer {adm_token}"}).json()) == 1


def test_criar_curso_campus_alheio_rejeitado_secretaria(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    payload = {"campus_id": setup_cenario["campus_b"].id, "nome": "Medicina", "codigo": "MED01"}
    assert client.post("/api/v1/cursos", json=payload, headers={"Authorization": f"Bearer {token}"}).status_code == 403


def test_criar_curso_codigo_duplicado_conflito(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_id = setup_cenario["campus_a"].id
    payload = {"campus_id": campus_id, "nome": "Ciencia da Computacao", "codigo": "CC01"}
    assert client.post("/api/v1/cursos", json=payload, headers={"Authorization": f"Bearer {token}"}).status_code == 201
    assert client.post("/api/v1/cursos", json={**payload, "codigo": "cc01"}, headers={"Authorization": f"Bearer {token}"}).status_code == 409


def test_criar_disciplina_sucesso_e_validacoes(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_id = setup_cenario["campus_a"].id
    c_resp = client.post("/api/v1/cursos", json={"campus_id": campus_id, "nome": "Computacao", "codigo": "CMP"}, headers={"Authorization": f"Bearer {token}"})
    curso_id = c_resp.json()["id"]

    d_payload = {"curso_id": curso_id, "nome": "Algoritmos e Estruturas", "codigo": "AED01", "carga_horaria": 60}
    d_resp = client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {token}"})
    assert d_resp.status_code == 201 and d_resp.json()["carga_horaria"] == 60

    for ch in [0, -10, 1001]:
        assert client.post("/api/v1/disciplinas", json={**d_payload, "carga_horaria": ch}, headers={"Authorization": f"Bearer {token}"}).status_code == 422

    list_resp = client.get(f"/api/v1/disciplinas?skip=0&limit=10&curso_id={curso_id}", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200 and len(list_resp.json()) == 1
    adm_token = setup_cenario["token_admin"]
    assert len(client.get(f"/api/v1/disciplinas?campus_id={campus_id}", headers={"Authorization": f"Bearer {adm_token}"}).json()) == 1


def test_criar_disciplina_curso_inexistente(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    d_payload = {"curso_id": 9999, "nome": "Invalida", "codigo": "INV", "carga_horaria": 60}
    assert client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {token}"}).status_code == 404

    c_b = client.post("/api/v1/cursos", json={"campus_id": setup_cenario["campus_b"].id, "nome": "Direito", "codigo": "DIR"}, headers={"Authorization": f"Bearer {setup_cenario['token_admin']}"}).json()["id"]
    assert client.post("/api/v1/disciplinas", json={**d_payload, "curso_id": c_b}, headers={"Authorization": f"Bearer {token}"}).status_code == 404


def test_criar_disciplina_codigo_duplicado_mesmo_curso(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_id = setup_cenario["campus_a"].id
    c_resp = client.post("/api/v1/cursos", json={"campus_id": campus_id, "nome": "Biologia", "codigo": "BIO"}, headers={"Authorization": f"Bearer {token}"})
    curso_id = c_resp.json()["id"]

    d_payload = {"curso_id": curso_id, "nome": "Genetica", "codigo": "GEN01", "carga_horaria": 60}
    assert client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {token}"}).status_code == 201
    assert client.post("/api/v1/disciplinas", json={**d_payload, "codigo": "gen01"}, headers={"Authorization": f"Bearer {token}"}).status_code == 409


def test_rbac_aluno_e_professor_bloqueados_em_cursos_e_disciplinas(client, setup_cenario):
    aluno_token = setup_cenario["token_aluno_a"]
    prof_token = setup_cenario["token_prof_a"]
    curso_payload = {"campus_id": setup_cenario["campus_a"].id, "nome": "Tentativa", "codigo": "TNT"}
    d_payload = {"curso_id": 1, "nome": "Tent", "codigo": "TNT01", "carga_horaria": 30}

    assert client.post("/api/v1/cursos", json=curso_payload, headers={"Authorization": f"Bearer {aluno_token}"}).status_code == 403
    assert client.post("/api/v1/cursos", json=curso_payload, headers={"Authorization": f"Bearer {prof_token}"}).status_code == 403
    assert client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {aluno_token}"}).status_code == 403
    assert client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {prof_token}"}).status_code == 403


def test_validacao_defensiva_strings_em_branco(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_id = setup_cenario["campus_a"].id

    for payload in [
        {"campus_id": campus_id, "nome": "   ", "codigo": "OK"},
        {"campus_id": campus_id, "nome": "Valido", "codigo": "   "},
        {"campus_id": campus_id, "nome": " A ", "codigo": "OK"},
        {"campus_id": campus_id, "nome": "Valido", "codigo": " B "},
        {"campus_id": campus_id, "nome": "Valido", "codigo": "OK", "campo_extra": "proibido"},
    ]:
        assert client.post("/api/v1/cursos", json=payload, headers={"Authorization": f"Bearer {token}"}).status_code == 422

    for d_payload in [
        {"curso_id": 1, "nome": "   ", "codigo": "OK", "carga_horaria": 30},
        {"curso_id": 1, "nome": "OK", "codigo": "   ", "carga_horaria": 30},
        {"curso_id": 1, "nome": " A ", "codigo": "OK", "carga_horaria": 30},
        {"curso_id": 1, "nome": "OK", "codigo": " B ", "carga_horaria": 30},
    ]:
        assert client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {token}"}).status_code == 422
