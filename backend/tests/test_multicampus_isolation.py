"""
Testes automatizados TDD para isolamento estrito multi-campus (BOLA/IDOR) e ciclo de vida.
Cobre Historia 2 da Sprint 08 (docs/specs/sprint8-rbac-multicampus.md).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models import Campus, Usuario, PerfilUsuario
from app.models.sala import Sala
from app.models.academico import Curso, Disciplina, Turma
from app.models.enums import Turno, TipoSala
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def test_db():
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
    def override_get_db():
        yield test_db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def cenario_isolamento(test_db):
    c1 = Campus(nome="Campus Teresina", cidade="Teresina", endereco="Av Frei Serafim")
    c2 = Campus(nome="Campus Parnaiba", cidade="Parnaiba", endereco="Av Sao Sebastiao")
    test_db.add_all([c1, c2])
    test_db.commit()

    senha = get_password_hash("senha_sigaas_123")
    admin = Usuario(nome="Admin Geral", email="admin.iso@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ADMIN, campus_id=c1.id)
    coord1 = Usuario(nome="Coord C1", email="coord1.iso@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR, campus_id=c1.id)
    coord2 = Usuario(nome="Coord C2", email="coord2.iso@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR, campus_id=c2.id)
    sec1 = Usuario(nome="Sec C1", email="sec1.iso@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.SECRETARIA, campus_id=c1.id)
    prof1 = Usuario(nome="Prof C1", email="prof1.iso@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR, campus_id=c1.id)
    prof1_outro = Usuario(nome="Prof Outro C1", email="prof1_outro.iso@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR, campus_id=c1.id)
    prof2 = Usuario(nome="Prof C2", email="prof2.iso@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR, campus_id=c2.id)
    prof_inativo = Usuario(nome="Prof Inativo C1", email="prof_inativo.iso@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR, campus_id=c1.id, ativo=False)
    aluno1 = Usuario(nome="Aluno C1", email="aluno1.iso@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO, campus_id=c1.id)

    test_db.add_all([admin, coord1, coord2, sec1, prof1, prof1_outro, prof2, prof_inativo, aluno1])
    test_db.commit()

    # Salas
    s1 = Sala(campus_id=c1.id, bloco="Bloco A", numero="101", tipo=TipoSala.REGULAR, capacidade=40, turnos_disponiveis=["matutino"], ativo=True)
    s1_outra = Sala(campus_id=c1.id, bloco="Bloco A", numero="102", tipo=TipoSala.REGULAR, capacidade=40, turnos_disponiveis=["matutino"], ativo=True)
    s2 = Sala(campus_id=c2.id, bloco="Bloco B", numero="201", tipo=TipoSala.REGULAR, capacidade=50, turnos_disponiveis=["vespertino"], ativo=True)
    test_db.add_all([s1, s1_outra, s2])
    test_db.commit()

    # Cursos e Disciplinas
    curso1 = Curso(campus_id=c1.id, nome="Ciencia da Computacao", codigo="CC")
    curso2 = Curso(campus_id=c2.id, nome="Sistemas de Informacao", codigo="SI")
    test_db.add_all([curso1, curso2])
    test_db.commit()

    disc1 = Disciplina(curso_id=curso1.id, nome="Algoritmos", codigo="CC101", carga_horaria=60)
    disc2 = Disciplina(curso_id=curso2.id, nome="Banco de Dados", codigo="SI201", carga_horaria=60)
    test_db.add_all([disc1, disc2])
    test_db.commit()

    turma1 = Turma(disciplina_id=disc1.id, professor_id=prof1.id, periodo_letivo="2026.1", turno_preferido=Turno.MATUTINO, num_matriculados=0)
    turma2 = Turma(disciplina_id=disc2.id, professor_id=prof2.id, periodo_letivo="2026.1", turno_preferido=Turno.VESPERTINO, num_matriculados=0)
    test_db.add_all([turma1, turma2])
    test_db.commit()

    return {
        "campus1": c1, "campus2": c2,
        "admin": admin, "coord1": coord1, "coord2": coord2,
        "sec1": sec1, "prof1": prof1, "prof1_outro": prof1_outro, "prof2": prof2,
        "prof_inativo": prof_inativo, "aluno1": aluno1,
        "s1": s1, "s1_outra": s1_outra, "s2": s2,
        "curso1": curso1, "curso2": curso2,
        "disc1": disc1, "disc2": disc2,
        "turma1": turma1, "turma2": turma2,
        "token_admin": create_access_token({"sub": str(admin.id), "perfil": admin.perfil.value}),
        "token_coord1": create_access_token({"sub": str(coord1.id), "perfil": coord1.perfil.value}),
        "token_coord2": create_access_token({"sub": str(coord2.id), "perfil": coord2.perfil.value}),
        "token_sec1": create_access_token({"sub": str(sec1.id), "perfil": sec1.perfil.value}),
        "token_prof1": create_access_token({"sub": str(prof1.id), "perfil": prof1.perfil.value}),
        "token_aluno1": create_access_token({"sub": str(aluno1.id), "perfil": aluno1.perfil.value}),
    }


def test_coordenador_patch_sala_proprio_campus_sucesso(client, test_db, cenario_isolamento):
    c = cenario_isolamento
    resp = client.patch(
        f"/api/v1/salas/{c['s1'].id}",
        json={"capacidade": 45, "ativo": False},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["capacidade"] == 45
    assert data["ativo"] is False

    sala_atualizada = test_db.get(Sala, c["s1"].id)
    assert sala_atualizada.capacidade == 45
    assert sala_atualizada.ativo is False


def test_coordenador_patch_sala_outro_campus_retorna_404(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.patch(
        f"/api/v1/salas/{c['s2'].id}",
        json={"capacidade": 60},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 404


def test_patch_sala_conflito_duplicidade(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.patch(
        f"/api/v1/salas/{c['s1'].id}",
        json={"bloco": "Bloco A", "numero": "102"},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 409


def test_secretaria_patch_sala_forbidden(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.patch(
        f"/api/v1/salas/{c['s1'].id}",
        json={"capacidade": 50},
        headers={"Authorization": f"Bearer {c['token_sec1']}"},
    )
    assert resp.status_code == 403


def test_patch_turma_sucesso_mesmo_campus(client, test_db, cenario_isolamento):
    c = cenario_isolamento
    resp = client.patch(
        f"/api/v1/turmas/{c['turma1'].id}",
        json={"turno_preferido": "vespertino", "professor_id": c["prof1_outro"].id},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["turno_preferido"] == "vespertino"
    assert data["professor_id"] == c["prof1_outro"].id

    turma = test_db.get(Turma, c["turma1"].id)
    assert turma.turno_preferido == Turno.VESPERTINO
    assert turma.professor_id == c["prof1_outro"].id


def test_patch_turma_desassociar_professor_sucesso(client, test_db, cenario_isolamento):
    c = cenario_isolamento
    resp = client.patch(
        f"/api/v1/turmas/{c['turma1'].id}",
        json={"professor_id": None},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["professor_id"] is None

    turma = test_db.get(Turma, c["turma1"].id)
    assert turma.professor_id is None


def test_patch_turma_outro_campus_retorna_404(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.patch(
        f"/api/v1/turmas/{c['turma2'].id}",
        json={"turno_preferido": "noturno"},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 404


def test_patch_turma_professor_outro_campus_retorna_400(client, cenario_isolamento):
    c = cenario_isolamento
    # Admin tenta associar prof do Campus 2 a turma do Campus 1
    resp = client.patch(
        f"/api/v1/turmas/{c['turma1'].id}",
        json={"professor_id": c["prof2"].id},
        headers={"Authorization": f"Bearer {c['token_admin']}"},
    )
    assert resp.status_code == 400
    assert "Professor pertence a campus diferente da disciplina" in resp.json()["detail"]


def test_patch_turma_professor_inativo_ou_invalido(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.patch(
        f"/api/v1/turmas/{c['turma1'].id}",
        json={"professor_id": c["prof_inativo"].id},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 404


def test_get_curso_unitario_proprio_campus_sucesso(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.get(
        f"/api/v1/cursos/{c['curso1'].id}",
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == c["curso1"].id
    assert data["codigo"] == "CC"


def test_get_curso_unitario_outro_campus_retorna_404(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.get(
        f"/api/v1/cursos/{c['curso2'].id}",
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 404


def test_get_curso_inexistente_retorna_404(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.get(
        "/api/v1/cursos/99999",
        headers={"Authorization": f"Bearer {c['token_admin']}"},
    )
    assert resp.status_code == 404


def test_get_disciplina_unitario_proprio_campus_sucesso(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.get(
        f"/api/v1/disciplinas/{c['disc1'].id}",
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == c["disc1"].id
    assert data["codigo"] == "CC101"


def test_get_disciplina_unitario_outro_campus_retorna_404(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.get(
        f"/api/v1/disciplinas/{c['disc2'].id}",
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 404


def test_get_disciplina_inexistente_retorna_404(client, cenario_isolamento):
    c = cenario_isolamento
    resp = client.get(
        "/api/v1/disciplinas/99999",
        headers={"Authorization": f"Bearer {c['token_admin']}"},
    )
    assert resp.status_code == 404


def test_admin_acessa_qualquer_curso_e_disciplina(client, cenario_isolamento):
    c = cenario_isolamento
    resp_curso = client.get(
        f"/api/v1/cursos/{c['curso2'].id}",
        headers={"Authorization": f"Bearer {c['token_admin']}"},
    )
    assert resp_curso.status_code == 200

    resp_disc = client.get(
        f"/api/v1/disciplinas/{c['disc2'].id}",
        headers={"Authorization": f"Bearer {c['token_admin']}"},
    )
    assert resp_disc.status_code == 200
