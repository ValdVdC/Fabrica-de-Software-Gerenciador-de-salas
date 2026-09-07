"""
Testes de integracao para o endpoint HTTP do Motor C (/api/v1/motor).
"""

from fastapi.testclient import TestClient
from app.main import app


def test_endpoint_motor_status():
    client = TestClient(app)
    res = client.get("/api/v1/motor/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "OpenMP" in data["versao"]
    assert data["biblioteca"] is not None


def test_endpoint_motor_teste_integracao():
    client = TestClient(app)
    res = client.post("/api/v1/motor/teste-integracao", json={"a": 10, "b": 32})
    assert res.status_code == 200
    data = res.json()
    assert data["resultado"] == 42
    assert data["ctypes_ok"] is True

    # Valida rejeicao de inteiros fora do limite (prevencao de overflow)
    res_overflow = client.post("/api/v1/motor/teste-integracao", json={"a": 2_000_000, "b": 1})
    assert res_overflow.status_code == 422
