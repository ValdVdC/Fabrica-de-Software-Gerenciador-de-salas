"""Schemas Pydantic v2 para os indicadores consolidados do Dashboard (Sprint 07)."""

from typing import List
from pydantic import BaseModel, Field

from app.schemas.log import LogRead


class SugestoesPorStatusRead(BaseModel):
    pendente: int = Field(default=0, ge=0, description="Total de sugestoes pendentes")
    aprovado: int = Field(default=0, ge=0, description="Total de sugestoes aprovadas")
    rejeitado: int = Field(default=0, ge=0, description="Total de sugestoes rejeitadas")
    total: int = Field(default=0, ge=0, description="Total geral de sugestoes")


class DashboardResumoRead(BaseModel):
    salas_ativas: int = Field(..., ge=0, description="Total de salas ativas no escopo")
    turmas: int = Field(..., ge=0, description="Total de turmas no escopo")
    horarios: int = Field(..., ge=0, description="Total de horarios alocados no escopo")
    sugestoes: SugestoesPorStatusRead = Field(..., description="Contagem de sugestoes por status")
    vagas_recuperadas: int = Field(..., ge=0, description="Assentos liberados por remanejamentos aprovados")
    eventos_recentes: List[LogRead] = Field(default_factory=list, description="Ultimos eventos de auditoria")


class OcupacaoPorDiaRead(BaseModel):
    dia_semana: int = Field(..., ge=0, le=6, description="Dia da semana (0=Domingo a 6=Sabado)")
    total_horarios: int = Field(..., ge=0, description="Quantidade de horarios alocados no dia")


class OcupacaoPorTurnoRead(BaseModel):
    turno: str = Field(..., description="Turno (matutino, vespertino, noturno, integral)")
    total_horarios: int = Field(..., ge=0, description="Quantidade de horarios alocados no turno")


class DashboardOcupacaoRead(BaseModel):
    por_dia_semana: List[OcupacaoPorDiaRead] = Field(..., description="Ocupacao por dia da semana (0 a 6)")
    por_turno: List[OcupacaoPorTurnoRead] = Field(..., description="Ocupacao por turno")
