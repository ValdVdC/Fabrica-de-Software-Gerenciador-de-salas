"""Endpoints RESTful para gestao de equipamentos."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.sala import Equipamento
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.equipamento import EquipamentoCreate, EquipamentoRead
from app.api.deps import require_role

router = APIRouter()


@router.get("", response_model=list[EquipamentoRead])
def listar_equipamentos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista equipamentos disponiveis no catalogo institucional."""
    stmt = select(Equipamento).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.post("", response_model=EquipamentoRead, status_code=status.HTTP_201_CREATED)
def criar_equipamento(
    payload: EquipamentoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR)),
):
    """Cadastra novo equipamento no catalogo institucional com protecao de concorrencia."""
    err_msg = f"Ja existe equipamento cadastrado com o nome '{payload.nome}'"
    if db.scalar(select(Equipamento).where(Equipamento.nome == payload.nome)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)
    equipamento = Equipamento(nome=payload.nome, descricao=payload.descricao)
    db.add(equipamento)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)
    db.refresh(equipamento)
    return equipamento
