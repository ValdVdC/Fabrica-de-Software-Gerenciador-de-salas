"""
Teste automatizado de verificação de integridade da API (Health Check).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.session import Base, get_db


@pytest.fixture
def client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()


def test_health_check_connected(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "version" in data


def test_health_check_disconnected():
    # Sem override e sem banco rodando, deve retornar degraded
    with TestClient(app) as direct_client:
        response = direct_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["database"] in ["connected", "disconnected"]
        if data["database"] == "disconnected":
            assert data["status"] == "degraded"


def test_root_api(client):
    response = client.get("/api/v1")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data


def test_docs_redirect(client):
    response = client.get("/docs", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/api/v1/docs"


def test_root_redirect(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/api/v1"

