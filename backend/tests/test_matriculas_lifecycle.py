"""
Testes automatizados TDD para ciclo de vida de matriculas e usuarios.
Cobre Historias 1 e 3 da Sprint 08 (docs/specs/sprint8-rbac-multicampus.md).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models import Campus, Usuario, PerfilUsuario
from app.models.academico import Curso, Disciplina, Turma, Matricula
from app.models.alocacao import LogAlocacao
from app.models.enums import Turno, TipoEventoLog
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
def cenario_matriculas(test_db):
    c1 = Campus(nome="Campus Sao Luis", cidade="Sao Luis", endereco="Av Portugueses")
    c2 = Campus(nome="Campus Imperatriz", cidade="Imperatriz", endereco="Rua Urbano")
    test_db.add_all([c1, c2])
    test_db.commit()

    senha = get_password_hash("senha_sigaas_123")
    admin = Usuario(nome="Admin Geral", email="admin@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ADMIN, campus_id=c1.id)
    coord1 = Usuario(nome="Coord C1", email="coord1@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.COORDENADOR, campus_id=c1.id)
    sec1 = Usuario(nome="Sec C1", email="sec1@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.SECRETARIA, campus_id=c1.id)
    sec2 = Usuario(nome="Sec C2", email="sec2@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.SECRETARIA, campus_id=c2.id)
    prof1 = Usuario(nome="Prof C1", email="prof1@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.PROFESSOR, campus_id=c1.id)
    aluno1 = Usuario(nome="Aluno 1 C1", email="aluno1@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO, campus_id=c1.id)
    aluno2 = Usuario(nome="Aluno 2 C1", email="aluno2@sigaas.edu", senha_hash=senha, perfil=PerfilUsuario.ALUNO, campus_id=c1.id)

    test_db.add_all([admin, coord1, sec1, sec2, prof1, aluno1, aluno2])
    test_db.commit()

    curso1 = Curso(campus_id=c1.id, nome="Engenharia de Software", codigo="ESW")
    test_db.add(curso1)
    test_db.commit()

    disc1 = Disciplina(curso_id=curso1.id, nome="Arquitetura de Software", codigo="ESW01", carga_horaria=60)
    test_db.add(disc1)
    test_db.commit()

    turma1 = Turma(
        disciplina_id=disc1.id,
        professor_id=prof1.id,
        periodo_letivo="2026.1",
        turno_preferido=Turno.MATUTINO,
        num_matriculados=2,
    )
    test_db.add(turma1)
    test_db.commit()

    mat1 = Matricula(aluno_id=aluno1.id, turma_id=turma1.id, status="ativa")
    mat2 = Matricula(aluno_id=aluno2.id, turma_id=turma1.id, status="ativa")
    test_db.add_all([mat1, mat2])
    test_db.commit()

    return {
        "campus1": c1, "campus2": c2,
        "admin": admin, "coord1": coord1, "sec1": sec1, "sec2": sec2,
        "prof1": prof1, "aluno1": aluno1, "aluno2": aluno2,
        "turma1": turma1, "mat1": mat1, "mat2": mat2,
        "token_admin": create_access_token({"sub": str(admin.id), "perfil": admin.perfil.value}),
        "token_coord1": create_access_token({"sub": str(coord1.id), "perfil": coord1.perfil.value}),
        "token_sec1": create_access_token({"sub": str(sec1.id), "perfil": sec1.perfil.value}),
        "token_sec2": create_access_token({"sub": str(sec2.id), "perfil": sec2.perfil.value}),
        "token_prof1": create_access_token({"sub": str(prof1.id), "perfil": prof1.perfil.value}),
        "token_aluno1": create_access_token({"sub": str(aluno1.id), "perfil": aluno1.perfil.value}),
        "token_aluno2": create_access_token({"sub": str(aluno2.id), "perfil": aluno2.perfil.value}),
    }


def test_aluno_cancela_propria_matricula_sucesso(client, test_db, cenario_matriculas):
    c = cenario_matriculas
    resp = client.delete(
        f"/api/v1/matriculas/{c['mat1'].id}",
        headers={"Authorization": f"Bearer {c['token_aluno1']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelada"

    turma = test_db.get(Turma, c["turma1"].id)
    assert turma.num_matriculados == 1

    log = test_db.scalars(
        select(LogAlocacao).where(
            LogAlocacao.usuario_responsavel == c["aluno1"].id,
            LogAlocacao.tipo_evento == TipoEventoLog.CANCELAMENTO,
        )
    ).first()
    assert log is not None
    assert log.snapshot_evento["entidade"] == "matricula"
    assert log.snapshot_evento["entidade_id"] == c["mat1"].id


def test_aluno_tenta_cancelar_matricula_de_outro_aluno_forbidden(client, test_db, cenario_matriculas):
    c = cenario_matriculas
    resp = client.delete(
        f"/api/v1/matriculas/{c['mat2'].id}",
        headers={"Authorization": f"Bearer {c['token_aluno1']}"},
    )
    assert resp.status_code == 403

    turma = test_db.get(Turma, c["turma1"].id)
    assert turma.num_matriculados == 2
    mat2 = test_db.get(Matricula, c["mat2"].id)
    assert mat2.status == "ativa"


def test_secretaria_cancela_matricula_do_seu_campus(client, test_db, cenario_matriculas):
    c = cenario_matriculas
    resp = client.delete(
        f"/api/v1/matriculas/{c['mat1'].id}",
        headers={"Authorization": f"Bearer {c['token_sec1']}"},
    )
    assert resp.status_code == 200
    turma = test_db.get(Turma, c["turma1"].id)
    assert turma.num_matriculados == 1


def test_coordenador_cancela_matricula_do_seu_campus(client, test_db, cenario_matriculas):
    c = cenario_matriculas
    resp = client.delete(
        f"/api/v1/matriculas/{c['mat1'].id}",
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 200
    turma = test_db.get(Turma, c["turma1"].id)
    assert turma.num_matriculados == 1


def test_admin_cancela_matricula_qualquer_campus(client, test_db, cenario_matriculas):
    c = cenario_matriculas
    resp = client.delete(
        f"/api/v1/matriculas/{c['mat1'].id}",
        headers={"Authorization": f"Bearer {c['token_admin']}"},
    )
    assert resp.status_code == 200
    turma = test_db.get(Turma, c["turma1"].id)
    assert turma.num_matriculados == 1


def test_secretaria_outro_campus_retorna_404(client, cenario_matriculas):
    c = cenario_matriculas
    resp = client.delete(
        f"/api/v1/matriculas/{c['mat1'].id}",
        headers={"Authorization": f"Bearer {c['token_sec2']}"},
    )
    assert resp.status_code == 404


def test_professor_nao_pode_cancelar_matricula_forbidden(client, cenario_matriculas):
    c = cenario_matriculas
    resp = client.delete(
        f"/api/v1/matriculas/{c['mat1'].id}",
        headers={"Authorization": f"Bearer {c['token_prof1']}"},
    )
    assert resp.status_code == 403


def test_cancelar_matricula_ja_cancelada_bad_request(client, test_db, cenario_matriculas):
    c = cenario_matriculas
    resp1 = client.delete(
        f"/api/v1/matriculas/{c['mat1'].id}",
        headers={"Authorization": f"Bearer {c['token_aluno1']}"},
    )
    assert resp1.status_code == 200

    resp2 = client.delete(
        f"/api/v1/matriculas/{c['mat1'].id}",
        headers={"Authorization": f"Bearer {c['token_aluno1']}"},
    )
    assert resp2.status_code == 400

    turma = test_db.get(Turma, c["turma1"].id)
    assert turma.num_matriculados == 1


def test_rematricula_apos_cancelamento_sucesso(client, test_db, cenario_matriculas):
    c = cenario_matriculas
    # Aluno 1 cancela
    client.delete(
        f"/api/v1/matriculas/{c['mat1'].id}",
        headers={"Authorization": f"Bearer {c['token_aluno1']}"},
    )
    turma = test_db.get(Turma, c["turma1"].id)
    assert turma.num_matriculados == 1

    # Secretaria re-matricula Aluno 1 na mesma turma
    resp_re = client.post(
        "/api/v1/matriculas",
        json={"aluno_id": c["aluno1"].id, "turma_id": c["turma1"].id},
        headers={"Authorization": f"Bearer {c['token_sec1']}"},
    )
    assert resp_re.status_code == 201
    assert resp_re.json()["status"] == "ativa"

    test_db.refresh(turma)
    assert turma.num_matriculados == 2


def test_cancelar_matricula_inexistente_retorna_404(client, cenario_matriculas):
    c = cenario_matriculas
    resp = client.delete(
        "/api/v1/matriculas/99999",
        headers={"Authorization": f"Bearer {c['token_admin']}"},
    )
    assert resp.status_code == 404


def test_patch_usuario_alternar_ativo_e_dados(client, test_db, cenario_matriculas):
    c = cenario_matriculas
    # Coordenador inativa aluno de seu campus
    resp = client.patch(
        f"/api/v1/usuarios/{c['aluno1'].id}",
        json={"ativo": False, "nome": "Aluno 1 Atualizado", "email": "Aluno1.Novo@sigaas.edu"},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ativo"] is False
    assert data["nome"] == "Aluno 1 Atualizado"
    assert data["email"] == "aluno1.novo@sigaas.edu"

    log = test_db.scalars(
        select(LogAlocacao).where(
            LogAlocacao.usuario_responsavel == c["coord1"].id,
            LogAlocacao.tipo_evento == TipoEventoLog.ALTERACAO,
        )
    ).first()
    assert log is not None
    assert log.snapshot_evento["entidade"] == "usuario"
    assert log.snapshot_evento["entidade_id"] == c["aluno1"].id


def test_auto_edicao_coordenador_e_secretaria_sucesso(client, cenario_matriculas):
    c = cenario_matriculas
    # Coordenador altera proprio nome
    resp_coord = client.patch(
        f"/api/v1/usuarios/{c['coord1'].id}",
        json={"nome": "Coordenador Atualizado"},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp_coord.status_code == 200
    assert resp_coord.json()["nome"] == "Coordenador Atualizado"

    # Coordenador tenta auto-elevar perfil para admin (bloqueado)
    resp_elev = client.patch(
        f"/api/v1/usuarios/{c['coord1'].id}",
        json={"perfil": "admin"},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp_elev.status_code == 403


def test_patch_usuario_email_duplicado_retorna_409(client, cenario_matriculas):
    c = cenario_matriculas
    resp = client.patch(
        f"/api/v1/usuarios/{c['aluno1'].id}",
        json={"email": c["aluno2"].email},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 409


def test_patch_usuario_secretaria_tenta_alterar_coordenador_forbidden(client, cenario_matriculas):
    c = cenario_matriculas
    resp = client.patch(
        f"/api/v1/usuarios/{c['coord1'].id}",
        json={"ativo": False},
        headers={"Authorization": f"Bearer {c['token_sec1']}"},
    )
    assert resp.status_code == 403


def test_patch_usuario_coordenador_tenta_alterar_usuario_outro_campus_not_found(client, cenario_matriculas):
    c = cenario_matriculas
    resp = client.patch(
        f"/api/v1/usuarios/{c['sec2'].id}",
        json={"ativo": False},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 404


def test_patch_usuario_coordenador_tenta_promover_para_admin_forbidden(client, cenario_matriculas):
    c = cenario_matriculas
    resp = client.patch(
        f"/api/v1/usuarios/{c['aluno1'].id}",
        json={"perfil": "admin"},
        headers={"Authorization": f"Bearer {c['token_coord1']}"},
    )
    assert resp.status_code == 403
