"""Endpoints para autenticacao e identificacao de usuarios."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.usuario import UsuarioRead
from app.core.security import verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(login_in: LoginRequest, db: Session = Depends(get_db)):
    """Autentica usuario via email e senha, retornando token JWT e perfil."""
    stmt = select(Usuario).where(Usuario.email == login_in.email)
    user = db.scalars(stmt).first()

    if not user or not verify_password(login_in.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inativo no sistema",
        )

    token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "perfil": user.perfil.value,
            "campus_id": user.campus_id,
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        usuario=UsuarioRead.model_validate(user),
    )


@router.get("/me", response_model=UsuarioRead)
def obter_usuario_logado(current_user: Usuario = Depends(get_current_user)):
    """Retorna dados do usuario autenticado pelo token JWT."""
    return current_user
