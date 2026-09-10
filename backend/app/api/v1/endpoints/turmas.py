"""Endpoints para gestao de Turmas com RBAC e isolamento por campus."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.academico import Curso, Disciplina, Turma
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.turma import TurmaCreate, TurmaRead

router = APIRouter()


@router.get("", response_model=list[TurmaRead])
def listar_turmas(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    disciplina_id: int | None = Query(default=None, gt=0),
    campus_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    stmt = select(Turma).join(Disciplina).join(Curso)
    if current_user.perfil != PerfilUsuario.ADMIN:
        stmt = stmt.where(Curso.campus_id == current_user.campus_id)
    elif campus_id:
        stmt = stmt.where(Curso.campus_id == campus_id)
    if disciplina_id:
        stmt = stmt.where(Turma.disciplina_id == disciplina_id)
    return db.scalars(stmt.order_by(Turma.id.asc()).offset(skip).limit(limit)).all()


@router.get("/{turma_id}", response_model=TurmaRead)
def obter_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    turma = db.get(Turma, turma_id)
    if not turma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma nao encontrada")
    if current_user.perfil != PerfilUsuario.ADMIN and turma.disciplina.curso.campus_id != current_user.campus_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma nao encontrada")
    return turma


@router.post("", response_model=TurmaRead, status_code=status.HTTP_201_CREATED)
def criar_turma(
    payload: TurmaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)),
):
    disciplina = db.get(Disciplina, payload.disciplina_id)
    if not disciplina or (current_user.perfil != PerfilUsuario.ADMIN and disciplina.curso.campus_id != current_user.campus_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disciplina nao encontrada")

    if payload.professor_id:
        prof = db.get(Usuario, payload.professor_id)
        if current_user.perfil != PerfilUsuario.ADMIN:
            if not prof or prof.perfil != PerfilUsuario.PROFESSOR or not prof.ativo or prof.campus_id != current_user.campus_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor invalido, inativo ou inexistente")
        else:
            if not prof or prof.perfil != PerfilUsuario.PROFESSOR or not prof.ativo:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Professor invalido, inativo ou inexistente")
            if prof.campus_id != disciplina.curso.campus_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Professor pertence a campus diferente da disciplina")

    turma = Turma(
        disciplina_id=payload.disciplina_id,
        professor_id=payload.professor_id,
        periodo_letivo=payload.periodo_letivo,
        turno_preferido=payload.turno_preferido,
        num_matriculados=0,
    )
    db.add(turma)
    try:
        db.commit()
        db.refresh(turma)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito ao criar turma")
    return turma

