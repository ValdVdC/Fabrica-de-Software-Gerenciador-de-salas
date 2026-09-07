"""Testes de integracao dos routers da API v1 e validacao de schemas."""
from datetime import time
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models import Campus, Usuario, Sala, PerfilUsuario, TipoSala, Turno
from app.schemas.horario import HorarioCreate


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


def test_routers_registrados():
    paths = fastapi_app.openapi()["paths"]
    for r in ["/api/v1/campi", "/api/v1/usuarios", "/api/v1/salas", "/api/v1/turmas", "/api/v1/horarios"]:
        assert any(p.startswith(r) for p in paths)



def test_crud_campus(client):
    assert client.get("/api/v1/campi").json() == []
    res = client.post("/api/v1/campi", json={"nome": "Campus Litoral", "cidade": "Parnaiba", "endereco": "Av Sao Sebastiao"})
    assert res.status_code == 201
    cid = res.json()["id"]
    assert client.get(f"/api/v1/campi/{cid}").json()["cidade"] == "Parnaiba"
    assert client.post("/api/v1/campi", json={}).status_code == 422
    assert client.get("/api/v1/campi/9999").status_code == 404


def test_paginacao_sanitizada(client):
    for q in ["skip=-1", "limit=0", "limit=101"]:
        assert client.get(f"/api/v1/campi?{q}").status_code == 422


def test_validacao_horario_schema():
    for d, hi, hf in [(7, time(8), time(10)), (1, time(10), time(8))]:
        with pytest.raises(ValidationError):
            HorarioCreate(campus_id=1, turma_id=1, sala_id=1, dia_semana=d, hora_inicio=hi, hora_fim=hf)


def test_serializacao_entidades_com_dados(client, test_db):
    c = Campus(nome="Campus Sul", cidade="Floriano", endereco="Rua 2")
    test_db.add(c)
    test_db.commit()
    u = Usuario(campus_id=c.id, nome="Prof", email="prof@sigaas.edu", senha_hash="h", perfil=PerfilUsuario.PROFESSOR)
    s = Sala(campus_id=c.id, bloco="B", numero="201", tipo=TipoSala.REGULAR, capacidade=30, turnos_disponiveis=[Turno.MATUTINO])
    test_db.add_all([u, s])
    test_db.commit()
    res_u = client.get(f"/api/v1/usuarios/{u.id}")
    assert res_u.status_code == 200 and "senha_hash" not in res_u.json() and res_u.json()["perfil"] == "professor"
    res_s = client.get(f"/api/v1/salas/{s.id}")
    assert res_s.status_code == 200 and res_s.json()["tipo"] == "regular"


@pytest.mark.parametrize("endpoint", ["usuarios", "salas", "turmas", "horarios"])
def test_listar_e_obter_404_recursos(client, endpoint):
    assert client.get(f"/api/v1/{endpoint}").status_code == 200 and client.get(f"/api/v1/{endpoint}/9999").status_code == 404
