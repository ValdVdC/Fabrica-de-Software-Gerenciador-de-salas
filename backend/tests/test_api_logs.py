"""
Testes automatizados TDD para o endpoint GET /api/v1/logs e trilha de auditoria.
Cobre paginacao, filtros combinados (tipo_evento, usuario_id, datas, horario_id),
RBAC, isolamento multi-campus (BOLA/IDOR), operacoes somente-leitura (405) e backfill.
"""

from datetime import datetime, timedelta, timezone, time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.session import Base, get_db
from app.main import app as fastapi_app
from app.models import (
    Campus,
    Curso,
    Disciplina,
    Horario,
    LogAlocacao,
    PerfilUsuario,
    Sala,
    TipoEventoLog,
    TipoSala,
    Turma,
    Turno,
    Usuario,
)


@pytest.fixture
def test_db():
    """Banco SQLite em memoria isolado para os testes de logs."""
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
def client(test_db: Session):
    """TestClient do FastAPI com injecao de sessao de banco de testes."""
    def override_get_db():
        yield test_db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def seed_cenario_logs(test_db: Session):
    """Semeia campus, usuarios de diferentes perfis e logs de auditoria."""
    senha = get_password_hash("senha_secreta")

    c1 = Campus(nome="Campus Alpha", cidade="Petrolina", endereco="Rua 1, 100")
    c2 = Campus(nome="Campus Beta", cidade="Juazeiro", endereco="Rua 2, 200")
    test_db.add_all([c1, c2])
    test_db.flush()

    admin = Usuario(campus_id=c1.id, nome="Admin Master", email="admin@test.com", senha_hash=senha, perfil=PerfilUsuario.ADMIN)
    coord1 = Usuario(campus_id=c1.id, nome="Coord Alpha", email="coord1@test.com", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR)
    sec1 = Usuario(campus_id=c1.id, nome="Secretaria Alpha", email="sec1@test.com", senha_hash=senha, perfil=PerfilUsuario.SECRETARIA)
    coord2 = Usuario(campus_id=c2.id, nome="Coord Beta", email="coord2@test.com", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR)
    prof = Usuario(campus_id=c1.id, nome="Prof Alpha", email="prof@test.com", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR)
    aluno = Usuario(campus_id=c1.id, nome="Aluno Alpha", email="aluno@test.com", senha_hash=senha, perfil=PerfilUsuario.ALUNO)
    test_db.add_all([admin, coord1, sec1, coord2, prof, aluno])
    test_db.flush()

    sala1 = Sala(campus_id=c1.id, bloco="A", numero="101", tipo=TipoSala.REGULAR, capacidade=40, turnos_disponiveis=["matutino"])
    sala2 = Sala(campus_id=c2.id, bloco="B", numero="201", tipo=TipoSala.REGULAR, capacidade=40, turnos_disponiveis=["matutino"])
    test_db.add_all([sala1, sala2])
    test_db.flush()

    curso1 = Curso(campus_id=c1.id, nome="Computacao", codigo="CC")
    test_db.add(curso1)
    test_db.flush()

    disc1 = Disciplina(curso_id=curso1.id, nome="Algoritmos", codigo="CC101", carga_horaria=60)
    test_db.add(disc1)
    test_db.flush()

    turma1 = Turma(disciplina_id=disc1.id, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=20, turno_preferido=Turno.MATUTINO)
    test_db.add(turma1)
    test_db.flush()

    horario1 = Horario(campus_id=c1.id, turma_id=turma1.id, sala_id=sala1.id, dia_semana=1, hora_inicio=time(8, 0), hora_fim=time(10, 0))
    test_db.add(horario1)
    test_db.flush()

    # Base temporal para teste de ordenacao e filtros
    base_time = datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Logs no Campus 1
    log1 = LogAlocacao(
        campus_id=c1.id,
        horario_id=horario1.id,
        tipo_evento=TipoEventoLog.CRIACAO,
        usuario_responsavel=coord1.id,
        snapshot_evento={"entidade": "horario", "entidade_id": horario1.id},
        detalhes="Alocacao inicial",
        timestamp=base_time - timedelta(days=2),
    )
    log2 = LogAlocacao(
        campus_id=c1.id,
        horario_id=horario1.id,
        tipo_evento=TipoEventoLog.ALTERACAO,
        usuario_responsavel=coord1.id,
        snapshot_evento={"entidade": "sala", "entidade_id": sala1.id},
        detalhes="Alteracao de sala",
        timestamp=base_time - timedelta(days=1),
    )
    log3 = LogAlocacao(
        campus_id=c1.id,
        horario_id=None,
        tipo_evento=TipoEventoLog.CANCELAMENTO,
        usuario_responsavel=sec1.id,
        snapshot_evento={"entidade": "turma", "entidade_id": turma1.id},
        detalhes="Cancelamento de turma",
        timestamp=base_time,
    )
    # Log no Campus 2
    log4 = LogAlocacao(
        campus_id=c2.id,
        horario_id=None,
        tipo_evento=TipoEventoLog.CRIACAO,
        usuario_responsavel=coord2.id,
        snapshot_evento={"entidade": "sala", "entidade_id": sala2.id},
        detalhes="Criacao sala campus 2",
        timestamp=base_time + timedelta(days=1),
    )

    test_db.add_all([log1, log2, log3, log4])
    test_db.commit()

    return {
        "admin": admin,
        "coord1": coord1,
        "sec1": sec1,
        "coord2": coord2,
        "prof": prof,
        "aluno": aluno,
        "c1": c1,
        "c2": c2,
        "horario1": horario1,
        "log1": log1,
        "log2": log2,
        "log3": log3,
        "log4": log4,
    }


