"""Schemas Pydantic v2 para Relatorios Consolidados (Sprint 07 - Historia 2)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusSugestao, TipoSala


class RelatorioOcupacaoSalaRead(BaseModel):
    sala_id: int = Field(..., description="ID da sala")
    campus_id: int = Field(..., description="ID do campus")
    sala: str = Field(..., description="Identificador composto Bloco-Numero")
    bloco: str = Field(..., description="Bloco da sala")
    numero: str = Field(..., description="Numero da sala")
    tipo: TipoSala = Field(..., description="Tipo da sala")
    capacidade: int = Field(..., gt=0, description="Capacidade da sala")
    quantidade_horarios: int = Field(..., ge=0, description="Total de horarios alocados")
    taxa_ocupacao_semanal: float = Field(..., ge=0.0, le=100.0, description="Percentual de ocupacao semanal")

    model_config = ConfigDict(from_attributes=True)


class RelatorioRemanejamentoRead(BaseModel):
    id: int = Field(..., description="ID da sugestao de remanejamento")
    campus_id: int = Field(..., description="ID do campus")
    horario_id: int = Field(..., description="ID do horario")
    status: StatusSugestao = Field(..., description="Status da sugestao")
    sala_origem_id: int = Field(..., description="ID da sala de origem")
    sala_origem: str = Field(..., description="Identificador da sala de origem")
    sala_origem_capacidade: int = Field(..., gt=0, description="Capacidade da sala de origem")
    sala_destino_id: int = Field(..., description="ID da sala de destino")
    sala_destino: str = Field(..., description="Identificador da sala de destino")
    sala_destino_capacidade: int = Field(..., gt=0, description="Capacidade da sala de destino")
    decisor_id: Optional[int] = Field(default=None, description="ID do usuario decisor")
    decisor: Optional[str] = Field(default=None, description="Nome do usuario decisor")
    motivo: str = Field(..., description="Motivo da sugestao")
    justificativa: Optional[str] = Field(default=None, description="Justificativa da decisao")
    criado_em: datetime = Field(..., description="Data/hora de criacao")
    atualizado_em: datetime = Field(..., description="Data/hora de atualizacao")

    model_config = ConfigDict(from_attributes=True)
