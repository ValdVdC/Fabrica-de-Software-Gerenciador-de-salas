"""
Testes de integracao TDD para Relatorios e Exportacao CSV (Sprint 07 - Historias 2 e 4):
- GET /api/v1/relatorios/ocupacao-salas (JSON e CSV)
- GET /api/v1/relatorios/remanejamentos (JSON e CSV)
- GET /api/v1/logs?formato=csv

Cobre:
- Colunas e calculo de taxa de ocupacao semanal de salas
- Filtros de remanejamentos por status, data_inicio, data_fim e campus_id
- Validacao 422 quando data_fim < data_inicio
- Lista vazia 200 OK quando filtro nao encontra registros
- Isolamento multi-campus (BOLA/IDOR) para coordenador e secretaria
- RBAC (403 para professor e aluno, 401 para nao autenticado, 405 para escrita)
- Exportacao CSV com UTF-8 BOM, sanitizacao de CSV injection e respeito aos filtros
- Ausencia de queries N+1
"""

import csv
import io
from datetime import datetime, timezone, time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
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
    """Banco SQLite em memoria isolado para os testes de relatorios."""
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
    """TestClient do FastAPI com sessao de banco de testes injetada."""
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
def seed_relatorios(test_db: Session):
    """Semeia dois campi com salas, turmas, horarios, sugestoes e logs para relatorios."""
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

    # Campus 1:
    # - sala1_a: 2 turnos disponiveis (10 slots semanais), recebera 2 horarios => 20.0%
    # - sala1_b: 1 turno disponivel (5 slots semanais), recebera 1 horario => 20.0%
    # - sala1_lab: 2 turnos disponiveis (10 slots semanais), 0 horarios => 0.0%
    sala1_a = Sala(
        campus_id=c1.id,
        bloco="A",
        numero="101",
        tipo=TipoSala.REGULAR,
        capacidade=80,
        turnos_disponiveis=["matutino", "noturno"],
        ativo=True,
    )
    sala1_b = Sala(
        campus_id=c1.id,
        bloco="A",
        numero="102",
        tipo=TipoSala.REGULAR,
        capacidade=40,
        turnos_disponiveis=["matutino"],
        ativo=True,
    )
    sala1_lab = Sala(
        campus_id=c1.id,
        bloco="B",
        numero="201",
        tipo=TipoSala.LABORATORIO,
        capacidade=30,
        turnos_disponiveis=["matutino", "vespertino"],
        ativo=True,
    )

    # Campus 2:
    # - sala2_a: 1 turno disponivel (5 slots semanais), recebera 1 horario => 20.0%
    sala2_a = Sala(
        campus_id=c2.id,
        bloco="C",
        numero="301",
        tipo=TipoSala.AUDITORIO,
        capacidade=100,
        turnos_disponiveis=["vespertino"],
        ativo=True,
    )
    sala2_b = Sala(
        campus_id=c2.id,
        bloco="C",
        numero="302",
        tipo=TipoSala.REGULAR,
        capacidade=45,
        turnos_disponiveis=["vespertino"],
        ativo=True,
    )
    test_db.add_all([sala1_a, sala1_b, sala1_lab, sala2_a, sala2_b])
    test_db.flush()

    curso1 = Curso(campus_id=c1.id, nome="Computacao", codigo="CC")
    curso2 = Curso(campus_id=c2.id, nome="Engenharia", codigo="ENG")
    test_db.add_all([curso1, curso2])
    test_db.flush()

    disc1 = Disciplina(curso_id=curso1.id, nome="Algoritmos", codigo="CC101", carga_horaria=60)
    disc2 = Disciplina(curso_id=curso2.id, nome="Calculo", codigo="ENG101", carga_horaria=60)
    test_db.add_all([disc1, disc2])
    test_db.flush()

    t1 = Turma(disciplina_id=disc1.id, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=30, turno_preferido=Turno.MATUTINO)
    t2 = Turma(disciplina_id=disc2.id, professor_id=None, periodo_letivo="2026.1", num_matriculados=25, turno_preferido=Turno.VESPERTINO)
    test_db.add_all([t1, t2])
    test_db.flush()

    h1 = Horario(campus_id=c1.id, turma_id=t1.id, sala_id=sala1_a.id, dia_semana=1, hora_inicio=time(8, 0), hora_fim=time(10, 0))
    h2 = Horario(campus_id=c1.id, turma_id=t1.id, sala_id=sala1_a.id, dia_semana=3, hora_inicio=time(8, 0), hora_fim=time(10, 0))
    h3 = Horario(campus_id=c1.id, turma_id=t1.id, sala_id=sala1_b.id, dia_semana=2, hora_inicio=time(10, 0), hora_fim=time(12, 0))
    h4 = Horario(campus_id=c2.id, turma_id=t2.id, sala_id=sala2_a.id, dia_semana=4, hora_inicio=time(14, 0), hora_fim=time(16, 0))
    test_db.add_all([h1, h2, h3, h4])
    test_db.flush()

    dt_outubro = datetime(2026, 10, 15, 14, 0, 0, tzinfo=timezone.utc)
    dt_setembro = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)

    sug_aprov_out = SugestaoRemanejamento(
        horario_id=h1.id,
        sala_atual_id=sala1_a.id,
        sala_sugerida_id=sala1_b.id,
        motivo="Ociosidade 50% em outubro",
        justificativa="Aprovado pela coordenacao",
        status=StatusSugestao.APROVADO,
        aprovado_por=coord1.id,
        criado_em=dt_outubro,
        atualizado_em=dt_outubro,
    )
    sug_pend_out = SugestaoRemanejamento(
        horario_id=h2.id,
        sala_atual_id=sala1_a.id,
        sala_sugerida_id=sala1_lab.id,
        motivo="=SUM(1,2) motivo com formula",
        status=StatusSugestao.PENDENTE,
        aprovado_por=None,
        criado_em=dt_outubro,
        atualizado_em=dt_outubro,
    )
    sug_aprov_set = SugestaoRemanejamento(
        horario_id=h3.id,
        sala_atual_id=sala1_a.id,
        sala_sugerida_id=sala1_b.id,
        motivo="Remanejamento de setembro",
        status=StatusSugestao.APROVADO,
        aprovado_por=coord1.id,
        criado_em=dt_setembro,
        atualizado_em=dt_setembro,
    )
    sug_c2 = SugestaoRemanejamento(
        horario_id=h4.id,
        sala_atual_id=sala2_a.id,
        sala_sugerida_id=sala2_b.id,
        motivo="Remanejamento campus 2",
        status=StatusSugestao.APROVADO,
        aprovado_por=coord2.id,
        criado_em=dt_outubro,
        atualizado_em=dt_outubro,
    )
    test_db.add_all([sug_aprov_out, sug_pend_out, sug_aprov_set, sug_c2])
    test_db.flush()

    log1 = LogAlocacao(
        campus_id=c1.id,
        horario_id=h1.id,
        tipo_evento=TipoEventoLog.REMANEJAMENTO,
        usuario_responsavel=coord1.id,
        snapshot_evento={"entidade": "sugestao", "entidade_id": sug_aprov_out.id},
        detalhes="=CMD|' /C calc'!A0 log suspeito",
        timestamp=dt_outubro,
    )
    log2 = LogAlocacao(
        campus_id=c2.id,
        horario_id=h4.id,
        tipo_evento=TipoEventoLog.CRIACAO,
        usuario_responsavel=coord2.id,
        snapshot_evento={"entidade": "horario", "entidade_id": h4.id},
        detalhes="Log campus 2",
        timestamp=dt_outubro,
    )
    test_db.add_all([log1, log2])
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
        "sala1_a": sala1_a,
        "sala1_b": sala1_b,
        "sala1_lab": sala1_lab,
        "sug_aprov_out": sug_aprov_out,
        "sug_pend_out": sug_pend_out,
        "sug_aprov_set": sug_aprov_set,
        "sug_c2": sug_c2,
    }


