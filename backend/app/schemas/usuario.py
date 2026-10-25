"""
Schemas Pydantic v2 para a entidade Usuario.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.enums import PerfilUsuario


class UsuarioBase(BaseModel):
    campus_id: int = Field(..., gt=0, description="ID do campus de lotacao")
    nome: str = Field(..., min_length=2, max_length=150, description="Nome do usuario")
    email: EmailStr = Field(..., max_length=255, description="Email institucional")
    perfil: PerfilUsuario = Field(..., description="Perfil de acesso")


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, description="Senha de acesso")


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150, description="Nome do usuario")
    email: EmailStr | None = Field(default=None, max_length=255, description="Email institucional")
    perfil: PerfilUsuario | None = Field(default=None, description="Perfil de acesso")
    ativo: bool | None = Field(default=None, description="Status do usuario")
    model_config = ConfigDict(extra="forbid")


class UsuarioRead(UsuarioBase):
    id: int
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
