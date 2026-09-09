"""Endpoints para gestao de Matriculas com RBAC, contagem atomica e isolamento por campus."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.academico import Curso, Disciplina, Matricula, Turma
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.matricula import MatriculaCreate, MatriculaRead

router = APIRouter()


@router.get("", response_model=list[MatriculaRead])
def listar_matriculas(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    turma_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    stmt = select(Matricula).join(Turma).join(Disciplina).join(Curso)
    if current_user.perfil != PerfilUsuario.ADMIN:
        stmt = stmt.where(Curso.campus_id == current_user.campus_id)
    if turma_id:
        stmt = stmt.where(Matricula.turma_id == turma_id)
    return db.scalars(stmt.offset(skip).limit(limit)).all()


@router.post("", response_model=MatriculaRead, status_code=status.HTTP_201_CREATED)
def matricular_aluno(
    payload: MatriculaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)),
):
    aluno = db.get(Usuario, payload.aluno_id)
    if not aluno or aluno.perfil != PerfilUsuario.ALUNO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aluno invalido ou inexistente")

    turma = db.get(Turma, payload.turma_id)
    if not turma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma nao encontrada")

    if current_user.perfil != PerfilUsuario.ADMIN:
        if aluno.campus_id != current_user.campus_id or turma.disciplina.curso.campus_id != current_user.campus_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso nao encontrado no campus")
    elif aluno.campus_id != turma.disciplina.curso.campus_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aluno e turma pertencem a campi diferentes")

    stmt = select(Matricula).where(Matricula.aluno_id == payload.aluno_id, Matricula.turma_id == payload.turma_id)
    if db.scalars(stmt).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Aluno ja matriculado nesta turma")

    turma.num_matriculados += 1
    matricula = Matricula(aluno_id=payload.aluno_id, turma_id=payload.turma_id, status="ativa")
    db.add(matricula)
    try:
        db.commit()
        db.refresh(matricula)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito ao efetuar matricula")
    return matricula
