"""Schemas Pydantic v2 para requisicoes e respostas de autenticacao."""
from pydantic import BaseModel, Field
from app.schemas.usuario import UsuarioRead


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, description="Email institucional")
    senha: str = Field(..., min_length=1, description="Senha do usuario")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioRead
