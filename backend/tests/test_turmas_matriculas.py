"""Testes automatizados TDD para gestao de turmas e matriculas com integridade e isolamento multi-campus."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models import Campus, Usuario, PerfilUsuario
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(test_db):
    def override_get_db():
        yield test_db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def setup_cenario(test_db):
    ca = Campus(nome="Campus Sao Luis", cidade="Sao Luis", endereco="Av dos Portugueses")
    cb = Campus(nome="Campus Imperatriz", cidade="Imperatriz", endereco="Rua Urbano Santos")
    test_db.add_all([ca, cb])
    test_db.commit()

    s = get_password_hash("sigaas123")
    adm = Usuario(nome="Admin", email="admin@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.ADMIN, campus_id=ca.id)
    sec = Usuario(nome="Sec A", email="sec_a@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.SECRETARIA, campus_id=ca.id)
    pa = Usuario(nome="Prof A", email="prof_a@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.PROFESSOR, campus_id=ca.id)
    pb = Usuario(nome="Prof B", email="prof_b@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.PROFESSOR, campus_id=cb.id)
    p_inativo = Usuario(nome="Prof Inativo", email="prof_inativo@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.PROFESSOR, campus_id=ca.id, ativo=False)
    aa = Usuario(nome="Aluno A", email="aluno_a@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.ALUNO, campus_id=ca.id)
    ab = Usuario(nome="Aluno B", email="aluno_b@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.ALUNO, campus_id=cb.id)
    a_inativo = Usuario(nome="Aluno Inativo", email="aluno_inativo@sigaas.edu", senha_hash=s, perfil=PerfilUsuario.ALUNO, campus_id=ca.id, ativo=False)
    test_db.add_all([adm, sec, pa, pb, p_inativo, aa, ab, a_inativo])
    test_db.commit()

    return {
        "campus_a": ca, "campus_b": cb, "admin": adm, "sec_a": sec,
        "prof_a": pa, "prof_b": pb, "prof_inativo": p_inativo,
        "aluno_a": aa, "aluno_b": ab, "aluno_inativo": a_inativo,
        "token_admin": create_access_token({"sub": str(adm.id), "perfil": adm.perfil.value}),
        "token_sec_a": create_access_token({"sub": str(sec.id), "perfil": sec.perfil.value}),
        "token_prof_a": create_access_token({"sub": str(pa.id), "perfil": pa.perfil.value}),
        "token_aluno_a": create_access_token({"sub": str(aa.id), "perfil": aa.perfil.value}),
    }


def _criar_curso_e_disciplina(client, token, campus_id, cod_c="CC", cod_d="POO"):
    c = client.post("/api/v1/cursos", json={"campus_id": campus_id, "nome": f"Curso {cod_c}", "codigo": cod_c}, headers={"Authorization": f"Bearer {token}"}).json()
    d = client.post("/api/v1/disciplinas", json={"curso_id": c["id"], "nome": f"Disciplina {cod_d}", "codigo": cod_d, "carga_horaria": 60}, headers={"Authorization": f"Bearer {token}"}).json()
    return c["id"], d["id"]


def test_criar_turma_sucesso_inicializacao_matriculados(client, setup_cenario):
    t, cid = setup_cenario["token_sec_a"], setup_cenario["campus_a"].id
    _, did = _criar_curso_e_disciplina(client, t, cid, "CC01", "POO01")
    p = {"disciplina_id": did, "professor_id": setup_cenario["prof_a"].id, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}
    resp = client.post("/api/v1/turmas", json=p, headers={"Authorization": f"Bearer {t}"})
    assert resp.status_code == 201 and resp.json()["num_matriculados"] == 0 and resp.json()["periodo_letivo"] == "2026.1"


def test_criar_turma_disciplina_campus_alheio_rejeitado(client, setup_cenario):
    _, did_b = _criar_curso_e_disciplina(client, setup_cenario["token_admin"], setup_cenario["campus_b"].id, "MED", "ANAT")
    p = {"disciplina_id": did_b, "periodo_letivo": "2026.1", "turno_preferido": "vespertino"}
    assert client.post("/api/v1/turmas", json=p, headers={"Authorization": f"Bearer {setup_cenario['token_sec_a']}"}).status_code == 404


def test_criar_turma_professor_invalido_inativo_ou_campus_alheio(client, setup_cenario):
    t, cid = setup_cenario["token_sec_a"], setup_cenario["campus_a"].id
    _, did = _criar_curso_e_disciplina(client, t, cid, "ENG", "FIS1")
    assert client.post("/api/v1/turmas", json={"disciplina_id": did, "professor_id": setup_cenario["aluno_a"].id, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {t}"}).status_code == 404
    assert client.post("/api/v1/turmas", json={"disciplina_id": did, "professor_id": setup_cenario["prof_b"].id, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {t}"}).status_code == 404
    assert client.post("/api/v1/turmas", json={"disciplina_id": did, "professor_id": setup_cenario["prof_inativo"].id, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {t}"}).status_code == 404


def test_matricular_aluno_incremento_atomico_e_duplicidade(client, setup_cenario):
    t, cid = setup_cenario["token_sec_a"], setup_cenario["campus_a"].id
    _, did = _criar_curso_e_disciplina(client, t, cid, "MAT", "CALC1")
    tid = client.post("/api/v1/turmas", json={"disciplina_id": did, "periodo_letivo": "2026.1", "turno_preferido": "noturno"}, headers={"Authorization": f"Bearer {t}"}).json()["id"]

    mp = {"aluno_id": setup_cenario["aluno_a"].id, "turma_id": tid}
    m = client.post("/api/v1/matriculas", json=mp, headers={"Authorization": f"Bearer {t}"})
    assert m.status_code == 201 and m.json()["status"] == "ativa"
    assert client.get(f"/api/v1/turmas/{tid}", headers={"Authorization": f"Bearer {t}"}).json()["num_matriculados"] == 1

    assert client.post("/api/v1/matriculas", json=mp, headers={"Authorization": f"Bearer {t}"}).status_code == 409
    assert client.get(f"/api/v1/turmas/{tid}", headers={"Authorization": f"Bearer {t}"}).json()["num_matriculados"] == 1


def test_matricular_aluno_campus_alheio_ou_inativo_rejeitado(client, setup_cenario):
    t, cid = setup_cenario["token_sec_a"], setup_cenario["campus_a"].id
    _, did = _criar_curso_e_disciplina(client, t, cid, "DIR", "DCONST")
    tid = client.post("/api/v1/turmas", json={"disciplina_id": did, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {t}"}).json()["id"]

    assert client.post("/api/v1/matriculas", json={"aluno_id": setup_cenario["aluno_b"].id, "turma_id": tid}, headers={"Authorization": f"Bearer {t}"}).status_code == 404
    assert client.post("/api/v1/matriculas", json={"aluno_id": setup_cenario["aluno_inativo"].id, "turma_id": tid}, headers={"Authorization": f"Bearer {t}"}).status_code == 404
    assert client.post("/api/v1/matriculas", json={"aluno_id": setup_cenario["aluno_b"].id, "turma_id": tid}, headers={"Authorization": f"Bearer {setup_cenario['token_admin']}"}).status_code == 400


def test_listar_turmas_e_matriculas_paginacao_e_bola_aluno(client, setup_cenario):
    t, cid = setup_cenario["token_sec_a"], setup_cenario["campus_a"].id
    _, did = _criar_curso_e_disciplina(client, t, cid, "HIS", "HIST1")
    t1 = client.post("/api/v1/turmas", json={"disciplina_id": did, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {t}"}).json()
    client.post("/api/v1/turmas", json={"disciplina_id": did, "periodo_letivo": "2026.2", "turno_preferido": "noturno"}, headers={"Authorization": f"Bearer {t}"})

    list_turmas = client.get("/api/v1/turmas?skip=0&limit=10", headers={"Authorization": f"Bearer {t}"})
    assert list_turmas.status_code == 200 and len(list_turmas.json()) >= 2

    client.post("/api/v1/matriculas", json={"aluno_id": setup_cenario["aluno_a"].id, "turma_id": t1["id"]}, headers={"Authorization": f"Bearer {t}"})
    list_matr = client.get(f"/api/v1/matriculas?turma_id={t1['id']}", headers={"Authorization": f"Bearer {t}"})
    assert list_matr.status_code == 200 and len(list_matr.json()) == 1

    aluno_matr = client.get("/api/v1/matriculas", headers={"Authorization": f"Bearer {setup_cenario['token_aluno_a']}"})
    assert aluno_matr.status_code == 200 and all(m["aluno_id"] == setup_cenario["aluno_a"].id for m in aluno_matr.json())


def test_rbac_aluno_e_professor_bloqueados_em_turmas_e_matriculas(client, setup_cenario):
    at, pt = setup_cenario["token_aluno_a"], setup_cenario["token_prof_a"]
    assert client.post("/api/v1/turmas", json={"disciplina_id": 1, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {at}"}).status_code == 403
    assert client.post("/api/v1/turmas", json={"disciplina_id": 1, "periodo_letivo": "2026.1", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {pt}"}).status_code == 403
    assert client.post("/api/v1/matriculas", json={"aluno_id": 1, "turma_id": 1}, headers={"Authorization": f"Bearer {at}"}).status_code == 403
    assert client.post("/api/v1/matriculas", json={"aluno_id": 1, "turma_id": 1}, headers={"Authorization": f"Bearer {pt}"}).status_code == 403


def test_validacoes_defensivas_turma_e_matricula(client, setup_cenario):
    t, cid = setup_cenario["token_sec_a"], setup_cenario["campus_a"].id
    _, did = _criar_curso_e_disciplina(client, t, cid, "LET", "PORT1")
    assert client.post("/api/v1/turmas", json={"disciplina_id": did, "periodo_letivo": "   ", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {t}"}).status_code == 422
    assert client.post("/api/v1/turmas", json={"disciplina_id": did, "periodo_letivo": "20", "turno_preferido": "matutino"}, headers={"Authorization": f"Bearer {t}"}).status_code == 422
    assert client.post("/api/v1/turmas", json={"disciplina_id": did, "periodo_letivo": "2026.1", "turno_preferido": "matutino", "extra": "x"}, headers={"Authorization": f"Bearer {t}"}).status_code == 422
    assert client.post("/api/v1/matriculas", json={"aluno_id": 1, "turma_id": 1, "extra": "x"}, headers={"Authorization": f"Bearer {t}"}).status_code == 422
