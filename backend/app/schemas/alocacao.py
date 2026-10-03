"""
Schemas Pydantic para endpoints de alocacao inteligente de salas (Sprint 05).
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class AlocacaoOtimizarRequest(BaseModel):
    periodo_letivo: str = Field(
        ...,
        pattern=r"^\d{4}\.[1-2]$",
        json_schema_extra={"example": "2026.1"},
        description="Periodo letivo de alocacao (formato AAAA.S)",
    )
    campus_id: int = Field(..., ge=1, description="Identificador do campus")
    max_threads: int = Field(default=4, ge=1, le=64, description="Numero de threads OpenMP")
    salvar_no_banco: bool = Field(default=True, description="Indica se os horarios serao persistidos")


class MetricasAlocacaoResponse(BaseModel):
    tempo_sequencial_ms: float = Field(..., description="Tempo de execucao sequencial (1 thread)")
    tempo_paralelo_ms: float = Field(..., description="Tempo de execucao paralelo com OpenMP")
    speedup: float = Field(..., description="Speedup alcancado (T_seq / T_par)")
    eficiencia_pct: float = Field(..., description="Eficiencia computacional percentual (Speedup / k)")
    fracao_amdahl: float = Field(..., description="Fracao paralelizavel teorica pela Lei de Amdahl")
    threads: int = Field(..., description="Threads OpenMP utilizadas")
    total_turmas: int = Field(..., description="Total de turmas processadas")
    alocadas: int = Field(..., description="Total de turmas alocadas com sucesso")
    conflitos: int = Field(..., description="Total de turmas sem sala compativel disponivel")


class AlocacaoItemResponse(BaseModel):
    turma_id: int
    disciplina_codigo: str
    disciplina_nome: str
    sala_id: int
    sala_bloco: Optional[str] = ""
    sala_numero: Optional[str] = ""
    dia_semana: int
    hora_inicio: str
    hora_fim: str
    score_desperdicio: Optional[int] = None


class AlocacaoOtimizarResponse(BaseModel):
    sucesso: bool
    mensagem: str
    metricas: MetricasAlocacaoResponse
    alocacoes: List[AlocacaoItemResponse]


class AlocacaoBenchmarkRequest(BaseModel):
    cenario: Literal["pequeno", "medio", "stress"] = Field(
        default="medio", description="Cenario sintetico: pequeno, medio ou stress"
    )
    threads: int = Field(default=4, ge=1, le=64, description="Numero de threads OpenMP")


class AlocacaoBenchmarkResponse(BaseModel):
    cenario: str
    num_turmas: int
    num_salas: int
    metricas: MetricasAlocacaoResponse
