"""Testes automatizados TDD para gestao administrativa de salas, equipamentos e RBAC."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models import Campus, Usuario, PerfilUsuario, Equipamento, Sala, TipoSala
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
    campus_a = Campus(nome="Campus Norte", cidade="Teresina", endereco="Rua 1")
    campus_b = Campus(nome="Campus Sul", cidade="Parnaiba", endereco="Rua 2")
    test_db.add_all([campus_a, campus_b])
    test_db.commit()

    senha = get_password_hash("sigaas123")
    admin = Usuario(nome="Admin", email="admin@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ADMIN, campus_id=campus_a.id)
    coord_a = Usuario(nome="Coord A", email="coord_a@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR, campus_id=campus_a.id)
    aluno = Usuario(nome="Aluno", email="aluno@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO, campus_id=campus_a.id)
    test_db.add_all([admin, coord_a, aluno])
    test_db.commit()

    return {
        "campus_a": campus_a,
        "campus_b": campus_b,
        "token_admin": create_access_token({"sub": str(admin.id), "perfil": admin.perfil.value}),
        "token_coord_a": create_access_token({"sub": str(coord_a.id), "perfil": coord_a.perfil.value}),
        "token_aluno": create_access_token({"sub": str(aluno.id), "perfil": aluno.perfil.value}),
    }


def test_criar_sala_sucesso_admin(client, setup_cenario):
    token, campus_id = setup_cenario["token_admin"], setup_cenario["campus_a"].id
    payload = {"campus_id": campus_id, "bloco": "A", "numero": "101", "tipo": "regular", "capacidade": 45, "turnos_disponiveis": ["matutino", "noturno"]}
    resp = client.post("/api/v1/salas", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["bloco"] == "A" and data["numero"] == "101" and data["capacidade"] == 45 and data["campus_id"] == campus_id


def test_criar_sala_bloqueio_duplicidade(client, setup_cenario):
    token, campus_id = setup_cenario["token_admin"], setup_cenario["campus_a"].id
    payload = {"campus_id": campus_id, "bloco": "B", "numero": "202", "tipo": "laboratorio", "capacidade": 30, "turnos_disponiveis": ["vespertino"]}
    assert client.post("/api/v1/salas", json=payload, headers={"Authorization": f"Bearer {token}"}).status_code == 201
    resp2 = client.post("/api/v1/salas", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 409 and "Ja existe" in resp2.json()["detail"]


def test_coordenador_isolamento_multi_campus(client, setup_cenario):
    token_coord = setup_cenario["token_coord_a"]
    campus_a, campus_b = setup_cenario["campus_a"].id, setup_cenario["campus_b"].id
    payload_ok = {"campus_id": campus_a, "bloco": "C", "numero": "301", "tipo": "regular", "capacidade": 40, "turnos_disponiveis": ["matutino"]}
    assert client.post("/api/v1/salas", json=payload_ok, headers={"Authorization": f"Bearer {token_coord}"}).status_code == 201
    payload_inv = {"campus_id": campus_b, "bloco": "C", "numero": "301", "tipo": "regular", "capacidade": 40, "turnos_disponiveis": ["matutino"]}
    resp_inv = client.post("/api/v1/salas", json=payload_inv, headers={"Authorization": f"Bearer {token_coord}"})
    assert resp_inv.status_code == 403 and "coordenador" in resp_inv.json()["detail"].lower()


def test_bloqueio_rbac_perfil_sem_permissao(client, setup_cenario):
    token_aluno = setup_cenario["token_aluno"]
    payload = {"campus_id": setup_cenario["campus_a"].id, "bloco": "D", "numero": "401", "tipo": "auditorio", "capacidade": 100, "turnos_disponiveis": ["noturno"]}
    assert client.post("/api/v1/salas", json=payload, headers={"Authorization": f"Bearer {token_aluno}"}).status_code == 403


def test_listar_salas_com_filtro_e_coordenador(client, setup_cenario, test_db):
    campus_a, campus_b = setup_cenario["campus_a"], setup_cenario["campus_b"]
    sala_a = Sala(campus_id=campus_a.id, bloco="A", numero="1", tipo=TipoSala.REGULAR, capacidade=30, turnos_disponiveis=["matutino"])
    sala_b = Sala(campus_id=campus_b.id, bloco="B", numero="1", tipo=TipoSala.REGULAR, capacidade=30, turnos_disponiveis=["vespertino"])
    test_db.add_all([sala_a, sala_b])
    test_db.commit()
    resp_coord = client.get("/api/v1/salas", headers={"Authorization": f"Bearer {setup_cenario['token_coord_a']}"})
    assert resp_coord.status_code == 200 and len(resp_coord.json()) == 1 and resp_coord.json()[0]["campus_id"] == campus_a.id
    resp_admin = client.get("/api/v1/salas", headers={"Authorization": f"Bearer {setup_cenario['token_admin']}"})
    assert resp_admin.status_code == 200 and len(resp_admin.json()) >= 2


def test_crud_equipamento_e_duplicidade(client, setup_cenario):
    token = setup_cenario["token_admin"]
    payload = {"nome": "Projetor Laser 4K", "descricao": "Projetor de alta resolucao"}
    assert client.post("/api/v1/equipamentos", json=payload, headers={"Authorization": f"Bearer {token}"}).status_code == 201
    assert client.post("/api/v1/equipamentos", json=payload, headers={"Authorization": f"Bearer {token}"}).status_code == 409
    resp_list = client.get("/api/v1/equipamentos", headers={"Authorization": f"Bearer {token}"})
    assert resp_list.status_code == 200 and "Projetor Laser 4K" in [e["nome"] for e in resp_list.json()]


def test_associar_equipamento_a_sala(client, setup_cenario, test_db):
    campus_a = setup_cenario["campus_a"]
    sala = Sala(campus_id=campus_a.id, bloco="Z", numero="99", tipo=TipoSala.REGULAR, capacidade=20, turnos_disponiveis=["matutino"])
    equip = Equipamento(nome="Ar Condicionado 30000 BTUs")
    test_db.add_all([sala, equip])
    test_db.commit()
    token = setup_cenario["token_admin"]
    payload = {"equipamento_id": equip.id, "quantidade": 2}
    resp = client.post(f"/api/v1/salas/{sala.id}/equipamentos", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201 and resp.json()["quantidade"] == 2
    assert client.post("/api/v1/salas/9999/equipamentos", json=payload, headers={"Authorization": f"Bearer {token}"}).status_code == 404
    assert client.post(f"/api/v1/salas/{sala.id}/equipamentos", json={"equipamento_id": 9999, "quantidade": 1}, headers={"Authorization": f"Bearer {token}"}).status_code == 404
