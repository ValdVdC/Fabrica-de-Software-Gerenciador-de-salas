"""
Endpoints para gestao de Turmas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.academico import Turma
from app.schemas.turma import TurmaRead

router = APIRouter()


@router.get("", response_model=list[TurmaRead])
def listar_turmas(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=100), db: Session = Depends(get_db)):
    stmt = select(Turma).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{turma_id}", response_model=TurmaRead)
def obter_turma(turma_id: int, db: Session = Depends(get_db)):
    turma = db.get(Turma, turma_id)
    if not turma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma nao encontrada")
    return turma
