"""
Endpoints para gestao de Campi.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.campus import Campus
from app.schemas.campus import CampusCreate, CampusRead

router = APIRouter()


@router.get("", response_model=list[CampusRead])
def listar_campi(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=100), db: Session = Depends(get_db)):
    stmt = select(Campus).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.post("", response_model=CampusRead, status_code=status.HTTP_201_CREATED)
def criar_campus(campus_in: CampusCreate, db: Session = Depends(get_db)):
    campus = Campus(**campus_in.model_dump())
    db.add(campus)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(campus)
    return campus


@router.get("/{campus_id}", response_model=CampusRead)
def obter_campus(campus_id: int, db: Session = Depends(get_db)):
    campus = db.get(Campus, campus_id)
    if not campus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus nao encontrado")
    return campus
