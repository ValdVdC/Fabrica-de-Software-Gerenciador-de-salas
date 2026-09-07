"""
Testes unitarios para o servico do Motor de Alocacao em C via ctypes.
"""

from app.services.motor_service import motor_service


def test_motor_service_status():
    status = motor_service.get_status()
    assert status["status"] == "online"
    assert "OpenMP" in status["versao"]
    assert status["biblioteca"] is not None


def test_motor_service_teste_integracao():
    res = motor_service.executar_teste(15, 27)
    assert res["resultado"] == 42
    assert res["ctypes_ok"] is True
