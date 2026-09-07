"""
Schemas Pydantic v2 para a entidade Sala.
"""

from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import TipoSala, Turno


class SalaBase(BaseModel):
    campus_id: int = Field(..., gt=0, description="ID do campus")
    bloco: str = Field(..., max_length=50, description="Bloco predial")
    numero: str = Field(..., max_length=50, description="Identificador da sala")
    tipo: TipoSala = Field(..., description="Tipo da sala")
    capacidade: int = Field(..., gt=0, description="Capacidade maxima de alunos")
    turnos_disponiveis: list[Turno] = Field(default_factory=list, description="Turnos disponiveis")


class SalaCreate(SalaBase):
    pass


class SalaRead(SalaBase):
    id: int
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
