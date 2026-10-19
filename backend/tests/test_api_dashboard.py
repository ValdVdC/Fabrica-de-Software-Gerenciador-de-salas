"""
Testes automatizados TDD para os endpoints de Dashboard (Sprint 07 - Historia 1):
- GET /api/v1/dashboard/resumo
- GET /api/v1/dashboard/ocupacao

Cobre:
- Indicadores consolidados (salas_ativas, turmas, horarios, sugestoes por status, vagas_recuperadas, eventos_recentes)
- Agregacao de ocupacao por dia_semana (0 a 6) e por turno (matutino, vespertino, noturno, integral)
- Isolamento multi-campus (BOLA/IDOR) para coordenador e secretaria
- Filtro campus_id exclusivo para admin (ignorado para coordenador/secretaria)
- Controle de acesso RBAC (403 para professor/aluno, 401 para anonimo)
"""

from datetime import datetime, timedelta, timezone, time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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
    StatusSugestao,
    SugestaoRemanejamento,
    TipoEventoLog,
    TipoSala,
    Turma,
    Turno,
    Usuario,
)


@pytest.fixture
def test_db():
    """Banco SQLite em memoria isolado para os testes de dashboard."""
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


def auth_header(user: Usuario) -> dict:
    token = create_access_token(
        data={"sub": str(user.id), "perfil": user.perfil.value, "campus_id": user.campus_id}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed_dashboard(test_db: Session):
    """Semeia dois campi com salas (ativas/inativas), turmas, horarios, sugestoes e logs."""
    senha = get_password_hash("senha_secreta")

    c1 = Campus(nome="Campus Alpha", cidade="Petrolina", endereco="Rua 1, 100")
    c2 = Campus(nome="Campus Beta", cidade="Juazeiro", endereco="Rua 2, 200")
    test_db.add_all([c1, c2])
    test_db.flush()

    admin = Usuario(campus_id=c1.id, nome="Admin Master", email="admin@test.com", senha_hash=senha, perfil=PerfilUsuario.ADMIN)
    coord1 = Usuario(campus_id=c1.id, nome="Coord Alpha", email="coord1@test.com", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR)
    sec1 = Usuario(campus_id=c1.id, nome="Sec Alpha", email="sec1@test.com", senha_hash=senha, perfil=PerfilUsuario.SECRETARIA)
    coord2 = Usuario(campus_id=c2.id, nome="Coord Beta", email="coord2@test.com", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR)
    prof = Usuario(campus_id=c1.id, nome="Prof Alpha", email="prof@test.com", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR)
    aluno = Usuario(campus_id=c1.id, nome="Aluno Alpha", email="aluno@test.com", senha_hash=senha, perfil=PerfilUsuario.ALUNO)
    test_db.add_all([admin, coord1, sec1, coord2, prof, aluno])
    test_db.flush()

    # Campus 1: 2 salas ativas (cap 80 e 40) e 1 inativa (cap 50)
    sala1_grande = Sala(campus_id=c1.id, bloco="A", numero="101", tipo=TipoSala.REGULAR, capacidade=80, turnos_disponiveis=["matutino", "noturno"], ativo=True)
    sala1_peq = Sala(campus_id=c1.id, bloco="A", numero="102", tipo=TipoSala.REGULAR, capacidade=40, turnos_disponiveis=["matutino", "noturno"], ativo=True)
    sala1_inativa = Sala(campus_id=c1.id, bloco="A", numero="103", tipo=TipoSala.REGULAR, capacidade=50, turnos_disponiveis=["matutino"], ativo=False)

    # Campus 2: 1 sala ativa (cap 60) e 1 sala menor ativa (cap 30)
    sala2_grande = Sala(campus_id=c2.id, bloco="B", numero="201", tipo=TipoSala.REGULAR, capacidade=60, turnos_disponiveis=["vespertino"], ativo=True)
    sala2_peq = Sala(campus_id=c2.id, bloco="B", numero="202", tipo=TipoSala.REGULAR, capacidade=30, turnos_disponiveis=["vespertino"], ativo=True)
    test_db.add_all([sala1_grande, sala1_peq, sala1_inativa, sala2_grande, sala2_peq])
    test_db.flush()

    # Cursos e disciplinas
    curso1 = Curso(campus_id=c1.id, nome="Computacao", codigo="CC")
    curso2 = Curso(campus_id=c2.id, nome="Engenharia", codigo="ENG")
    test_db.add_all([curso1, curso2])
    test_db.flush()

    disc1 = Disciplina(curso_id=curso1.id, nome="Algoritmos", codigo="CC101", carga_horaria=60)
    disc2 = Disciplina(curso_id=curso2.id, nome="Calculo", codigo="ENG101", carga_horaria=60)
    test_db.add_all([disc1, disc2])
    test_db.flush()

    # Campus 1: 2 turmas (matutino e noturno)
    turma1_mat = Turma(disciplina_id=disc1.id, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=25, turno_preferido=Turno.MATUTINO)
    turma1_not = Turma(disciplina_id=disc1.id, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=30, turno_preferido=Turno.NOTURNO)
    # Campus 2: 1 turma (vespertino)
    turma2_vesp = Turma(disciplina_id=disc2.id, professor_id=None, periodo_letivo="2026.1", num_matriculados=20, turno_preferido=Turno.VESPERTINO)
    test_db.add_all([turma1_mat, turma1_not, turma2_vesp])
    test_db.flush()

    # Campus 1: 3 horarios (2 na segunda-feira dia 1, 1 na quarta-feira dia 3)
    h1 = Horario(campus_id=c1.id, turma_id=turma1_mat.id, sala_id=sala1_peq.id, dia_semana=1, hora_inicio=time(8, 0), hora_fim=time(10, 0))
    h2 = Horario(campus_id=c1.id, turma_id=turma1_not.id, sala_id=sala1_grande.id, dia_semana=1, hora_inicio=time(19, 0), hora_fim=time(21, 0))
    h3 = Horario(campus_id=c1.id, turma_id=turma1_mat.id, sala_id=sala1_peq.id, dia_semana=3, hora_inicio=time(10, 0), hora_fim=time(12, 0))

    # Campus 2: 1 horario (terca-feira dia 2, vespertino)
    h4 = Horario(campus_id=c2.id, turma_id=turma2_vesp.id, sala_id=sala2_peq.id, dia_semana=2, hora_inicio=time(14, 0), hora_fim=time(16, 0))
    test_db.add_all([h1, h2, h3, h4])
    test_db.flush()

    # Sugestoes no Campus 1:
    # - 1 APROVADO: sala1_grande (80) -> sala1_peq (40) => 40 vagas recuperadas
    # - 1 PENDENTE: sala1_grande (80) -> sala1_peq (40) => nao entra em vagas recuperadas
    # - 1 REJEITADO: sala1_grande (80) -> sala1_peq (40) => nao entra em vagas recuperadas
    sug1_aprov = SugestaoRemanejamento(
        horario_id=h1.id,
        sala_atual_id=sala1_grande.id,
        sala_sugerida_id=sala1_peq.id,
        motivo="Aprovada campus 1",
        status=StatusSugestao.APROVADO,
        aprovado_por=coord1.id,
    )
    sug1_pend = SugestaoRemanejamento(
        horario_id=h2.id,
        sala_atual_id=sala1_grande.id,
        sala_sugerida_id=sala1_peq.id,
        motivo="Pendente campus 1",
        status=StatusSugestao.PENDENTE,
    )
    sug1_rej = SugestaoRemanejamento(
        horario_id=h3.id,
        sala_atual_id=sala1_grande.id,
        sala_sugerida_id=sala1_peq.id,
        motivo="Rejeitada campus 1",
        status=StatusSugestao.REJEITADO,
        aprovado_por=coord1.id,
    )

    # Sugestao no Campus 2:
    # - 1 APROVADO: sala2_grande (60) -> sala2_peq (30) => 30 vagas recuperadas
    sug2_aprov = SugestaoRemanejamento(
        horario_id=h4.id,
        sala_atual_id=sala2_grande.id,
        sala_sugerida_id=sala2_peq.id,
        motivo="Aprovada campus 2",
        status=StatusSugestao.APROVADO,
        aprovado_por=coord2.id,
    )
    test_db.add_all([sug1_aprov, sug1_pend, sug1_rej, sug2_aprov])
    test_db.flush()

    # Logs de operacao: 2 no Campus 1 e 1 no Campus 2
    base_ts = datetime(2026, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
    log1 = LogAlocacao(
        campus_id=c1.id,
        horario_id=h1.id,
        tipo_evento=TipoEventoLog.CRIACAO,
        usuario_responsavel=coord1.id,
        snapshot_evento={"entidade": "horario", "entidade_id": h1.id},
        detalhes="Alocacao h1",
        timestamp=base_ts - timedelta(hours=2),
    )
    log2 = LogAlocacao(
        campus_id=c1.id,
        horario_id=h1.id,
        tipo_evento=TipoEventoLog.REMANEJAMENTO,
        usuario_responsavel=coord1.id,
        snapshot_evento={"entidade": "sugestao", "entidade_id": sug1_aprov.id},
        detalhes="Remanejamento aprovado h1",
        timestamp=base_ts - timedelta(hours=1),
    )
    log3 = LogAlocacao(
        campus_id=c2.id,
        horario_id=h4.id,
        tipo_evento=TipoEventoLog.CRIACAO,
        usuario_responsavel=coord2.id,
        snapshot_evento={"entidade": "horario", "entidade_id": h4.id},
        detalhes="Alocacao h4 campus 2",
        timestamp=base_ts,
    )
    test_db.add_all([log1, log2, log3])
    test_db.commit()

    return {
        "c1": c1,
        "c2": c2,
        "admin": admin,
        "coord1": coord1,
        "sec1": sec1,
        "coord2": coord2,
        "prof": prof,
        "aluno": aluno,
        "log1": log1,
        "log2": log2,
        "log3": log3,
    }


def test_dashboard_resumo_coordenador_isolado_no_campus(client: TestClient, seed_dashboard: dict):
    """Coordenador do Campus 1 obtem apenas indicadores consolidados do Campus 1."""
    resp = client.get("/api/v1/dashboard/resumo", headers=auth_header(seed_dashboard["coord1"]))
    assert resp.status_code == 200
    data = resp.json()

    assert data["salas_ativas"] == 2
    assert data["turmas"] == 2
    assert data["horarios"] == 3
    assert data["sugestoes"] == {
        "pendente": 1,
        "aprovado": 1,
        "rejeitado": 1,
        "total": 3,
    }
    assert data["vagas_recuperadas"] == 40
    assert len(data["eventos_recentes"]) == 2
    # Ordem decrescente de timestamp: log2 antes de log1
    assert data["eventos_recentes"][0]["id"] == seed_dashboard["log2"].id
    assert data["eventos_recentes"][1]["id"] == seed_dashboard["log1"].id
    assert all(ev["campus_id"] == seed_dashboard["c1"].id for ev in data["eventos_recentes"])


def test_dashboard_resumo_secretaria_isolada_no_campus(client: TestClient, seed_dashboard: dict):
    """Secretaria do Campus 1 acessa o resumo restrito ao Campus 1 e ignora campus_id alheio."""
    c2 = seed_dashboard["c2"]
    resp = client.get(
        f"/api/v1/dashboard/resumo?campus_id={c2.id}",
        headers=auth_header(seed_dashboard["sec1"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["salas_ativas"] == 2
    assert data["turmas"] == 2
    assert data["horarios"] == 3
    assert data["vagas_recuperadas"] == 40


def test_dashboard_resumo_coordenador_ignora_campus_alheio(client: TestClient, seed_dashboard: dict):
    """Coordenador do Campus 1 passando ?campus_id=2 tem o filtro ignorado e recebe dados do Campus 1."""
    c2 = seed_dashboard["c2"]
    resp = client.get(
        f"/api/v1/dashboard/resumo?campus_id={c2.id}",
        headers=auth_header(seed_dashboard["coord1"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["salas_ativas"] == 2
    assert data["horarios"] == 3
    assert data["vagas_recuperadas"] == 40
    assert all(ev["campus_id"] == seed_dashboard["c1"].id for ev in data["eventos_recentes"])


def test_dashboard_resumo_admin_global_e_filtrado_por_campus(client: TestClient, seed_dashboard: dict):
    """Admin sem filtro ve somatorio global; com ?campus_id=2 ve apenas Campus 2."""
    headers = auth_header(seed_dashboard["admin"])
    c2 = seed_dashboard["c2"]

    # 1. Global (Campus 1 + Campus 2)
    resp_global = client.get("/api/v1/dashboard/resumo", headers=headers)
    assert resp_global.status_code == 200
    global_data = resp_global.json()
    assert global_data["salas_ativas"] == 4  # 2 no C1 + 2 no C2 (inativa ignorada)
    assert global_data["turmas"] == 3
    assert global_data["horarios"] == 4
    assert global_data["sugestoes"] == {
        "pendente": 1,
        "aprovado": 2,
        "rejeitado": 1,
        "total": 4,
    }
    assert global_data["vagas_recuperadas"] == 70  # 40 (C1) + 30 (C2)
    assert len(global_data["eventos_recentes"]) == 3

    # 2. Filtrado para Campus 2
    resp_c2 = client.get(f"/api/v1/dashboard/resumo?campus_id={c2.id}", headers=headers)
    assert resp_c2.status_code == 200
    c2_data = resp_c2.json()
    assert c2_data["salas_ativas"] == 2
    assert c2_data["turmas"] == 1
    assert c2_data["horarios"] == 1
    assert c2_data["sugestoes"] == {
        "pendente": 0,
        "aprovado": 1,
        "rejeitado": 0,
        "total": 1,
    }
    assert c2_data["vagas_recuperadas"] == 30
    assert len(c2_data["eventos_recentes"]) == 1
    assert c2_data["eventos_recentes"][0]["campus_id"] == c2.id


def test_dashboard_ocupacao_por_dia_semana_e_turno(client: TestClient, seed_dashboard: dict):
    """Verifica agregacao SQL de horarios por dia_semana (0..6) e por turno com isolamento."""
    # Coordenador do Campus 1: 2 horarios no dia 1 (matutino e noturno), 1 horario no dia 3 (matutino)
    resp_c1 = client.get("/api/v1/dashboard/ocupacao", headers=auth_header(seed_dashboard["coord1"]))
    assert resp_c1.status_code == 200
    data_c1 = resp_c1.json()

    dias_map = {item["dia_semana"]: item["total_horarios"] for item in data_c1["por_dia_semana"]}
    assert set(dias_map.keys()) == {0, 1, 2, 3, 4, 5, 6}
    assert dias_map[1] == 2
    assert dias_map[3] == 1
    assert dias_map[0] == 0
    assert dias_map[2] == 0

    turnos_map = {item["turno"]: item["total_horarios"] for item in data_c1["por_turno"]}
    assert turnos_map["matutino"] == 2
    assert turnos_map["noturno"] == 1
    assert turnos_map["vespertino"] == 0
    assert turnos_map["integral"] == 0

    # Coordenador do Campus 1 tentando ?campus_id=2 continua restrito ao Campus 1
    c2 = seed_dashboard["c2"]
    resp_tamper = client.get(
        f"/api/v1/dashboard/ocupacao?campus_id={c2.id}",
        headers=auth_header(seed_dashboard["coord1"]),
    )
    assert resp_tamper.status_code == 200
    dias_tamper = {item["dia_semana"]: item["total_horarios"] for item in resp_tamper.json()["por_dia_semana"]}
    assert dias_tamper[2] == 0
    assert dias_tamper[1] == 2

    # Admin consultando Campus 2: 1 horario no dia 2 (vespertino)
    resp_c2 = client.get(
        f"/api/v1/dashboard/ocupacao?campus_id={c2.id}",
        headers=auth_header(seed_dashboard["admin"]),
    )
    assert resp_c2.status_code == 200
    data_c2 = resp_c2.json()
    dias_c2 = {item["dia_semana"]: item["total_horarios"] for item in data_c2["por_dia_semana"]}
    turnos_c2 = {item["turno"]: item["total_horarios"] for item in data_c2["por_turno"]}
    assert dias_c2[2] == 1
    assert dias_c2[1] == 0
    assert turnos_c2["vespertino"] == 1
    assert turnos_c2["matutino"] == 0


def test_dashboard_rbac_perfis_sem_privilegio(client: TestClient, seed_dashboard: dict):
    """Professor e Aluno recebem 403 Forbidden; requisicao sem token recebe 401 Unauthorized."""
    for endpoint in ("/api/v1/dashboard/resumo", "/api/v1/dashboard/ocupacao"):
        assert client.get(endpoint).status_code == 401
        assert client.get(endpoint, headers=auth_header(seed_dashboard["prof"])).status_code == 403
        assert client.get(endpoint, headers=auth_header(seed_dashboard["aluno"])).status_code == 403


def test_dashboard_campus_vazio_retorna_zeros_sem_erro(client: TestClient, test_db: Session, seed_dashboard: dict):
    """Campus sem salas, turmas, horarios, sugestoes ou logs retorna 0 em todos os indicadores."""
    c_vazio = Campus(nome="Campus Vazio", cidade="Recife", endereco="Rua 0")
    test_db.add(c_vazio)
    test_db.commit()

    headers = auth_header(seed_dashboard["admin"])
    resp_resumo = client.get(f"/api/v1/dashboard/resumo?campus_id={c_vazio.id}", headers=headers)
    assert resp_resumo.status_code == 200
    resumo = resp_resumo.json()
    assert resumo["salas_ativas"] == 0
    assert resumo["turmas"] == 0
    assert resumo["horarios"] == 0
    assert resumo["vagas_recuperadas"] == 0
    assert resumo["sugestoes"] == {"pendente": 0, "aprovado": 0, "rejeitado": 0, "total": 0}
    assert resumo["eventos_recentes"] == []

    resp_ocup = client.get(f"/api/v1/dashboard/ocupacao?campus_id={c_vazio.id}", headers=headers)
    assert resp_ocup.status_code == 200
    ocup = resp_ocup.json()
    assert all(d["total_horarios"] == 0 for d in ocup["por_dia_semana"])
    assert all(t["total_horarios"] == 0 for t in ocup["por_turno"])


def test_dashboard_validacao_parametros_e_metodos_405_422(client: TestClient, seed_dashboard: dict):
    """campus_id <= 0 retorna 422; metodos de escrita (POST/PUT/PATCH/DELETE) retornam 405."""
    headers = auth_header(seed_dashboard["admin"])
    for endpoint in ("/api/v1/dashboard/resumo", "/api/v1/dashboard/ocupacao"):
        assert client.get(f"{endpoint}?campus_id=0", headers=headers).status_code == 422
        assert client.get(f"{endpoint}?campus_id=-5", headers=headers).status_code == 422
        assert client.post(endpoint, json={}, headers=headers).status_code == 405
        assert client.put(endpoint, json={}, headers=headers).status_code == 405
        assert client.patch(endpoint, json={}, headers=headers).status_code == 405
        assert client.delete(endpoint, headers=headers).status_code == 405


def test_dashboard_sem_queries_n_mais_1(client: TestClient, test_db: Session, seed_dashboard: dict):
    """Garante numero constante de queries SQL (sem N+1) ao consultar resumo e ocupacao."""
    from sqlalchemy import event

    queries: list[str] = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    engine = test_db.get_bind()
    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        headers = auth_header(seed_dashboard["admin"])
        queries.clear()
        resp_r = client.get("/api/v1/dashboard/resumo", headers=headers)
        assert resp_r.status_code == 200
        # 1 query auth + 6 queries fixas de agregacao/limite = 7 queries (constante O(1))
        assert len(queries) <= 8

        queries.clear()
        resp_o = client.get("/api/v1/dashboard/ocupacao", headers=headers)
        assert resp_o.status_code == 200
        # 1 query auth + 2 queries fixas group_by = 3 queries (constante O(1))
        assert len(queries) <= 4
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


def test_dashboard_vagas_recuperadas_ignora_capacidade_igual_ou_invertida(
    client: TestClient, test_db: Session, seed_dashboard: dict
):
    """Sugestao aprovada com sala_atual.capacidade <= sala_sugerida.capacidade nao subtrai vagas."""
    c1 = seed_dashboard["c1"]
    coord1 = seed_dashboard["coord1"]
    sala_peq = test_db.query(Sala).filter(Sala.campus_id == c1.id, Sala.capacidade == 40).first()
    sala_grande = test_db.query(Sala).filter(Sala.campus_id == c1.id, Sala.capacidade == 80).first()
    h1 = test_db.query(Horario).filter(Horario.campus_id == c1.id).first()

    sug_invertida = SugestaoRemanejamento(
        horario_id=h1.id,
        sala_atual_id=sala_peq.id,
        sala_sugerida_id=sala_grande.id,
        motivo="Anomalia capacidade invertida 40 -> 80",
        status=StatusSugestao.APROVADO,
        aprovado_por=coord1.id,
    )
    test_db.add(sug_invertida)
    test_db.commit()

    resp = client.get("/api/v1/dashboard/resumo", headers=auth_header(coord1))
    assert resp.status_code == 200
    data = resp.json()
    # Continua 40 (da sug1_aprov 80->40), sem subtrair -40 da sugestao invertida
    assert data["vagas_recuperadas"] == 40
    assert data["sugestoes"]["aprovado"] == 2


