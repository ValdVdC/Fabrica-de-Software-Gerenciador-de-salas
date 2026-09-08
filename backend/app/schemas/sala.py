"""
Schemas Pydantic v2 para a entidade Sala.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.enums import TipoSala, Turno


class SalaBase(BaseModel):
    campus_id: int = Field(..., gt=0, description="ID do campus")
    bloco: str = Field(..., min_length=1, max_length=50, description="Bloco predial")
    numero: str = Field(..., min_length=1, max_length=50, description="Identificador da sala")
    tipo: TipoSala = Field(..., description="Tipo da sala")
    capacidade: int = Field(..., gt=0, le=5000, description="Capacidade maxima de alunos")
    turnos_disponiveis: list[Turno] = Field(default_factory=list, description="Turnos disponiveis")

    @field_validator("bloco", "numero", mode="before")
    @classmethod
    def validar_nao_vazio(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Campo nao pode ser vazio ou composto apenas por espacos")
        return v


class SalaCreate(SalaBase):
    pass


class SalaRead(SalaBase):
    id: int
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
