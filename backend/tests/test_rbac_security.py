"""
Testes automatizados TDD para validacao de RBAC, prevencao de BFLA e BOLA/IDOR.
Cobre requisitos da Historia 1 da Sprint 08 (docs/specs/sprint8-rbac-multicampus.md).
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models import Campus, Usuario, PerfilUsuario
from app.core.security import get_password_hash, create_access_token
from app.api.deps import require_campus_access


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
def cenario_rbac(test_db):
    c1 = Campus(nome="Campus Teresina", cidade="Teresina", endereco="Av Frei Serafim")
    c2 = Campus(nome="Campus Parnaiba", cidade="Parnaiba", endereco="Av Sao Sebastiao")
    test_db.add_all([c1, c2])
    test_db.commit()

    senha_comum = get_password_hash("senha_teste_123")
    admin = Usuario(
        nome="Admin Geral",
        email="admin.rbac@sigaas.edu",
        senha_hash=senha_comum,
        perfil=PerfilUsuario.ADMIN,
        campus_id=c1.id,
    )
    coord1 = Usuario(
        nome="Coordenador C1",
        email="coord1.rbac@sigaas.edu",
        senha_hash=senha_comum,
        perfil=PerfilUsuario.COORDENADOR,
        campus_id=c1.id,
    )
    coord2 = Usuario(
        nome="Coordenador C2",
        email="coord2.rbac@sigaas.edu",
        senha_hash=senha_comum,
        perfil=PerfilUsuario.COORDENADOR,
        campus_id=c2.id,
    )
    sec1 = Usuario(
        nome="Secretaria C1",
        email="sec1.rbac@sigaas.edu",
        senha_hash=senha_comum,
        perfil=PerfilUsuario.SECRETARIA,
        campus_id=c1.id,
    )
    prof1 = Usuario(
        nome="Professor C1",
        email="prof1.rbac@sigaas.edu",
        senha_hash=senha_comum,
        perfil=PerfilUsuario.PROFESSOR,
        campus_id=c1.id,
    )
    aluno1 = Usuario(
        nome="Aluno C1",
        email="aluno1.rbac@sigaas.edu",
        senha_hash=senha_comum,
        perfil=PerfilUsuario.ALUNO,
        campus_id=c1.id,
    )

    test_db.add_all([admin, coord1, coord2, sec1, prof1, aluno1])
    test_db.commit()

    return {
        "c1": c1,
        "c2": c2,
        "admin": admin,
        "coord1": coord1,
        "coord2": coord2,
        "sec1": sec1,
        "prof1": prof1,
        "aluno1": aluno1,
        "headers_admin": {"Authorization": f"Bearer {create_access_token({'sub': str(admin.id), 'perfil': admin.perfil.value})}"},
        "headers_coord1": {"Authorization": f"Bearer {create_access_token({'sub': str(coord1.id), 'perfil': coord1.perfil.value})}"},
        "headers_sec1": {"Authorization": f"Bearer {create_access_token({'sub': str(sec1.id), 'perfil': sec1.perfil.value})}"},
        "headers_prof1": {"Authorization": f"Bearer {create_access_token({'sub': str(prof1.id), 'perfil': prof1.perfil.value})}"},
        "headers_aluno1": {"Authorization": f"Bearer {create_access_token({'sub': str(aluno1.id), 'perfil': aluno1.perfil.value})}"},
    }


# ==============================================================================
# 1. Testes Unitarios da Funcao Utilitaria require_campus_access
# ==============================================================================

def test_require_campus_access_admin_autoriza_qualquer_campus(cenario_rbac):
    admin = cenario_rbac["admin"]
    c1 = cenario_rbac["c1"]
    c2 = cenario_rbac["c2"]

    # Admin acessando proprio campus
    require_campus_access(c1.id, admin)
    # Admin acessando outro campus
    require_campus_access(c2.id, admin)
    # Admin acessando recurso sem campus ou id arbitrario
    require_campus_access(None, admin)
    require_campus_access(9999, admin)


def test_require_campus_access_mesmo_campus_autoriza(cenario_rbac):
    c1 = cenario_rbac["c1"]
    for role_key in ["coord1", "sec1", "prof1", "aluno1"]:
        user = cenario_rbac[role_key]
        require_campus_access(c1.id, user)


def test_require_campus_access_outro_campus_retorna_404(cenario_rbac):
    c2 = cenario_rbac["c2"]
    for role_key in ["coord1", "sec1", "prof1", "aluno1"]:
        user = cenario_rbac[role_key]
        with pytest.raises(HTTPException) as exc_info:
            require_campus_access(c2.id, user)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Recurso nao encontrado"


def test_require_campus_access_campus_nulo_ou_invalido_retorna_404(cenario_rbac):
    user = cenario_rbac["coord1"]
    # resource_campus_id nulo
    with pytest.raises(HTTPException) as exc_info:
        require_campus_access(None, user)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Recurso nao encontrado"

    # resource_campus_id booleano (prevencao de True == 1)
    with pytest.raises(HTTPException) as exc_info:
        require_campus_access(True, user)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Recurso nao encontrado"

    # resource_campus_id nao inteiro ou menor ou igual a zero
    for invalido in [0, -1, "1"]:
        with pytest.raises(HTTPException) as exc_info:
            require_campus_access(invalido, user)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Recurso nao encontrado"


def test_require_campus_access_usuario_sem_campus_gera_404(cenario_rbac):
    usuario_desacoplado = Usuario(
        nome="Usuario Sem Campus",
        email="sem.campus@sigaas.edu",
        senha_hash="hash",
        perfil=PerfilUsuario.COORDENADOR,
        campus_id=None,
    )
    with pytest.raises(HTTPException) as exc_info:
        require_campus_access(None, usuario_desacoplado)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Recurso nao encontrado"


# ==============================================================================
# 2. Testes de Integracao: Hierarquia BFLA em POST /api/v1/usuarios
# ==============================================================================

def test_secretaria_tenta_criar_admin_retorna_403(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Tentativa Admin",
        "email": "hacker.admin@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "admin",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_sec1"])
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Privilegio insuficiente para conceder este perfil"


def test_secretaria_tenta_criar_coordenador_retorna_403(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Tentativa Coordenador",
        "email": "hacker.coord@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "coordenador",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_sec1"])
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Privilegio insuficiente para conceder este perfil"


def test_secretaria_tenta_criar_secretaria_retorna_403(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Tentativa Secretaria",
        "email": "hacker.sec@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "secretaria",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_sec1"])
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Privilegio insuficiente para conceder este perfil"


def test_secretaria_cria_professor_no_proprio_campus_retorna_201(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Novo Professor Valido",
        "email": "prof.valido@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "professor",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_sec1"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "prof.valido@sigaas.edu"
    assert data["perfil"] == "professor"
    assert data["ativo"] is True


def test_secretaria_cria_aluno_no_proprio_campus_retorna_201(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Novo Aluno Valido",
        "email": "aluno.valido@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "aluno",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_sec1"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "aluno.valido@sigaas.edu"
    assert data["perfil"] == "aluno"
    assert data["ativo"] is True


def test_coordenador_tenta_criar_admin_retorna_403(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Tentativa Admin por Coord",
        "email": "coord.admin@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "admin",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_coord1"])
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Privilegio insuficiente para conceder este perfil"


def test_coordenador_tenta_criar_coordenador_retorna_403(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Tentativa Outro Coord",
        "email": "coord.coord@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "coordenador",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_coord1"])
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Privilegio insuficiente para conceder este perfil"


def test_coordenador_cria_secretaria_no_proprio_campus_retorna_201(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Nova Secretaria por Coord",
        "email": "coord.sec@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "secretaria",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_coord1"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "coord.sec@sigaas.edu"
    assert data["perfil"] == "secretaria"
    assert data["ativo"] is True


def test_coordenador_cria_professor_no_proprio_campus_retorna_201(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Professor Criado por Coord",
        "email": "coord.prof@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "professor",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_coord1"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "coord.prof@sigaas.edu"
    assert data["perfil"] == "professor"


def test_coordenador_cria_aluno_no_proprio_campus_retorna_201(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Aluno Criado por Coord",
        "email": "coord.aluno@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "aluno",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_coord1"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "coord.aluno@sigaas.edu"
    assert data["perfil"] == "aluno"


def test_coordenador_tenta_criar_usuario_em_outro_campus_retorna_403(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c2"].id,
        "nome": "Professor no Campus 2",
        "email": "coord.prof.c2@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "professor",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_coord1"])
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Acesso negado: restrito ao seu campus"


def test_secretaria_tenta_criar_usuario_em_outro_campus_retorna_403(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c2"].id,
        "nome": "Aluno no Campus 2",
        "email": "sec.aluno.c2@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "aluno",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_sec1"])
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Acesso negado: restrito ao seu campus"


def test_nao_admin_tenta_criar_com_campus_inexistente_retorna_403_sem_oraculo(client, cenario_rbac):
    """Garante que nao-admin receba 403 e nao 404 para campus inexistente (prevencao de oraculo)."""
    payload = {
        "campus_id": 99999,
        "nome": "Usuario Tentativa Oraculo",
        "email": "oraculo@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "professor",
    }
    resp_coord = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_coord1"])
    assert resp_coord.status_code == 403
    assert resp_coord.json()["detail"] == "Acesso negado: restrito ao seu campus"

    resp_sec = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_sec1"])
    assert resp_sec.status_code == 403
    assert resp_sec.json()["detail"] == "Acesso negado: restrito ao seu campus"


def test_admin_tenta_criar_com_campus_inexistente_retorna_404(client, cenario_rbac):
    """Admin com escopo global recebe 404 caso o campus referenciado nao exista no banco."""
    payload = {
        "campus_id": 99999,
        "nome": "Usuario Admin Campus Inexistente",
        "email": "admin.404@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "professor",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_admin"])
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Campus nao encontrado"


def test_admin_pode_criar_qualquer_perfil_em_qualquer_campus(client, cenario_rbac):
    c2 = cenario_rbac["c2"]
    perfis = ["admin", "coordenador", "secretaria", "professor", "aluno"]
    for i, perfil in enumerate(perfis):
        payload = {
            "campus_id": c2.id,
            "nome": f"Usuario Criado por Admin {i}",
            "email": f"admin.criou.{perfil}@sigaas.edu",
            "senha": "senhaSegura123",
            "perfil": perfil,
        }
        resp = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_admin"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["perfil"] == perfil
        assert data["campus_id"] == c2.id


def test_professor_e_aluno_nao_podem_criar_usuarios(client, cenario_rbac):
    payload = {
        "campus_id": cenario_rbac["c1"].id,
        "nome": "Tentativa por Nao Autorizado",
        "email": "proibido@sigaas.edu",
        "senha": "senhaSegura123",
        "perfil": "aluno",
    }
    resp_prof = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_prof1"])
    assert resp_prof.status_code == 403
    assert resp_prof.json()["detail"] == "Acesso negado: privilegio insuficiente"

    resp_aluno = client.post("/api/v1/usuarios", json=payload, headers=cenario_rbac["headers_aluno1"])
    assert resp_aluno.status_code == 403
    assert resp_aluno.json()["detail"] == "Acesso negado: privilegio insuficiente"
