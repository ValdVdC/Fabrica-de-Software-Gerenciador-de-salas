"""
Endpoints para gestao de Salas e associacoes de equipamentos.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.campus import Campus
from app.models.sala import Sala, Equipamento, SalaEquipamento
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.sala import SalaCreate, SalaRead
from app.schemas.equipamento import SalaEquipamentoCreate, SalaEquipamentoRead
from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=list[SalaRead])
def listar_salas(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    campus_id: Optional[int] = Query(default=None, gt=0, description="Filtro por ID do campus"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista salas cadastradas respeitando o isolamento multi-campus."""
    stmt = select(Sala)
    if current_user.perfil == PerfilUsuario.ADMIN:
        if campus_id is not None:
            stmt = stmt.where(Sala.campus_id == campus_id)
    else:
        stmt = stmt.where(Sala.campus_id == current_user.campus_id)

    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.post("", response_model=SalaRead, status_code=status.HTTP_201_CREATED)
def criar_sala(
    payload: SalaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR)),
):
    """Cadastra nova sala no campus com validacao de duplicidade e multi-tenancy."""
    campus = db.get(Campus, payload.campus_id)
    if not campus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus nao encontrado")

    if current_user.perfil != PerfilUsuario.ADMIN and payload.campus_id != current_user.campus_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: coordenador restrito ao seu campus")

    stmt = select(Sala).where(Sala.campus_id == payload.campus_id, Sala.bloco == payload.bloco, Sala.numero == payload.numero)
    if db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ja existe sala no bloco '{payload.bloco}' e numero '{payload.numero}' para este campus")

    turnos_str = [t.value if hasattr(t, "value") else str(t) for t in payload.turnos_disponiveis]
    sala = Sala(
        campus_id=payload.campus_id,
        bloco=payload.bloco,
        numero=payload.numero,
        tipo=payload.tipo,
        capacidade=payload.capacidade,
        turnos_disponiveis=turnos_str,
    )
    db.add(sala)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito de unicidade: sala ja cadastrada")
    db.refresh(sala)
    return sala


@router.get("/{sala_id}", response_model=SalaRead)
def obter_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtem dados de uma sala especifica garantindo isolamento tenant."""
    sala = db.get(Sala, sala_id)
    if not sala or (current_user.perfil != PerfilUsuario.ADMIN and sala.campus_id != current_user.campus_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sala nao encontrada")
    return sala


@router.post("/{sala_id}/equipamentos", response_model=SalaEquipamentoRead, status_code=status.HTTP_201_CREATED)
def associar_equipamento(
    sala_id: int,
    payload: SalaEquipamentoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR)),
):
    """Vincula equipamento a uma sala com quantidade especificada."""
    sala = db.get(Sala, sala_id)
    if not sala or (current_user.perfil != PerfilUsuario.ADMIN and sala.campus_id != current_user.campus_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sala nao encontrada")

    equip = db.get(Equipamento, payload.equipamento_id)
    if not equip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipamento nao encontrado")

    stmt = select(SalaEquipamento).where(
        SalaEquipamento.sala_id == sala_id,
        SalaEquipamento.equipamento_id == payload.equipamento_id,
    )
    assoc = db.scalar(stmt)
    if assoc:
        assoc.quantidade = payload.quantidade
    else:
        assoc = SalaEquipamento(
            sala_id=sala_id,
            equipamento_id=payload.equipamento_id,
            quantidade=payload.quantidade,
        )
        db.add(assoc)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito ao associar equipamento")
    db.refresh(assoc)
    return assoc
