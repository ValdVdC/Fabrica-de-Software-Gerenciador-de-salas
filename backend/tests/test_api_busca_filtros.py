"""Testes TDD para pesquisa textual (q) e filtros combinados (Sprint 07 - Historia 3)."""

from datetime import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.session import Base, get_db
from app.main import app as fastapi_app
from app.models import Campus, Curso, Disciplina, Horario, PerfilUsuario, Sala, TipoSala, Turma, Turno, Usuario


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(test_db: Session):
    def override_get_db():
        yield test_db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


def auth_headers(user: Usuario) -> dict[str, str]:
    token = create_access_token(
        {"sub": str(user.id), "perfil": user.perfil.value, "campus_id": user.campus_id}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def cenario(test_db: Session):
    senha = get_password_hash("SenhaForte123")
    c1 = Campus(nome="Campus Norte", cidade="Teresina", endereco="Av 1")
    c2 = Campus(nome="Campus Sul", cidade="Picos", endereco="Av 2")
    test_db.add_all([c1, c2])
    test_db.flush()

    admin = Usuario(campus_id=c1.id, nome="Admin Geral", email="admin@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ADMIN)
    coord1 = Usuario(campus_id=c1.id, nome="Helena Costa", email="helena_costa@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR)
    sec1 = Usuario(campus_id=c1.id, nome="Marcos 100% Ativo", email="marcos@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.SECRETARIA)
    prof1 = Usuario(campus_id=c1.id, nome="Professor Silva", email="silva@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR)
    aluno1 = Usuario(campus_id=c1.id, nome="Aluno Joao", email="joao@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO)
    coord2 = Usuario(campus_id=c2.id, nome="Helena Outro Campus", email="helena.sul@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR)
    test_db.add_all([admin, coord1, sec1, prof1, aluno1, coord2])
    test_db.flush()

    s_lab = Sala(campus_id=c1.id, bloco="Lab", numero="101", tipo=TipoSala.LABORATORIO, capacidade=40, turnos_disponiveis=["matutino", "noturno"])
    s_num_lab = Sala(campus_id=c1.id, bloco="Bloco A", numero="LAB-202", tipo=TipoSala.LABORATORIO, capacidade=35, turnos_disponiveis=["noturno"])
    s_reg = Sala(campus_id=c1.id, bloco="Bloco B", numero="301", tipo=TipoSala.REGULAR, capacidade=50, turnos_disponiveis=["matutino", "vespertino", "noturno"])
    s_pct = Sala(campus_id=c1.id, bloco="Bloco C", numero="100% Digital", tipo=TipoSala.AUDITORIO, capacidade=100, turnos_disponiveis=["integral"])
    s_und = Sala(campus_id=c1.id, bloco="Bloco D", numero="Sala_Especial", tipo=TipoSala.REUNIAO, capacidade=20, turnos_disponiveis=["vespertino"])
    s_bar = Sala(campus_id=c1.id, bloco="Setor\\Norte", numero="404", tipo=TipoSala.REGULAR, capacidade=30, turnos_disponiveis=["matutino"])
    s_c2 = Sala(campus_id=c2.id, bloco="Lab Sul", numero="101", tipo=TipoSala.LABORATORIO, capacidade=40, turnos_disponiveis=["noturno"])
    test_db.add_all([s_lab, s_num_lab, s_reg, s_pct, s_und, s_bar, s_c2])
    test_db.flush()

    curso1 = Curso(campus_id=c1.id, nome="Ciencia da Computacao", codigo="BCC")
    curso2 = Curso(campus_id=c2.id, nome="Sistemas de Informacao", codigo="BSI")
    test_db.add_all([curso1, curso2])
    test_db.flush()

    d_ia = Disciplina(curso_id=curso1.id, nome="Inteligencia Artificial", codigo="IA_2026", carga_horaria=60)
    d_iax = Disciplina(curso_id=curso1.id, nome="Topicos Avancados", codigo="IAX2026", carga_horaria=60)
    d_bd = Disciplina(curso_id=curso1.id, nome="Banco de Dados 100%", codigo="BD101", carga_horaria=60)
    d_c2 = Disciplina(curso_id=curso2.id, nome="Inteligencia Artificial Sul", codigo="IASUL", carga_horaria=60)
    test_db.add_all([d_ia, d_iax, d_bd, d_c2])
    test_db.flush()

    t_not = Turma(disciplina_id=d_ia.id, professor_id=prof1.id, periodo_letivo="2026.1", turno_preferido=Turno.NOTURNO, num_matriculados=30)
    t_iax = Turma(disciplina_id=d_iax.id, professor_id=prof1.id, periodo_letivo="2026.1", turno_preferido=Turno.NOTURNO, num_matriculados=15)
    t_mat = Turma(disciplina_id=d_bd.id, professor_id=prof1.id, periodo_letivo="2026.2", turno_preferido=Turno.MATUTINO, num_matriculados=25)
    t_c2 = Turma(disciplina_id=d_c2.id, professor_id=None, periodo_letivo="2026.1", turno_preferido=Turno.NOTURNO, num_matriculados=20)
    test_db.add_all([t_not, t_iax, t_mat, t_c2])
    test_db.flush()

    h1 = Horario(campus_id=c1.id, turma_id=t_not.id, sala_id=s_lab.id, dia_semana=1, hora_inicio=time(18, 30), hora_fim=time(20, 10))
    h2 = Horario(campus_id=c1.id, turma_id=t_not.id, sala_id=s_reg.id, dia_semana=3, hora_inicio=time(18, 30), hora_fim=time(20, 10))
    h3 = Horario(campus_id=c1.id, turma_id=t_mat.id, sala_id=s_lab.id, dia_semana=0, hora_inicio=time(8, 0), hora_fim=time(10, 0))
    h4 = Horario(campus_id=c1.id, turma_id=t_mat.id, sala_id=s_reg.id, dia_semana=6, hora_inicio=time(10, 0), hora_fim=time(12, 0))
    h_c2 = Horario(campus_id=c2.id, turma_id=t_c2.id, sala_id=s_c2.id, dia_semana=1, hora_inicio=time(18, 30), hora_fim=time(20, 10))
    test_db.add_all([h1, h2, h3, h4, h_c2])
    test_db.commit()

    return {
        "c1": c1, "c2": c2,
        "admin": admin, "coord1": coord1, "sec1": sec1, "prof1": prof1, "aluno1": aluno1, "coord2": coord2,
        "s_lab": s_lab, "s_num_lab": s_num_lab, "s_reg": s_reg, "s_pct": s_pct, "s_und": s_und, "s_bar": s_bar, "s_c2": s_c2,
        "d_ia": d_ia, "d_iax": d_iax, "d_bd": d_bd, "t_not": t_not, "t_iax": t_iax, "t_mat": t_mat, "t_c2": t_c2,
        "h1": h1, "h2": h2, "h3": h3, "h4": h4, "h_c2": h_c2,
    }


def test_salas_busca_textual_case_insensitive_e_isolamento(client: TestClient, cenario: dict):
    headers_coord1 = auth_headers(cenario["coord1"])
    res = client.get("/api/v1/salas?q=lab", headers=headers_coord1)
    assert res.status_code == 200
    ids = {s["id"] for s in res.json()}
    assert ids == {cenario["s_lab"].id, cenario["s_num_lab"].id}

    # Coordenador tentando filtrar outro campus tem campus_id ignorado
    res_bola = client.get(f"/api/v1/salas?q=lab&campus_id={cenario['c2'].id}", headers=headers_coord1)
    assert res_bola.status_code == 200
    assert {s["id"] for s in res_bola.json()} == {cenario["s_lab"].id, cenario["s_num_lab"].id}

    # Admin pode filtrar por campus_id
    res_admin = client.get(f"/api/v1/salas?q=lab&campus_id={cenario['c2'].id}", headers=auth_headers(cenario["admin"]))
    assert res_admin.status_code == 200
    assert [s["id"] for s in res_admin.json()] == [cenario["s_c2"].id]


def test_salas_escape_caracteres_especiais_ilike(client: TestClient, cenario: dict):
    headers = auth_headers(cenario["coord1"])

    res_pct = client.get("/api/v1/salas?q=%25", headers=headers)
    assert res_pct.status_code == 200
    assert [s["id"] for s in res_pct.json()] == [cenario["s_pct"].id]

    res_und = client.get("/api/v1/salas?q=_", headers=headers)
    assert res_und.status_code == 200
    assert [s["id"] for s in res_und.json()] == [cenario["s_und"].id]

    res_bar = client.get("/api/v1/salas?q=%5C", headers=headers)
    assert res_bar.status_code == 200
    assert [s["id"] for s in res_bar.json()] == [cenario["s_bar"].id]

    res_vazio = client.get("/api/v1/salas?q=%20%20", headers=headers)
    assert res_vazio.status_code == 200
    assert len(res_vazio.json()) == 6


def test_turmas_busca_textual_escape_e_isolamento(client: TestClient, cenario: dict):
    headers_sec = auth_headers(cenario["sec1"])

    # Busca por nome da disciplina (ignorando turma do campus 2)
    res_nome = client.get("/api/v1/turmas?q=inteligencia", headers=headers_sec)
    assert res_nome.status_code == 200
    assert [t["id"] for t in res_nome.json()] == [cenario["t_not"].id]

    # Busca por periodo letivo
    res_per1 = client.get("/api/v1/turmas?q=2026.1", headers=headers_sec)
    assert res_per1.status_code == 200
    assert {t["id"] for t in res_per1.json()} == {cenario["t_not"].id, cenario["t_iax"].id}

    res_per = client.get("/api/v1/turmas?q=2026.2", headers=headers_sec)
    assert res_per.status_code == 200
    assert [t["id"] for t in res_per.json()] == [cenario["t_mat"].id]

    # Escape literal de '_' (nao retorna IAX2026) e '%'
    res_und = client.get("/api/v1/turmas?q=IA_2026", headers=headers_sec)
    assert res_und.status_code == 200
    assert [t["id"] for t in res_und.json()] == [cenario["t_not"].id]

    res_pct = client.get("/api/v1/turmas?q=%25", headers=headers_sec)
    assert res_pct.status_code == 200
    assert [t["id"] for t in res_pct.json()] == [cenario["t_mat"].id]

    # Coordenador/Secretaria nao vaza campus 2 mesmo passando campus_id
    res_bola = client.get(f"/api/v1/turmas?campus_id={cenario['c2'].id}&q=inteligencia", headers=headers_sec)
    assert res_bola.status_code == 200
    assert [t["id"] for t in res_bola.json()] == [cenario["t_not"].id]

    # Admin filtra por campus_id e disciplina_id combinados com q
    res_adm = client.get(
        f"/api/v1/turmas?campus_id={cenario['c1'].id}&disciplina_id={cenario['d_ia'].id}&q=2026",
        headers=auth_headers(cenario["admin"]),
    )
    assert res_adm.status_code == 200
    assert [t["id"] for t in res_adm.json()] == [cenario["t_not"].id]


def test_usuarios_busca_textual_escape_e_isolamento(client: TestClient, cenario: dict):
    headers_coord1 = auth_headers(cenario["coord1"])

    # Sem autenticacao retorna 401; perfil aluno/professor retorna 403 em listagem
    assert client.get("/api/v1/usuarios").status_code == 401
    assert client.get("/api/v1/usuarios", headers=auth_headers(cenario["aluno1"])).status_code == 403
    assert client.get("/api/v1/usuarios", headers=auth_headers(cenario["prof1"])).status_code == 403

    # Aluno nao pode acessar dados de outro usuario nem usuario de outro campus
    assert client.get(f"/api/v1/usuarios/{cenario['coord1'].id}", headers=auth_headers(cenario["aluno1"])).status_code == 403
    assert client.get(f"/api/v1/usuarios/{cenario['coord2'].id}", headers=headers_coord1).status_code == 404

    # Busca por nome case-insensitive restrita ao campus 1
    res_nome = client.get("/api/v1/usuarios?q=helena", headers=headers_coord1)
    assert res_nome.status_code == 200
    assert [u["id"] for u in res_nome.json()] == [cenario["coord1"].id]

    # Tentativa de forcar campus_id alheio ignorada para nao-admin
    res_bola = client.get(f"/api/v1/usuarios?q=helena&campus_id={cenario['c2'].id}", headers=headers_coord1)
    assert res_bola.status_code == 200
    assert [u["id"] for u in res_bola.json()] == [cenario["coord1"].id]

    # Admin filtra por campus_id
    res_admin = client.get(f"/api/v1/usuarios?q=helena&campus_id={cenario['c2'].id}", headers=auth_headers(cenario["admin"]))
    assert res_admin.status_code == 200
    assert [u["id"] for u in res_admin.json()] == [cenario["coord2"].id]

    # Escape literal de '_' no email e '%' no nome
    res_und = client.get("/api/v1/usuarios?q=_", headers=headers_coord1)
    assert res_und.status_code == 200
    assert [u["id"] for u in res_und.json()] == [cenario["coord1"].id]

    res_pct = client.get("/api/v1/usuarios?q=%25", headers=headers_coord1)
    assert res_pct.status_code == 200
    assert [u["id"] for u in res_pct.json()] == [cenario["sec1"].id]


def test_horarios_filtros_combinados_e_isolamento(client: TestClient, cenario: dict):
    headers_coord1 = auth_headers(cenario["coord1"])

    # Sem autenticacao deve retornar 401
    assert client.get("/api/v1/horarios").status_code == 401

    # Listagem padrao retorna apenas horarios do campus do usuario autenticado
    res_all = client.get("/api/v1/horarios", headers=headers_coord1)
    assert res_all.status_code == 200
    assert {h["id"] for h in res_all.json()} == {
        cenario["h1"].id, cenario["h2"].id, cenario["h3"].id, cenario["h4"].id
    }

    # Filtros combinados: dia_semana=1, turno=noturno, sala_id=s_lab
    url = f"/api/v1/horarios?dia_semana=1&turno=noturno&sala_id={cenario['s_lab'].id}"
    res_comb = client.get(url, headers=headers_coord1)
    assert res_comb.status_code == 200
    assert [h["id"] for h in res_comb.json()] == [cenario["h1"].id]

    # Limites de dia_semana=0 e dia_semana=6 e filtro turma_id
    res_d0 = client.get(f"/api/v1/horarios?dia_semana=0&turma_id={cenario['t_mat'].id}", headers=headers_coord1)
    assert res_d0.status_code == 200
    assert [h["id"] for h in res_d0.json()] == [cenario["h3"].id]

    res_d6 = client.get("/api/v1/horarios?dia_semana=6&turno=matutino", headers=headers_coord1)
    assert res_d6.status_code == 200
    assert [h["id"] for h in res_d6.json()] == [cenario["h4"].id]

    # Isolamento contra campus_id e sala_id de outro campus e GET /horarios/{id}
    res_bola = client.get(f"/api/v1/horarios?campus_id={cenario['c2'].id}", headers=headers_coord1)
    assert res_bola.status_code == 200
    assert {h["id"] for h in res_bola.json()} == {
        cenario["h1"].id, cenario["h2"].id, cenario["h3"].id, cenario["h4"].id
    }

    res_sala_alheia = client.get(f"/api/v1/horarios?sala_id={cenario['s_c2'].id}", headers=headers_coord1)
    assert res_sala_alheia.status_code == 200
    assert res_sala_alheia.json() == []

    assert client.get(f"/api/v1/horarios/{cenario['h1'].id}", headers=headers_coord1).status_code == 200
    assert client.get(f"/api/v1/horarios/{cenario['h_c2'].id}", headers=headers_coord1).status_code == 404

    # Admin filtrando campus 2
    res_admin = client.get(f"/api/v1/horarios?campus_id={cenario['c2'].id}", headers=auth_headers(cenario["admin"]))
    assert res_admin.status_code == 200
    assert [h["id"] for h in res_admin.json()] == [cenario["h_c2"].id]


@pytest.mark.parametrize(
    "query_invalida",
    ["dia_semana=9", "dia_semana=-1", "dia_semana=7", "turno=madrugada", "sala_id=0", "sala_id=-5", "turma_id=0", "turma_id=-1", "campus_id=0", "skip=-1", "limit=0", "limit=101"],
)
def test_horarios_parametros_invalidos_retornam_422(client: TestClient, cenario: dict, query_invalida: str):
    headers = auth_headers(cenario["coord1"])
    res = client.get(f"/api/v1/horarios?{query_invalida}", headers=headers)
    assert res.status_code == 422


@pytest.mark.parametrize("endpoint", ["salas", "turmas", "usuarios"])
@pytest.mark.parametrize("query_paginacao", ["skip=-1", "limit=0", "limit=101", "campus_id=0", f"q={'x' * 101}"])
def test_paginacao_invalida_endpoints_busca(
    client: TestClient, cenario: dict, endpoint: str, query_paginacao: str
):
    headers = auth_headers(cenario["coord1"])
    res = client.get(f"/api/v1/{endpoint}?{query_paginacao}", headers=headers)
    assert res.status_code == 422
