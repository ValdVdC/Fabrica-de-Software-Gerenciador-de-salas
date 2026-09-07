"""
Endpoints para gestao de Horarios.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.alocacao import Horario
from app.schemas.horario import HorarioRead

router = APIRouter()


@router.get("", response_model=list[HorarioRead])
def listar_horarios(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=100), db: Session = Depends(get_db)):
    stmt = select(Horario).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{horario_id}", response_model=HorarioRead)
def obter_horario(horario_id: int, db: Session = Depends(get_db)):
    horario = db.get(Horario, horario_id)
    if not horario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horario nao encontrado")
    return horario
