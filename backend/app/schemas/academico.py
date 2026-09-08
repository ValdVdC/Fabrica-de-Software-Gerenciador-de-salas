"""Schemas Pydantic v2 para gestao academica (Cursos e Disciplinas)."""
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CursoBase(BaseModel):
    campus_id: int = Field(..., gt=0, description="ID do campus associado")
    nome: str = Field(..., min_length=2, max_length=150, description="Nome do curso")
    codigo: str = Field(..., min_length=2, max_length=30, description="Codigo do curso")

    @field_validator("nome", "codigo")
    @classmethod
    def validar_strings_nao_vazias(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Campo nao pode ser vazio ou conter apenas espacos")
        return s


class CursoCreate(CursoBase):
    pass


class CursoRead(CursoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DisciplinaBase(BaseModel):
    curso_id: int = Field(..., gt=0, description="ID do curso associado")
    nome: str = Field(..., min_length=2, max_length=150, description="Nome da disciplina")
    codigo: str = Field(..., min_length=2, max_length=30, description="Codigo da disciplina")
    carga_horaria: int = Field(..., gt=0, le=1000, description="Carga horaria em horas")

    @field_validator("nome", "codigo")
    @classmethod
    def validar_strings_nao_vazias(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Campo nao pode ser vazio ou conter apenas espacos")
        return s


class DisciplinaCreate(DisciplinaBase):
    pass


class DisciplinaRead(DisciplinaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