def test_relatorio_ocupacao_salas_json_e_isolamento_campus(client: TestClient, seed_relatorios: dict):
    """Retorna ocupacao semanal por sala do campus com isolamento multi-tenant."""
    resp = client.get(
        "/api/v1/relatorios/ocupacao-salas",
        headers=auth_header(seed_relatorios["sec1"]),
    )
    assert resp.status_code == 200
    dados = resp.json()
    assert len(dados) == 3
    assert all(item["campus_id"] == seed_relatorios["c1"].id for item in dados)

    por_sala = {item["sala"]: item for item in dados}
    assert "A-101" in por_sala
    assert por_sala["A-101"]["bloco"] == "A"
    assert por_sala["A-101"]["capacidade"] == 80
    assert por_sala["A-101"]["tipo"] == "regular"
    assert por_sala["A-101"]["quantidade_horarios"] == 2
    assert por_sala["A-101"]["taxa_ocupacao_semanal"] == 20.0

    assert por_sala["A-102"]["quantidade_horarios"] == 1
    assert por_sala["A-102"]["taxa_ocupacao_semanal"] == 20.0

    assert por_sala["B-201"]["quantidade_horarios"] == 0
    assert por_sala["B-201"]["taxa_ocupacao_semanal"] == 0.0

    # Tentativa de BOLA: coordenador do Campus 1 passando campus_id=2 continua restrito ao Campus 1
    c2 = seed_relatorios["c2"]
    resp_bola = client.get(
        f"/api/v1/relatorios/ocupacao-salas?campus_id={c2.id}",
        headers=auth_header(seed_relatorios["coord1"]),
    )
    assert resp_bola.status_code == 200
    assert all(item["campus_id"] == seed_relatorios["c1"].id for item in resp_bola.json())


