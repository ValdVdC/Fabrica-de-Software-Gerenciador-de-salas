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
    assert resp.status_code == 201
    dados = resp.json()
    assert dados["codigo"] == "ES01"
    assert dados["campus_id"] == campus_id

    list_resp = client.get("/api/v1/cursos", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    cursos = list_resp.json()
    assert len(cursos) == 1
    assert cursos[0]["nome"] == "Engenharia de Software"


def test_criar_curso_campus_alheio_rejeitado_secretaria(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_b_id = setup_cenario["campus_b"].id
    payload = {"campus_id": campus_b_id, "nome": "Medicina", "codigo": "MED01"}
    resp = client.post("/api/v1/cursos", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_criar_curso_codigo_duplicado_conflito(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_id = setup_cenario["campus_a"].id
    payload = {"campus_id": campus_id, "nome": "Ciencia da Computacao", "codigo": "CC01"}
    resp1 = client.post("/api/v1/cursos", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/cursos", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 409


def test_criar_disciplina_sucesso_e_validacoes(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_id = setup_cenario["campus_a"].id
    c_resp = client.post("/api/v1/cursos", json={"campus_id": campus_id, "nome": "Computacao", "codigo": "CMP"}, headers={"Authorization": f"Bearer {token}"})
    curso_id = c_resp.json()["id"]

    d_payload = {"curso_id": curso_id, "nome": "Algoritmos e Estruturas", "codigo": "AED01", "carga_horaria": 60}
    d_resp = client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {token}"})
    assert d_resp.status_code == 201
    assert d_resp.json()["carga_horaria"] == 60

    invalida = {"curso_id": curso_id, "nome": "Invalida", "codigo": "INV", "carga_horaria": 0}
    err_resp = client.post("/api/v1/disciplinas", json=invalida, headers={"Authorization": f"Bearer {token}"})
    assert err_resp.status_code == 422


def test_criar_disciplina_curso_inexistente(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    d_payload = {"curso_id": 9999, "nome": "Invalida", "codigo": "INV", "carga_horaria": 60}
    resp = client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_criar_disciplina_codigo_duplicado_mesmo_curso(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_id = setup_cenario["campus_a"].id
    c_resp = client.post("/api/v1/cursos", json={"campus_id": campus_id, "nome": "Biologia", "codigo": "BIO"}, headers={"Authorization": f"Bearer {token}"})
    curso_id = c_resp.json()["id"]

    d_payload = {"curso_id": curso_id, "nome": "Genetica", "codigo": "GEN01", "carga_horaria": 60}
    resp1 = client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/disciplinas", json=d_payload, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 409


def test_rbac_aluno_e_professor_bloqueados_em_cursos_e_disciplinas(client, setup_cenario):
    aluno_token = setup_cenario["token_aluno_a"]
    prof_token = setup_cenario["token_prof_a"]
    curso_payload = {"campus_id": setup_cenario["campus_a"].id, "nome": "Tentativa", "codigo": "TNT"}

    assert client.post("/api/v1/cursos", json=curso_payload, headers={"Authorization": f"Bearer {aluno_token}"}).status_code == 403
    assert client.post("/api/v1/cursos", json=curso_payload, headers={"Authorization": f"Bearer {prof_token}"}).status_code == 403
    assert client.post("/api/v1/disciplinas", json={"curso_id": 1, "nome": "T", "codigo": "T", "carga_horaria": 30}, headers={"Authorization": f"Bearer {aluno_token}"}).status_code == 403


def test_validacao_defensiva_strings_em_branco(client, setup_cenario):
    token = setup_cenario["token_sec_a"]
    campus_id = setup_cenario["campus_a"].id

    resp = client.post("/api/v1/cursos", json={"campus_id": campus_id, "nome": "   ", "codigo": "OK"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422

    resp2 = client.post("/api/v1/cursos", json={"campus_id": campus_id, "nome": "Valido", "codigo": "   "}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 422
