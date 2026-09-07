"""
Teste automatizado de verificação de integridade da API (Health Check).
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_root_api():
    response = client.get("/api/v1")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data


def test_docs_redirect():
    response = client.get("/docs", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/api/v1/docs"


def test_root_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/api/v1"

