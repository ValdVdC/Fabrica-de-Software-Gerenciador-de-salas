"""Schemas Pydantic v2 para gestao academica (Cursos e Disciplinas)."""
from pydantic import BaseModel, Field, ConfigDict, field_validator


def _sanitizar(v: str, campo: str, upper: bool = False) -> str:
    if not isinstance(v, str):
        raise ValueError(f"{campo} deve ser uma string")
    s = v.strip()
    if upper:
        s = s.upper()
    if len(s) < 2:
        raise ValueError(f"{campo} deve ter no minimo 2 caracteres uteis")
    return s


class CursoBase(BaseModel):
    campus_id: int = Field(..., gt=0, description="ID do campus associado")
    nome: str = Field(..., min_length=2, max_length=150, description="Nome do curso")
    codigo: str = Field(..., min_length=2, max_length=30, description="Codigo do curso")

    @field_validator("nome", mode="before")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        return _sanitizar(v, "Nome")

    @field_validator("codigo", mode="before")
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        return _sanitizar(v, "Codigo", upper=True)


class CursoCreate(CursoBase):
    model_config = ConfigDict(extra="forbid")


class CursoRead(CursoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DisciplinaBase(BaseModel):
    curso_id: int = Field(..., gt=0, description="ID do curso associado")
    nome: str = Field(..., min_length=2, max_length=150, description="Nome da disciplina")
    codigo: str = Field(..., min_length=2, max_length=30, description="Codigo da disciplina")
    carga_horaria: int = Field(..., gt=0, le=1000, description="Carga horaria em horas")

    @field_validator("nome", mode="before")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        return _sanitizar(v, "Nome")

    @field_validator("codigo", mode="before")
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        return _sanitizar(v, "Codigo", upper=True)


class DisciplinaCreate(DisciplinaBase):
    model_config = ConfigDict(extra="forbid")


class DisciplinaRead(DisciplinaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
