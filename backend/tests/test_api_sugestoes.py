"""
Testes automatizados TDD para endpoints de Sugestoes de Remanejamento e IA Preditiva (Sprint 06).
Cobre RBAC, BOLA/IDOR, atomicidade transacional, trilha de auditoria e conflitos de horario.
"""

from datetime import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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
    """Banco SQLite em memoria isolado para testes de API."""
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
def client(test_db):
    """TestClient do FastAPI com injecao de sessao de banco controlada."""
    def override_get_db():
        yield test_db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def seed_dados_sugestoes(test_db: Session):
    """Configura ambiente multi-campus completo com usuarios, salas, horarios e sugestoes."""
    senha_hash = get_password_hash("senha123")

    c1 = Campus(nome="Campus Alpha", cidade="Alpha City", endereco="Rua A, 1")
    c2 = Campus(nome="Campus Beta", cidade="Beta City", endereco="Rua B, 2")
    test_db.add_all([c1, c2])
    test_db.flush()

    admin = Usuario(campus_id=c1.id, nome="Admin Master", email="admin@test.com", senha_hash=senha_hash, perfil=PerfilUsuario.ADMIN)
    coord_c1 = Usuario(campus_id=c1.id, nome="Coord Alpha", email="coord1@test.com", senha_hash=senha_hash, perfil=PerfilUsuario.COORDENADOR)
    coord_c2 = Usuario(campus_id=c2.id, nome="Coord Beta", email="coord2@test.com", senha_hash=senha_hash, perfil=PerfilUsuario.COORDENADOR)
    prof = Usuario(campus_id=c1.id, nome="Prof Alpha", email="prof@test.com", senha_hash=senha_hash, perfil=PerfilUsuario.PROFESSOR)
    aluno = Usuario(campus_id=c1.id, nome="Aluno Alpha", email="aluno@test.com", senha_hash=senha_hash, perfil=PerfilUsuario.ALUNO)
    test_db.add_all([admin, coord_c1, coord_c2, prof, aluno])
    test_db.flush()

    # Salas no Campus 1
    sala_grande_c1 = Sala(campus_id=c1.id, bloco="A", numero="101", tipo=TipoSala.REGULAR, capacidade=100, turnos_disponiveis=["matutino", "noturno"], ativo=True)
    sala_menor_c1 = Sala(campus_id=c1.id, bloco="A", numero="102", tipo=TipoSala.REGULAR, capacidade=30, turnos_disponiveis=["matutino", "noturno"], ativo=True)
    # Sala no Campus 2
    sala_c2 = Sala(campus_id=c2.id, bloco="B", numero="201", tipo=TipoSala.REGULAR, capacidade=80, turnos_disponiveis=["matutino", "noturno"], ativo=True)
    sala_menor_c2 = Sala(campus_id=c2.id, bloco="B", numero="202", tipo=TipoSala.REGULAR, capacidade=25, turnos_disponiveis=["matutino", "noturno"], ativo=True)
    test_db.add_all([sala_grande_c1, sala_menor_c1, sala_c2, sala_menor_c2])
    test_db.flush()

    curso1 = Curso(campus_id=c1.id, nome="Computacao", codigo="CC")
    curso2 = Curso(campus_id=c2.id, nome="Engenharia", codigo="ENG")
    test_db.add_all([curso1, curso2])
    test_db.flush()

    disc1 = Disciplina(curso_id=curso1.id, nome="Algoritmos", codigo="CC101", carga_horaria=60)
    disc2 = Disciplina(curso_id=curso2.id, nome="Calculo", codigo="ENG101", carga_horaria=60)
    test_db.add_all([disc1, disc2])
    test_db.flush()

    turma1 = Turma(disciplina_id=disc1.id, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=20, turno_preferido=Turno.NOTURNO)
    turma2 = Turma(disciplina_id=disc2.id, professor_id=prof.id, periodo_letivo="2026.1", num_matriculados=20, turno_preferido=Turno.NOTURNO)
    test_db.add_all([turma1, turma2])
    test_db.flush()

    horario_c1 = Horario(
        campus_id=c1.id, turma_id=turma1.id, sala_id=sala_grande_c1.id,
        dia_semana=4, hora_inicio=time(19, 0), hora_fim=time(21, 0)
    )
    horario_c2 = Horario(
        campus_id=c2.id, turma_id=turma2.id, sala_id=sala_c2.id,
        dia_semana=4, hora_inicio=time(19, 0), hora_fim=time(21, 0)
    )
    test_db.add_all([horario_c1, horario_c2])
    test_db.flush()

    # Sugestoes pendentes (uma para c1 e uma para c2)
    sug_c1 = SugestaoRemanejamento(
        horario_id=horario_c1.id,
        sala_atual_id=sala_grande_c1.id,
        sala_sugerida_id=sala_menor_c1.id,
        motivo="Ociosidade estimada de 75%",
        status=StatusSugestao.PENDENTE,
    )
    sug_c2 = SugestaoRemanejamento(
        horario_id=horario_c2.id,
        sala_atual_id=sala_c2.id,
        sala_sugerida_id=sala_menor_c2.id,
        motivo="Ociosidade estimada de 68%",
        status=StatusSugestao.PENDENTE,
    )
    test_db.add_all([sug_c1, sug_c2])
    test_db.commit()

    return {
        "admin": admin,
        "coord_c1": coord_c1,
        "coord_c2": coord_c2,
        "prof": prof,
        "aluno": aluno,
        "c1": c1,
        "c2": c2,
        "sala_grande_c1": sala_grande_c1,
        "sala_menor_c1": sala_menor_c1,
        "horario_c1": horario_c1,
        "sug_c1": sug_c1,
        "sug_c2": sug_c2,
    }


