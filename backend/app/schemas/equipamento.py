"""Schemas Pydantic v2 para as entidades Equipamento e SalaEquipamento."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EquipamentoBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100, description="Nome do equipamento")
    descricao: Optional[str] = Field(None, max_length=255, description="Descricao complementar")

    @field_validator("nome", mode="before")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Nome do equipamento deve ter pelo menos 2 caracteres validos")
        return v


class EquipamentoCreate(EquipamentoBase):
    pass


class EquipamentoRead(EquipamentoBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SalaEquipamentoBase(BaseModel):
    equipamento_id: int = Field(..., gt=0, description="ID do equipamento")
    quantidade: int = Field(..., gt=0, le=1000, description="Quantidade alocada na sala")


class SalaEquipamentoCreate(SalaEquipamentoBase):
    pass


class SalaEquipamentoRead(SalaEquipamentoBase):
    sala_id: int
    model_config = ConfigDict(from_attributes=True)