def test_relatorio_ocupacao_salas_filtros_bloco_tipo_e_vazio(client: TestClient, seed_relatorios: dict):
    """Filtra ocupacao de salas por bloco e tipo; retorna 200 [] quando vazio."""
    headers = auth_header(seed_relatorios["coord1"])

    resp_lab = client.get("/api/v1/relatorios/ocupacao-salas?tipo=laboratorio", headers=headers)
    assert resp_lab.status_code == 200
    dados_lab = resp_lab.json()
    assert len(dados_lab) == 1
    assert dados_lab[0]["sala"] == "B-201"

    resp_bloco = client.get("/api/v1/relatorios/ocupacao-salas?bloco=A", headers=headers)
    assert resp_bloco.status_code == 200
    assert len(resp_bloco.json()) == 2

    resp_vazio = client.get("/api/v1/relatorios/ocupacao-salas?bloco=INEXISTENTE", headers=headers)
    assert resp_vazio.status_code == 200
    assert resp_vazio.json() == []


def test_relatorio_remanejamentos_filtrado_status_e_periodo(client: TestClient, seed_relatorios: dict):
    """Filtra remanejamentos por status e intervalo de datas, retornando sala origem, destino e decisor."""
    headers = auth_header(seed_relatorios["coord1"])
    resp = client.get(
        "/api/v1/relatorios/remanejamentos?status=aprovado&data_inicio=2026-10-01&data_fim=2026-10-31",
        headers=headers,
    )
    assert resp.status_code == 200
    dados = resp.json()
    assert len(dados) == 1

    item = dados[0]
    assert item["id"] == seed_relatorios["sug_aprov_out"].id
    assert item["status"] == "aprovado"
    assert item["sala_origem"] == "A-101"
    assert item["sala_destino"] == "A-102"
    assert item["decisor"] == "Coord Alpha"
    assert item["campus_id"] == seed_relatorios["c1"].id

    # Filtro sem resultados retorna 200 OK com lista vazia
    resp_vazio = client.get(
        "/api/v1/relatorios/remanejamentos?status=rejeitado",
        headers=headers,
    )
    assert resp_vazio.status_code == 200
    assert resp_vazio.json() == []