def auth_header(user: Usuario) -> dict:
    token = create_access_token(data={"sub": str(user.id), "perfil": user.perfil.value, "campus_id": user.campus_id})
    return {"Authorization": f"Bearer {token}"}


def test_listar_logs_autenticado_admin_ordenacao_e_paginacao(client: TestClient, seed_cenario_logs: dict):
    """Admin lista todos os logs; valida ordenacao decrescente e paginacao."""
    headers = auth_header(seed_cenario_logs["admin"])
    resp = client.get("/api/v1/logs?skip=0&limit=2", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

    # Verifica ordenacao decrescente: o primeiro registro deve ser o log4 (mais recente)
    assert data[0]["id"] == seed_cenario_logs["log4"].id
    assert data[1]["id"] == seed_cenario_logs["log3"].id

    # Segunda pagina
    resp_page2 = client.get("/api/v1/logs?skip=2&limit=2", headers=headers)
    assert resp_page2.status_code == 200
    data2 = resp_page2.json()
    assert len(data2) == 2
    assert data2[0]["id"] == seed_cenario_logs["log2"].id
    assert data2[1]["id"] == seed_cenario_logs["log1"].id


def test_listar_logs_filtros_combinados(client: TestClient, seed_cenario_logs: dict):
    """Testa filtros combinados: tipo_evento, usuario_id, data_inicio, data_fim e horario_id."""
    headers = auth_header(seed_cenario_logs["admin"])
    coord1 = seed_cenario_logs["coord1"]
    horario1 = seed_cenario_logs["horario1"]

    # 1. Filtro por tipo_evento
    resp = client.get("/api/v1/logs?tipo_evento=criacao", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["tipo_evento"] == "criacao" for item in data)
    assert len(data) == 2

    # 2. Filtro por usuario_id
    resp = client.get(f"/api/v1/logs?usuario_id={coord1.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["usuario_responsavel"] == coord1.id for item in data)
    assert len(data) == 2

    # 3. Filtro por horario_id
    resp = client.get(f"/api/v1/logs?horario_id={horario1.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["horario_id"] == horario1.id for item in data)
    assert len(data) == 2

    # 4. Filtro por intervalo de datas (2026-10-08 a 2026-10-09)
    resp = client.get("/api/v1/logs?data_inicio=2026-10-08&data_fim=2026-10-09", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

    # 5. Combinacao multipla
    resp = client.get(
        f"/api/v1/logs?tipo_evento=criacao&usuario_id={coord1.id}&horario_id={horario1.id}",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == seed_cenario_logs["log1"].id


def test_listar_logs_periodo_invalido_retorna_422(client: TestClient, seed_cenario_logs: dict):
    """Quando data_fim < data_inicio a API deve retornar 422 Unprocessable Entity."""
    headers = auth_header(seed_cenario_logs["admin"])
    resp = client.get("/api/v1/logs?data_inicio=2026-10-15&data_fim=2026-10-10", headers=headers)
    assert resp.status_code == 422
    assert "data_fim" in resp.json()["detail"].lower()


def test_listar_logs_isolamento_campus_bola(client: TestClient, seed_cenario_logs: dict):
    """Garante isolamento multi-campus (BOLA): Coordenador e Secretaria restritos ao seu campus."""
    coord1 = seed_cenario_logs["coord1"]
    sec1 = seed_cenario_logs["sec1"]
    coord2 = seed_cenario_logs["coord2"]
    admin = seed_cenario_logs["admin"]
    c1 = seed_cenario_logs["c1"]
    c2 = seed_cenario_logs["c2"]

    # Coordenador Campus 1: apenas logs do Campus 1
    resp = client.get("/api/v1/logs", headers=auth_header(coord1))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert all(item["campus_id"] == c1.id for item in data)

    # Coordenador Campus 1 tenta consultar ?campus_id=2 -> filtro e ignorado e restrito ao seu campus
    resp_tamper = client.get(f"/api/v1/logs?campus_id={c2.id}", headers=auth_header(coord1))
    assert resp_tamper.status_code == 200
    data_tamper = resp_tamper.json()
    assert all(item["campus_id"] == c1.id for item in data_tamper)

    # Secretaria Campus 1: apenas logs do Campus 1
    resp_sec = client.get("/api/v1/logs", headers=auth_header(sec1))
    assert resp_sec.status_code == 200
    data_sec = resp_sec.json()
    assert len(data_sec) == 3
    assert all(item["campus_id"] == c1.id for item in data_sec)

    # Coordenador Campus 2: apenas logs do Campus 2
    resp2 = client.get("/api/v1/logs", headers=auth_header(coord2))
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2) == 1
    assert data2[0]["campus_id"] == c2.id

    # Admin com filtro de campus explicito
    resp_admin_c2 = client.get(f"/api/v1/logs?campus_id={c2.id}", headers=auth_header(admin))
    assert resp_admin_c2.status_code == 200
    data_admin_c2 = resp_admin_c2.json()
    assert len(data_admin_c2) == 1
    assert data_admin_c2[0]["campus_id"] == c2.id


def test_listar_logs_rbac_privilegios(client: TestClient, seed_cenario_logs: dict):
    """Professor e Aluno recebem 403; Nao autenticado recebe 401."""
    # Nao autenticado
    resp_anon = client.get("/api/v1/logs")
    assert resp_anon.status_code == 401

    # Professor
    resp_prof = client.get("/api/v1/logs", headers=auth_header(seed_cenario_logs["prof"]))
    assert resp_prof.status_code == 403

    # Aluno
    resp_aluno = client.get("/api/v1/logs", headers=auth_header(seed_cenario_logs["aluno"]))
    assert resp_aluno.status_code == 403


def test_logs_endpoints_somente_leitura_405(client: TestClient, seed_cenario_logs: dict):
    """Metodos de mutacao (POST, PUT, PATCH, DELETE) em /api/v1/logs devem retornar 405 Method Not Allowed."""
    headers = auth_header(seed_cenario_logs["admin"])
    assert client.post("/api/v1/logs", json={}, headers=headers).status_code == 405
    assert client.put("/api/v1/logs", json={}, headers=headers).status_code == 405
    assert client.patch("/api/v1/logs", json={}, headers=headers).status_code == 405
    assert client.delete("/api/v1/logs", headers=headers).status_code == 405


def test_migration_backfill_campus_id(test_db: Session):
    """Valida a consulta de backfill da migration: preenche campus_id a partir de horario.campus_id."""
    c = Campus(nome="Campus Teste Backfill", cidade="Petrolina", endereco="Rua 3")
    test_db.add(c)
    test_db.flush()

    u = Usuario(campus_id=c.id, nome="User B", email="userb@teste.com", senha_hash="hash", perfil=PerfilUsuario.ADMIN)
    test_db.add(u)
    test_db.flush()

    curso = Curso(campus_id=c.id, nome="Curso B", codigo="CB")
    test_db.add(curso)
    test_db.flush()

    disc = Disciplina(curso_id=curso.id, nome="Disc B", codigo="DB1", carga_horaria=30)
    test_db.add(disc)
    test_db.flush()

    sala = Sala(campus_id=c.id, bloco="B", numero="1", tipo=TipoSala.REGULAR, capacidade=30, turnos_disponiveis=["matutino"])
    test_db.add(sala)
    test_db.flush()

    turma = Turma(disciplina_id=disc.id, periodo_letivo="2026.1", num_matriculados=10, turno_preferido=Turno.MATUTINO)
    test_db.add(turma)
    test_db.flush()

    horario = Horario(campus_id=c.id, turma_id=turma.id, sala_id=sala.id, dia_semana=2, hora_inicio=time(10, 0), hora_fim=time(12, 0))
    test_db.add(horario)
    test_db.flush()

    # Cria log legado sem campus_id
    log_legado = LogAlocacao(
        campus_id=None,
        horario_id=horario.id,
        tipo_evento=TipoEventoLog.CRIACAO,
        usuario_responsavel=u.id,
        detalhes="Log legado sem campus_id",
    )
    test_db.add(log_legado)
    test_db.commit()

    assert log_legado.campus_id is None

    # Executa a query de backfill exatamente como definida na migration Alembic
    test_db.execute(text("""
        UPDATE log_alocacao
        SET campus_id = (
            SELECT h.campus_id FROM horario h WHERE h.id = log_alocacao.horario_id
        )
        WHERE log_alocacao.horario_id IS NOT NULL AND log_alocacao.campus_id IS NULL
    """))
    test_db.commit()

    test_db.refresh(log_legado)
    assert log_legado.campus_id == c.id


def test_crud_sala_gera_logs_em_criacao_alteracao_e_remocao(client: TestClient, test_db: Session, seed_cenario_logs: dict):
    """Verifica que operacoes de CRUD em salas geram automaticamente registros em LogAlocacao."""
    headers = auth_header(seed_cenario_logs["admin"])
    c1 = seed_cenario_logs["c1"]

    # 1. Criacao
    payload_criar = {
        "campus_id": c1.id,
        "bloco": "C",
        "numero": "301",
        "tipo": "regular",
        "capacidade": 35,
        "turnos_disponiveis": ["matutino"],
    }
    resp_criar = client.post("/api/v1/salas", json=payload_criar, headers=headers)
    assert resp_criar.status_code == 201
    sala_id = resp_criar.json()["id"]

    log_criacao = test_db.scalar(
        select(LogAlocacao)
        .where(
            LogAlocacao.tipo_evento == TipoEventoLog.CRIACAO,
            LogAlocacao.campus_id == c1.id,
        )
        .order_by(LogAlocacao.id.desc())
    )
    assert log_criacao is not None
    assert log_criacao.snapshot_evento == {"entidade": "sala", "entidade_id": sala_id}

    # 2. Alteracao
    payload_atualizar = {"capacidade": 45}
    resp_atualizar = client.put(f"/api/v1/salas/{sala_id}", json=payload_atualizar, headers=headers)
    assert resp_atualizar.status_code == 200

    log_alteracao = test_db.scalar(
        select(LogAlocacao)
        .where(
            LogAlocacao.tipo_evento == TipoEventoLog.ALTERACAO,
            LogAlocacao.campus_id == c1.id,
        )
        .order_by(LogAlocacao.id.desc())
    )
    assert log_alteracao is not None
    assert log_alteracao.snapshot_evento == {"entidade": "sala", "entidade_id": sala_id}

    # 3. Remocao
    resp_excluir = client.delete(f"/api/v1/salas/{sala_id}", headers=headers)
    assert resp_excluir.status_code == 204

    log_remocao = test_db.scalar(
        select(LogAlocacao)
        .where(
            LogAlocacao.tipo_evento == TipoEventoLog.CANCELAMENTO,
            LogAlocacao.campus_id == c1.id,
        )
        .order_by(LogAlocacao.id.desc())
    )
    assert log_remocao is not None
    assert log_remocao.snapshot_evento == {"entidade": "sala", "entidade_id": sala_id}


def test_crud_turma_gera_log_em_criacao(client: TestClient, test_db: Session, seed_cenario_logs: dict):
    """Verifica que a criacao de turma gera registro correspondente em LogAlocacao."""
    headers = auth_header(seed_cenario_logs["admin"])
    c1 = seed_cenario_logs["c1"]

    # Cria curso e disciplina auxiliar
    curso = Curso(campus_id=c1.id, nome="Fisica", codigo="FIS")
    test_db.add(curso)
    test_db.flush()
    disc = Disciplina(curso_id=curso.id, nome="Mecanica", codigo="FIS101", carga_horaria=60)
    test_db.add(disc)
    test_db.commit()

    payload = {
        "disciplina_id": disc.id,
        "periodo_letivo": "2026.1",
        "turno_preferido": "matutino",
    }
    resp = client.post("/api/v1/turmas", json=payload, headers=headers)
    assert resp.status_code == 201
    turma_id = resp.json()["id"]

    log = test_db.scalar(
        select(LogAlocacao)
        .where(
            LogAlocacao.tipo_evento == TipoEventoLog.CRIACAO,
            LogAlocacao.campus_id == c1.id,
        )
        .order_by(LogAlocacao.id.desc())
    )
    assert log is not None
    assert log.snapshot_evento == {"entidade": "turma", "entidade_id": turma_id}


def test_crud_usuario_gera_log_em_criacao(client: TestClient, test_db: Session, seed_cenario_logs: dict):
    """Verifica que o cadastro de usuario gera registro em LogAlocacao."""
    headers = auth_header(seed_cenario_logs["admin"])
    c1 = seed_cenario_logs["c1"]

    payload = {
        "campus_id": c1.id,
        "nome": "Novo Usuario Auditoria",
        "email": "auditoria_novo@test.com",
        "senha": "senha_segura_123",
        "perfil": "professor",
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=headers)
    assert resp.status_code == 201
    novo_user_id = resp.json()["id"]

    log = test_db.scalar(
        select(LogAlocacao)
        .where(
            LogAlocacao.tipo_evento == TipoEventoLog.CRIACAO,
            LogAlocacao.campus_id == c1.id,
        )
        .order_by(LogAlocacao.id.desc())
    )
    assert log is not None
    assert log.snapshot_evento == {"entidade": "usuario", "entidade_id": novo_user_id}