def auth_header(user: Usuario) -> dict:
    """Gera header de autorizacao JWT para o usuario."""
    token = create_access_token(data={"sub": str(user.id), "perfil": user.perfil.value, "campus_id": user.campus_id})
    return {"Authorization": f"Bearer {token}"}


def test_listar_sugestoes_admin_retorna_todos(client, seed_dados_sugestoes):
    """Admin deve conseguir visualizar sugestoes de todos os campi."""
    headers = auth_header(seed_dados_sugestoes["admin"])
    resp = client.get("/api/v1/sugestoes", headers=headers)
    assert resp.status_code == 200
    dados = resp.json()
    assert len(dados) == 2


def test_listar_sugestoes_coordenador_isolamento_multi_campus_bola(client, seed_dados_sugestoes):
    """Coordenador do Campus 1 so deve visualizar sugestoes pertencentes ao Campus 1."""
    headers = auth_header(seed_dados_sugestoes["coord_c1"])
    resp = client.get("/api/v1/sugestoes", headers=headers)
    assert resp.status_code == 200
    dados = resp.json()
    assert len(dados) == 1
    assert dados[0]["id"] == seed_dados_sugestoes["sug_c1"].id
    assert dados[0]["campus_id"] == seed_dados_sugestoes["c1"].id


def test_listar_sugestoes_filtro_status(client, seed_dados_sugestoes):
    """Filtro por status deve retornar apenas os registros correspondentes."""
    headers = auth_header(seed_dados_sugestoes["admin"])
    resp = client.get("/api/v1/sugestoes?status=aprovado", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    resp_pendente = client.get("/api/v1/sugestoes?status=pendente", headers=headers)
    assert resp_pendente.status_code == 200
    assert len(resp_pendente.json()) == 2


def test_rbac_bloqueio_professor_e_aluno_em_sugestoes(client, seed_dados_sugestoes):
    """Perfis docentes e discentes nao podem acessar endpoints de sugestao."""
    for usr_key in ["prof", "aluno"]:
        headers = auth_header(seed_dados_sugestoes[usr_key])
        resp = client.get("/api/v1/sugestoes", headers=headers)
        assert resp.status_code == 403

        resp_post = client.post("/api/v1/ia/analisar", headers=headers, json={})
        assert resp_post.status_code == 403

        resp_patch = client.patch(
            f"/api/v1/sugestoes/{seed_dados_sugestoes['sug_c1'].id}",
            headers=headers,
            json={"status": "aprovado"}
        )
        assert resp_patch.status_code == 403


def test_disparar_analise_ia_coordenador_e_admin(client, seed_dados_sugestoes):
    """Valida disparo de analise preditiva via POST /api/v1/ia/analisar."""
    headers = auth_header(seed_dados_sugestoes["coord_c1"])
    resp = client.post("/api/v1/ia/analisar", headers=headers, json={"limiar_ociosidade": 0.30})
    assert resp.status_code == 200
    dados = resp.json()
    assert "total_turmas_analisadas" in dados
    assert "tempo_processamento_ms" in dados


def test_aprovar_sugestao_sucesso_atomicidade_e_auditoria(client, test_db, seed_dados_sugestoes):
    """
    Aprovacao com sucesso deve:
    1. Atualizar status da sugestao para 'aprovado'
    2. Atualizar atomicamente a sala do horario
    3. Criar registro de auditoria na tabela log_alocacao com tipo 'alteracao'
    """
    sug = seed_dados_sugestoes["sug_c1"]
    horario = seed_dados_sugestoes["horario_c1"]
    sala_menor = seed_dados_sugestoes["sala_menor_c1"]
    coord = seed_dados_sugestoes["coord_c1"]

    headers = auth_header(coord)
    payload = {"status": "aprovado", "justificativa": "Sala otimizada com sucesso"}
    resp = client.patch(f"/api/v1/sugestoes/{sug.id}", headers=headers, json=payload)
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["status"] == "aprovado"
    assert dados["aprovado_por"] == coord.id
    assert dados["justificativa"] == "Sala otimizada com sucesso"

    # Confere no banco de dados
    test_db.refresh(horario)
    assert horario.sala_id == sala_menor.id

    # Confere criacao do log de auditoria
    logs = test_db.scalars(
        select(LogAlocacao).where(LogAlocacao.horario_id == horario.id)
    ).all()
    assert len(logs) >= 1
    log_recente = logs[-1]
    assert log_recente.tipo_evento == TipoEventoLog.ALTERACAO
    assert log_recente.usuario_responsavel == coord.id
    assert log_recente.snapshot_evento["nova_sala_id"] == sala_menor.id


def test_rejeitar_sugestao_nao_altera_horario(client, test_db, seed_dados_sugestoes):
    """Rejeicao humana deve marcar status como 'rejeitado' e manter horario inalterado."""
    sug = seed_dados_sugestoes["sug_c1"]
    horario = seed_dados_sugestoes["horario_c1"]
    sala_original_id = horario.sala_id
    coord = seed_dados_sugestoes["coord_c1"]

    headers = auth_header(coord)
    payload = {"status": "rejeitado", "justificativa": "Turma prefere manter auditorio"}
    resp = client.patch(f"/api/v1/sugestoes/{sug.id}", headers=headers, json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejeitado"

    test_db.refresh(horario)
    assert horario.sala_id == sala_original_id


def test_aprovar_sugestao_ja_processada_retorna_400(client, seed_dados_sugestoes):
    """Tentativa de aprovar sugestao ja finalizada deve falhar com HTTP 400 Bad Request."""
    sug = seed_dados_sugestoes["sug_c1"]
    headers = auth_header(seed_dados_sugestoes["coord_c1"])

    # Primeira aprovacao
    resp1 = client.patch(f"/api/v1/sugestoes/{sug.id}", headers=headers, json={"status": "aprovado"})
    assert resp1.status_code == 200

    # Segunda tentativa
    resp2 = client.patch(f"/api/v1/sugestoes/{sug.id}", headers=headers, json={"status": "aprovado"})
    assert resp2.status_code == 400
    assert "ja foi processada" in resp2.json()["detail"]


def test_conflito_horario_ao_aprovar_retorna_409(client, test_db, seed_dados_sugestoes):
    """Se a sala sugerida foi ocupada por outra turma entre a geracao e a aprovacao, retorna 409."""
    sug = seed_dados_sugestoes["sug_c1"]
    horario = seed_dados_sugestoes["horario_c1"]
    sala_menor = seed_dados_sugestoes["sala_menor_c1"]

    # Cria ocupacao concorrente na sala menor
    outro_horario = Horario(
        campus_id=seed_dados_sugestoes["c1"].id,
        turma_id=horario.turma_id,
        sala_id=sala_menor.id,
        dia_semana=horario.dia_semana,
        hora_inicio=horario.hora_inicio,
        hora_fim=horario.hora_fim,
    )
    test_db.add(outro_horario)
    test_db.commit()

    headers = auth_header(seed_dados_sugestoes["coord_c1"])
    resp = client.patch(f"/api/v1/sugestoes/{sug.id}", headers=headers, json={"status": "aprovado"})
    assert resp.status_code == 409
    assert "nao esta mais disponivel" in resp.json()["detail"]


def test_coordenador_campus_alheio_patch_retorna_404_bola(client, seed_dados_sugestoes):
    """Coordenador do Campus 1 tentando aprovar sugestao do Campus 2 recebe 404 (BOLA/IDOR mitigado)."""
    sug_c2 = seed_dados_sugestoes["sug_c2"]
    headers_coord_c1 = auth_header(seed_dados_sugestoes["coord_c1"])

    resp = client.patch(f"/api/v1/sugestoes/{sug_c2.id}", headers=headers_coord_c1, json={"status": "aprovado"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Sugestao nao encontrada"