def test_relatorio_remanejamentos_periodo_invalido_retorna_422(client: TestClient, seed_relatorios: dict):
    """Retorna 422 Unprocessable Entity quando data_fim < data_inicio."""
    headers = auth_header(seed_relatorios["coord1"])
    resp = client.get(
        "/api/v1/relatorios/remanejamentos?data_inicio=2026-10-31&data_fim=2026-10-01",
        headers=headers,
    )
    assert resp.status_code == 422
    assert "data_fim" in resp.json()["detail"].lower()


def test_exportacao_csv_relatorios_e_logs(client: TestClient, seed_relatorios: dict):
    """Testa exportacao CSV em /relatorios/ocupacao-salas, /relatorios/remanejamentos e /logs."""
    headers = auth_header(seed_relatorios["sec1"])

    # 1. CSV de ocupacao de salas
    resp_ocup = client.get("/api/v1/relatorios/ocupacao-salas?formato=csv&bloco=A", headers=headers)
    assert resp_ocup.status_code == 200
    assert "text/csv" in resp_ocup.headers["content-type"]
    assert "charset=utf-8" in resp_ocup.headers["content-type"]
    assert ".csv" in resp_ocup.headers["content-disposition"]
    assert resp_ocup.content.startswith(b"\xef\xbb\xbf")

    linhas_ocup = list(csv.DictReader(io.StringIO(resp_ocup.content.decode("utf-8-sig"))))
    assert len(linhas_ocup) == 2
    assert linhas_ocup[0]["sala"] == "A-101"
    assert linhas_ocup[0]["taxa_ocupacao_semanal"] == "20.0"

    # 2. CSV de remanejamentos (verifica sanitizacao de CSV injection no motivo)
    resp_rem = client.get("/api/v1/relatorios/remanejamentos?formato=csv", headers=headers)
    assert resp_rem.status_code == 200
    assert resp_rem.content.startswith(b"\xef\xbb\xbf")
    linhas_rem = list(csv.DictReader(io.StringIO(resp_rem.content.decode("utf-8-sig"))))
    # Apenas os 23 registros do Campus 1 (3 no seed: sug_aprov_out, sug_pend_out, sug_aprov_set)
    assert len(linhas_rem) == 3
    motivos = [r["motivo"] for r in linhas_rem]
    assert "'=SUM(1,2) motivo com formula" in motivos

    # 3. CSV de logs (verifica isolamento de campus e sanitizacao de CSV injection em detalhes)
    resp_logs = client.get("/api/v1/logs?formato=csv", headers=headers)
    assert resp_logs.status_code == 200
    assert "text/csv" in resp_logs.headers["content-type"]
    assert ".csv" in resp_logs.headers["content-disposition"]
    assert resp_logs.content.startswith(b"\xef\xbb\xbf")
    linhas_logs = list(csv.DictReader(io.StringIO(resp_logs.content.decode("utf-8-sig"))))
    assert len(linhas_logs) == 1
    assert linhas_logs[0]["detalhes"] == "'=CMD|' /C calc'!A0 log suspeito"


def test_relatorios_rbac_e_metodos_405(client: TestClient, seed_relatorios: dict):
    """Professor e Aluno recebem 403; anonimo recebe 401; metodos de escrita recebem 405."""
    headers_admin = auth_header(seed_relatorios["admin"])
    for rota in ("/api/v1/relatorios/ocupacao-salas", "/api/v1/relatorios/remanejamentos"):
        assert client.get(rota).status_code == 401
        assert client.get(rota, headers=auth_header(seed_relatorios["prof"])).status_code == 403
        assert client.get(rota, headers=auth_header(seed_relatorios["aluno"])).status_code == 403
        assert client.post(rota, json={}, headers=headers_admin).status_code == 405
        assert client.put(rota, json={}, headers=headers_admin).status_code == 405
        assert client.patch(rota, json={}, headers=headers_admin).status_code == 405
        assert client.delete(rota, headers=headers_admin).status_code == 405


