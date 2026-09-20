"""
Endpoints para gestao de Usuarios.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.campus import Campus
from app.models.usuario import Usuario
from app.models.enums import PerfilUsuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.core.security import get_password_hash
from app.api.deps import require_role

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


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)),
):
    """Cadastra novo usuario institucional com hash de senha Bcrypt e validacoes de unicidade."""
    campus = db.get(Campus, payload.campus_id)
    if not campus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus nao encontrado")

    if current_user.perfil != PerfilUsuario.ADMIN and payload.campus_id != current_user.campus_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: restrito ao seu campus")

    stmt = select(Usuario).where(Usuario.email == payload.email)
    if db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ja cadastrado no sistema")

    usuario = Usuario(
        campus_id=payload.campus_id,
        nome=payload.nome,
        email=payload.email,
        senha_hash=get_password_hash(payload.senha),
        perfil=payload.perfil,
        ativo=True,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito de unicidade ao cadastrar usuario")
    db.refresh(usuario)
    return usuario

