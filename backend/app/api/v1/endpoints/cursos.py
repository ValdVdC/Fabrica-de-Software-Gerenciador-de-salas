"""Endpoints para gestao de Cursos com RBAC e isolamento multi-campus."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.academico import Curso
from app.models.campus import Campus
from app.models.usuario import Usuario
from app.models.enums import PerfilUsuario
from app.schemas.academico import CursoCreate, CursoRead
from app.api.deps import require_role, get_current_user

router = APIRouter()


@router.get("", response_model=list[CursoRead])
def listar_cursos(
    campus_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista cursos filtrados pelo campus do usuario nao-admin."""
    filtro_campus = current_user.campus_id if current_user.perfil != PerfilUsuario.ADMIN else campus_id
    stmt = select(Curso)
    if filtro_campus:
        stmt = stmt.where(Curso.campus_id == filtro_campus)
    return db.scalars(stmt).all()


@router.post("", response_model=CursoRead, status_code=status.HTTP_201_CREATED)
def criar_curso(
    payload: CursoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)),
):
    """Cadastra novo curso garantindo restricao multi-campus."""
    if current_user.perfil != PerfilUsuario.ADMIN and payload.campus_id != current_user.campus_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissao negada para campus alheio")

    if not db.get(Campus, payload.campus_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus nao encontrado")

    stmt = select(Curso).where(Curso.campus_id == payload.campus_id, Curso.codigo == payload.codigo)
    if db.scalars(stmt).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Curso com este codigo ja existe neste campus")

    curso = Curso(campus_id=payload.campus_id, nome=payload.nome, codigo=payload.codigo)
    db.add(curso)
    try:
        db.commit()
        db.refresh(curso)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito ao cadastrar curso")
    return curso
