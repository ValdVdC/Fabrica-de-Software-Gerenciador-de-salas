"""Endpoints para gestao de Disciplinas com RBAC e isolamento por campus."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.academico import Disciplina, Curso
from app.models.usuario import Usuario
from app.models.enums import PerfilUsuario
from app.schemas.academico import DisciplinaCreate, DisciplinaRead
from app.api.deps import require_role, get_current_user

router = APIRouter()


@router.get("", response_model=list[DisciplinaRead])
def listar_disciplinas(
    curso_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista disciplinas respeitando o campus do usuario logado."""
    stmt = select(Disciplina).join(Curso)
    if current_user.perfil != PerfilUsuario.ADMIN:
        stmt = stmt.where(Curso.campus_id == current_user.campus_id)
    if curso_id:
        stmt = stmt.where(Disciplina.curso_id == curso_id)
    return db.scalars(stmt).all()


@router.post("", response_model=DisciplinaRead, status_code=status.HTTP_201_CREATED)
def criar_disciplina(
    payload: DisciplinaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)),
):
    """Cadastra disciplina com carga horaria positiva vinculada a curso valido."""
    curso = db.get(Curso, payload.curso_id)
    if not curso or (current_user.perfil != PerfilUsuario.ADMIN and curso.campus_id != current_user.campus_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso nao encontrado")

    stmt = select(Disciplina).where(Disciplina.curso_id == payload.curso_id, Disciplina.codigo == payload.codigo)
    if db.scalars(stmt).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Disciplina com este codigo ja existe no curso")

    disciplina = Disciplina(curso_id=payload.curso_id, nome=payload.nome, codigo=payload.codigo, carga_horaria=payload.carga_horaria)
    db.add(disciplina)
    try:
        db.commit()
        db.refresh(disciplina)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito ao cadastrar disciplina")
    return disciplina
