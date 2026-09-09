"""Schemas Pydantic v2 para a entidade Turma."""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.enums import Turno


class TurmaBase(BaseModel):
    disciplina_id: int = Field(..., gt=0, description="ID da disciplina ofertada")
    professor_id: int | None = Field(default=None, gt=0, description="ID do professor")
    periodo_letivo: str = Field(..., min_length=4, max_length=20, description="Semestre letivo")
    turno_preferido: Turno = Field(..., description="Turno preferencial")

    @field_validator("periodo_letivo", mode="before")
    @classmethod
    def validar_periodo(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Periodo letivo deve ser uma string")
        s = v.strip()
        if len(s) < 4:
            raise ValueError("Periodo letivo deve conter no minimo 4 caracteres")
        return s


class TurmaCreate(TurmaBase):
    model_config = ConfigDict(extra="forbid")


class TurmaRead(TurmaBase):
    id: int
    num_matriculados: int
    model_config = ConfigDict(from_attributes=True)

