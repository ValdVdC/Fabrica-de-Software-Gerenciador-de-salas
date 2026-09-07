"""
Schemas Pydantic v2 para a entidade Campus.
"""

from pydantic import BaseModel, Field, ConfigDict


class CampusBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, description="Nome do campus")
    cidade: str = Field(..., min_length=2, max_length=100, description="Cidade do campus")
    endereco: str = Field(..., min_length=2, max_length=255, description="Endereco completo")


class CampusCreate(CampusBase):
    pass


class CampusRead(CampusBase):
    id: int
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
