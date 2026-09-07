"""
Schemas Pydantic v2 para a entidade Usuario.
"""

from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PerfilUsuario


class UsuarioBase(BaseModel):
    campus_id: int = Field(..., gt=0, description="ID do campus de lotacao")
    nome: str = Field(..., min_length=2, max_length=150, description="Nome do usuario")
    email: str = Field(..., min_length=5, max_length=255, description="Email institucional")
    perfil: PerfilUsuario = Field(..., description="Perfil de acesso")


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, description="Senha de acesso")


class UsuarioRead(UsuarioBase):
    id: int
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
