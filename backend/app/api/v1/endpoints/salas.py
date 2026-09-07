"""
Endpoints para gestao de Salas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.sala import Sala
from app.schemas.sala import SalaRead

router = APIRouter()


@router.get("", response_model=list[SalaRead])
def listar_salas(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=100), db: Session = Depends(get_db)):
    stmt = select(Sala).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{sala_id}", response_model=SalaRead)
def obter_sala(sala_id: int, db: Session = Depends(get_db)):
    sala = db.get(Sala, sala_id)
    if not sala:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sala nao encontrada")
    return sala
