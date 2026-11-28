"""
Testes de integracao para o endpoint HTTP do Motor C (/api/v1/motor).
"""

import ctypes
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.session import Base, get_db
from app.main import app
from app.models import Campus, PerfilUsuario, Usuario
from app.services.motor_service import MotorAlocacaoService, SalaC, TurmaC, TIPO_SALA_REGULAR, TURNO_MASK_MATUTINO, TURNO_MATUTINO, motor_service


@pytest.fixture
def motor_test_db():
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
def motor_client(motor_test_db):
    def override_get_db():
        yield motor_test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def tokens_motor(motor_test_db):
    campus = Campus(nome="Campus Motor", cidade="Recife", endereco="Av. Principal")
    motor_test_db.add(campus)
    motor_test_db.commit()
    senha = get_password_hash("sigaas123")
    admin = Usuario(nome="Admin Motor", email="admin.motor@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ADMIN, campus_id=campus.id)
    aluno = Usuario(nome="Aluno Motor", email="aluno.motor@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO, campus_id=campus.id)
    motor_test_db.add_all([admin, aluno])
    motor_test_db.commit()
    return {
        "admin": create_access_token({"sub": str(admin.id), "perfil": admin.perfil.value}),
        "aluno": create_access_token({"sub": str(aluno.id), "perfil": aluno.perfil.value}),
    }


def test_endpoint_motor_status():
    client = TestClient(app)
    res = client.get("/api/v1/motor/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "OpenMP" in data["versao"]
    assert data["biblioteca"] is not None
    assert data["heuristica"] is not None
    assert isinstance(data["opencl_disponivel"], bool)
    assert isinstance(data["backends_suportados"], list)
    assert "openmp" in data["backends_suportados"]


def test_endpoint_motor_dispositivos_requer_jwt(motor_client, tokens_motor):
    res_unauth = motor_client.get("/api/v1/motor/dispositivos")
    assert res_unauth.status_code == 401

    res_forbidden = motor_client.get(
        "/api/v1/motor/dispositivos",
        headers={"Authorization": f"Bearer {tokens_motor['aluno']}"},
    )
    assert res_forbidden.status_code == 403

    res_ok = motor_client.get(
        "/api/v1/motor/dispositivos",
        headers={"Authorization": f"Bearer {tokens_motor['admin']}"},
    )
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert isinstance(data["opencl_disponivel"], bool)
    assert data["total"] == len(data["dispositivos"])
    if data["opencl_disponivel"]:
        assert data["total"] >= 1
        dev = data["dispositivos"][0]
        assert dev["device_name"]
        assert dev["device_type"] in ("GPU", "CPU", "ACCELERATOR", "UNKNOWN")
        assert dev["compute_units"] >= 1


def test_motor_service_opencl_abi_lib_path_e_baseline_opcional(monkeypatch):
    from app.services.motor_service import OpenCLDeviceInfoC

    assert ctypes.sizeof(OpenCLDeviceInfoC) == 192
    assert motor_service.lib_path is not None

    monkeypatch.setenv("MOTOR_LIB_PATH", str(motor_service.lib_path))
    svc_custom = MotorAlocacaoService()
    assert svc_custom.lib is not None
    assert svc_custom.lib_path == motor_service.lib_path

    salas = [SalaC(id=1, capacidade=40, tipo=TIPO_SALA_REGULAR, turnos_mask=TURNO_MASK_MATUTINO)]
    turmas = [
        TurmaC(
            id=1,
            num_matriculados=30,
            tipo_exigido=TIPO_SALA_REGULAR,
            turno=TURNO_MATUTINO,
            dia_semana_sugerido=0,
            hora_inicio_min=480,
            hora_fim_min=600,
            professor_id=10,
        )
    ]
    _, metricas = svc_custom.otimizar_alocacao(
        turmas=turmas,
        salas=salas,
        max_threads=2,
        backend="openmp",
        executar_baseline_sequencial=False,
    )
    assert metricas["tempo_sequencial_ms"] == 0.0
    assert metricas["backend_usado"] == "openmp"


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
