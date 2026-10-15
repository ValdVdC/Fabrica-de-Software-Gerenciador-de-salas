"""Schemas Pydantic v2 para Inteligencia Artificial e Sugestoes de Remanejamento."""

from datetime import date, datetime, time
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import StatusSugestao


class SugestaoRemanejamentoRead(BaseModel):
    """Schema de leitura para sugestoes de remanejamento com dados enriquecidos."""
    id: int
    horario_id: int
    sala_atual_id: int
    sala_sugerida_id: int
    motivo: str
    justificativa: Optional[str] = None
    status: StatusSugestao
    aprovado_por: Optional[int] = None
    criado_em: datetime
    atualizado_em: datetime

    # Dados contextuais enriquecidos
    prob_ausencia: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probabilidade estimada de absenteismo discente")
    turma_id: Optional[int] = None
    disciplina_codigo: Optional[str] = None
    disciplina_nome: Optional[str] = None
    sala_atual_bloco: Optional[str] = None
    sala_atual_numero: Optional[str] = None
    sala_atual_capacidade: Optional[int] = None
    sala_sugerida_bloco: Optional[str] = None
    sala_sugerida_numero: Optional[str] = None
    sala_sugerida_capacidade: Optional[int] = None
    dia_semana: Optional[int] = Field(None, ge=0, le=6, description="Dia da semana ISO 8601 (0=Segunda a 6=Domingo)")
    hora_inicio: Optional[time] = None
    hora_fim: Optional[time] = None
    campus_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SugestaoAprovacaoUpdate(BaseModel):
    """Schema para decisao humana (aprovacao ou rejeicao) de uma sugestao."""
    status: StatusSugestao = Field(..., description="Status de decisao: aprovado ou rejeitado")
    justificativa: Optional[str] = Field(None, max_length=500, description="Justificativa da decisao")

    @model_validator(mode="after")
    def validar_status_decisao(self):
        if self.status not in (StatusSugestao.APROVADO, StatusSugestao.REJEITADO):
            raise ValueError("Status de atualizacao deve ser 'aprovado' ou 'rejeitado'")
        return self


class AnaliseIARequest(BaseModel):
    """Parametros para execucao da analise preditiva de absenteismo."""
    campus_id: Optional[int] = Field(None, gt=0, description="Filtrar por campus")
    periodo_letivo: Optional[str] = Field(None, max_length=20, description="Filtrar por periodo letivo")
    limiar_ociosidade: float = Field(
        0.40,
        ge=0.0,
        le=1.0,
        description="Limiar minimo de ociosidade estimada para sugerir remanejamento"
    )


class AnaliseIAResponse(BaseModel):
    """Resultado da execucao analitica da IA."""
    total_turmas_analisadas: int
    total_sugestoes_geradas: int
    sugestoes: List[SugestaoRemanejamentoRead]
    tempo_processamento_ms: float


class TreinamentoIAResponse(BaseModel):
    """Metadados do treinamento do pipeline preditivo."""
    total_amostras: int
    metricas: Dict[str, float]
    versao_modelo: str
    caminho_artefato: str


class PrevisaoFaltaRead(BaseModel):
    """Schema de leitura para previsoes de falta."""
    id: int
    turma_id: int
    horario_id: int
    data_prevista: date
    prob_ausencia: float
    versao_modelo: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
