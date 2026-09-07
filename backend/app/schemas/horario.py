"""
Schemas Pydantic v2 para a entidade Horario.
"""

from datetime import time
from pydantic import BaseModel, Field, ConfigDict, model_validator


class HorarioBase(BaseModel):
    campus_id: int = Field(..., gt=0, description="ID do campus")
    turma_id: int = Field(..., gt=0, description="ID da turma vinculada")
    sala_id: int = Field(..., gt=0, description="ID da sala alocada")
    dia_semana: int = Field(..., ge=0, le=6, description="Dia da semana (0=Segunda a 6=Domingo)")
    hora_inicio: time = Field(..., description="Horario de inicio")
    hora_fim: time = Field(..., description="Horario de termino")

    @model_validator(mode="after")
    def validar_ordem_horarios(self):
        if self.hora_inicio >= self.hora_fim:
            raise ValueError("hora_inicio deve ser anterior a hora_fim")
        return self


class HorarioCreate(HorarioBase):
    pass


class HorarioRead(HorarioBase):
    id: int
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