def test_relatorios_sem_queries_n_mais_1(client: TestClient, test_db: Session, seed_relatorios: dict):
    """Garante que os endpoints de relatorios executam numero constante O(1) de queries SQL."""
    queries: list[str] = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    engine = test_db.get_bind()
    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        headers = auth_header(seed_relatorios["admin"])
        queries.clear()
        assert client.get("/api/v1/relatorios/ocupacao-salas", headers=headers).status_code == 200
        assert len(queries) <= 3

        queries.clear()
        assert client.get("/api/v1/relatorios/remanejamentos", headers=headers).status_code == 200
        assert len(queries) <= 3
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


def test_relatorios_admin_filtro_campus_e_data_igual(client: TestClient, seed_relatorios: dict):
    """Admin pode filtrar por campus_id especifico e data_inicio == data_fim retorna registros do dia."""
    headers = auth_header(seed_relatorios["admin"])
    c2 = seed_relatorios["c2"]

    resp_ocup = client.get(f"/api/v1/relatorios/ocupacao-salas?campus_id={c2.id}", headers=headers)
    assert resp_ocup.status_code == 200
    assert len(resp_ocup.json()) == 2
    assert all(r["campus_id"] == c2.id for r in resp_ocup.json())

    resp_rem = client.get(
        f"/api/v1/relatorios/remanejamentos?campus_id={c2.id}&data_inicio=2026-10-15&data_fim=2026-10-15",
        headers=headers,
    )
    assert resp_rem.status_code == 200
    assert len(resp_rem.json()) == 1
    assert resp_rem.json()[0]["id"] == seed_relatorios["sug_c2"].id


def test_relatorios_formato_e_paginacao_invalidos_retornam_422(client: TestClient, seed_relatorios: dict):
    """Formatos nao suportados (pdf, xlsx) e parametros de paginacao fora dos limites retornam 422."""
    headers = auth_header(seed_relatorios["admin"])
    for rota in ("/api/v1/relatorios/ocupacao-salas", "/api/v1/relatorios/remanejamentos", "/api/v1/logs"):
        assert client.get(f"{rota}?formato=pdf", headers=headers).status_code == 422
        assert client.get(f"{rota}?formato=xlsx", headers=headers).status_code == 422
        assert client.get(f"{rota}?campus_id=0", headers=headers).status_code == 422
        assert client.get(f"{rota}?skip=-1", headers=headers).status_code == 422
        assert client.get(f"{rota}?limit=101", headers=headers).status_code == 422


def test_bordas_taxa_ocupacao_e_csv_injection_ocupacao(client: TestClient, test_db: Session, seed_relatorios: dict):
    """Valida fallback de turnos vazios, teto de 100% na taxa de ocupacao e sanitizacao CSV em salas."""
    from app.services.relatorio_service import _calcular_taxa_ocupacao_semanal

    # Fallback para 3 turnos (15 slots semanais): 3 horarios => 20.0%
    assert _calcular_taxa_ocupacao_semanal([], 3) == 20.0
    assert _calcular_taxa_ocupacao_semanal(None, 3) == 20.0
    # Teto maximo de 100.0% quando quantidade_horarios > slots_semanais
    assert _calcular_taxa_ocupacao_semanal(["matutino"], 12) == 100.0

    # Sala com bloco iniciando por caractere de formula (=) e sanitizada no CSV
    c1 = seed_relatorios["c1"]
    sala_formula = Sala(
        campus_id=c1.id,
        bloco="=EVIL",
        numero="+999",
        tipo=TipoSala.REGULAR,
        capacidade=25,
        turnos_disponiveis=[],
        ativo=True,
    )
    test_db.add(sala_formula)
    test_db.commit()

    resp = client.get(
        "/api/v1/relatorios/ocupacao-salas?formato=csv&bloco==EVIL",
        headers=auth_header(seed_relatorios["sec1"]),
    )
    assert resp.status_code == 200
    linhas = list(csv.DictReader(io.StringIO(resp.content.decode("utf-8-sig"))))
    assert len(linhas) == 1
    assert linhas[0]["bloco"] == "'=EVIL"
    assert linhas[0]["numero"] == "'+999"
    assert linhas[0]["sala"] == "'=EVIL-+999"



