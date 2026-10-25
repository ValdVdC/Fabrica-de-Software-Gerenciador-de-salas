"""Schemas Pydantic v2 para a entidade Turma."""
from typing import Optional
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


class TurmaUpdate(BaseModel):
    professor_id: Optional[int] = Field(default=None, description="ID do professor ou null para desvincular")
    turno_preferido: Optional[Turno] = Field(default=None, description="Turno preferencial")
    model_config = ConfigDict(extra="forbid")

    @field_validator("professor_id")
    @classmethod
    def validar_professor_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("ID do professor deve ser positivo")
        return v


class TurmaRead(TurmaBase):
    id: int
    num_matriculados: int
    model_config = ConfigDict(from_attributes=True)
