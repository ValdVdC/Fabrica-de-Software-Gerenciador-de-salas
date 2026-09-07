"""
Schemas Pydantic v2 para a entidade Turma.
"""

from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import Turno


class TurmaBase(BaseModel):
    disciplina_id: int = Field(..., gt=0, description="ID da disciplina ofertada")
    professor_id: int | None = Field(default=None, gt=0, description="ID do professor")
    periodo_letivo: str = Field(..., max_length=20, description="Semestre letivo")
    turno_preferido: Turno = Field(..., description="Turno preferencial")


class TurmaCreate(TurmaBase):
    pass


class TurmaRead(TurmaBase):
    id: int
    num_matriculados: int
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
