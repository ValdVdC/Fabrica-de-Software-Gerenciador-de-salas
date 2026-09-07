"""
Endpoints para gestao de Usuarios.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioRead

router = APIRouter()


@router.get("", response_model=list[UsuarioRead])
def listar_usuarios(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=100), db: Session = Depends(get_db)):
    stmt = select(Usuario).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{usuario_id}", response_model=UsuarioRead)
def obter_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")
    return usuario
