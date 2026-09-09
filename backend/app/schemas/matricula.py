"""Schemas Pydantic v2 para a entidade Matricula."""
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class MatriculaBase(BaseModel):
    aluno_id: int = Field(..., gt=0, description="ID do aluno")
    turma_id: int = Field(..., gt=0, description="ID da turma")


class MatriculaCreate(MatriculaBase):
    model_config = ConfigDict(extra="forbid")


class MatriculaRead(MatriculaBase):
    id: int
    data_matricula: date
    status: str
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
