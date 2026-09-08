"""Testes automatizados para autenticacao JWT, hash de senhas e RBAC."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models import Campus, Usuario, PerfilUsuario
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)


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
def usuario_teste(test_db):
    campus = Campus(nome="Campus Teste", cidade="Teresina", endereco="Av Central")
    test_db.add(campus)
    test_db.commit()

    senha_hash = get_password_hash("sigaas123")
    user = Usuario(
        campus_id=campus.id,
        nome="Admin Teste",
        email="admin@sigaas.edu",
        senha_hash=senha_hash,
        perfil=PerfilUsuario.ADMIN,
        ativo=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def test_password_hashing_and_verification():
    raw_pass = "segredo123"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("senha_errada", hashed) is False


def test_token_creation_and_decoding():
    token = create_access_token(data={"sub": "1", "perfil": "admin", "campus_id": 1})
    payload = decode_access_token(token)
    assert payload.get("sub") == "1"
    assert payload.get("perfil") == "admin"
    assert payload.get("campus_id") == 1
    assert "exp" in payload


def test_login_sucesso(client, usuario_teste):
    payload = {"email": "admin@sigaas.edu", "senha": "sigaas123"}
    res = client.post("/api/v1/auth/login", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["usuario"]["email"] == "admin@sigaas.edu"
    assert data["usuario"]["perfil"] == "admin"


def test_login_senha_incorreta(client, usuario_teste):
    payload = {"email": "admin@sigaas.edu", "senha": "senha_errada"}
    res = client.post("/api/v1/auth/login", json=payload)
    assert res.status_code == 401
    assert "Credenciais invalidas" in res.json()["detail"]


def test_login_usuario_inexistente(client, test_db):
    payload = {"email": "naoexiste@sigaas.edu", "senha": "sigaas123"}
    res = client.post("/api/v1/auth/login", json=payload)
    assert res.status_code == 401
    assert "Credenciais invalidas" in res.json()["detail"]


def test_auth_me_com_token_valido(client, usuario_teste):
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@sigaas.edu", "senha": "sigaas123"})
    token = login_res.json()["access_token"]

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == usuario_teste.id
    assert data["email"] == "admin@sigaas.edu"
    assert data["perfil"] == "admin"


def test_auth_me_sem_token_retorna_401(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
