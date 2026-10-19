"""Endpoints REST para Relatorios Consolidados e Exportacao CSV (Sprint 07 - Historias 2 e 4)."""

from datetime import date
from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.enums import PerfilUsuario, StatusSugestao, TipoSala
from app.models.usuario import Usuario
from app.schemas.relatorio import RelatorioOcupacaoSalaRead, RelatorioRemanejamentoRead
from app.services.dashboard_service import resolver_escopo_campus
from app.services.export_service import MAX_EXPORT_ROWS, gerar_csv_streaming
from app.services.relatorio_service import (
    COLUNAS_CSV_OCUPACAO,
    COLUNAS_CSV_REMANEJAMENTOS,
    obter_relatorio_ocupacao_salas,
    obter_relatorio_remanejamentos,
)

router = APIRouter()


@router.get("/ocupacao-salas", response_model=List[RelatorioOcupacaoSalaRead])
def relatorio_ocupacao_salas(
    campus_id: Optional[int] = Query(default=None, gt=0, description="Filtro de campus (exclusivo para admin)"),
    bloco: Optional[str] = Query(default=None, max_length=50, description="Filtro por bloco"),
    tipo: Optional[TipoSala] = Query(default=None, description="Filtro por tipo de sala"),
    formato: Optional[Literal["json", "csv"]] = Query(default=None, description="Formato de retorno (json ou csv)"),
    skip: int = Query(default=0, ge=0, description="Offset de paginacao"),
    limit: int = Query(default=50, ge=1, le=100, description="Limite de registros por pagina"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)
    ),
):
    """Retorna relatorio de ocupacao semanal por sala em JSON ou CSV."""
    escopo_campus = resolver_escopo_campus(current_user, campus_id)
    itens = obter_relatorio_ocupacao_salas(
        db=db,
        campus_id=escopo_campus,
        bloco=bloco,
        tipo=tipo,
        skip=0 if formato == "csv" else skip,
        limit=MAX_EXPORT_ROWS if formato == "csv" else limit,
    )
    if formato == "csv":
        return gerar_csv_streaming(
            (item.model_dump(mode="json") for item in itens),
            COLUNAS_CSV_OCUPACAO,
            nome_arquivo="ocupacao_salas.csv",
        )
    return itens


@router.get("/remanejamentos", response_model=List[RelatorioRemanejamentoRead])
def relatorio_remanejamentos(
    campus_id: Optional[int] = Query(default=None, gt=0, description="Filtro de campus (exclusivo para admin)"),
    status_filtro: Optional[StatusSugestao] = Query(default=None, alias="status", description="Filtro por status"),
    data_inicio: Optional[date] = Query(default=None, description="Data inicial do periodo"),
    data_fim: Optional[date] = Query(default=None, description="Data final do periodo"),
    formato: Optional[Literal["json", "csv"]] = Query(default=None, description="Formato de retorno (json ou csv)"),
    skip: int = Query(default=0, ge=0, description="Offset de paginacao"),
    limit: int = Query(default=50, ge=1, le=100, description="Limite de registros por pagina"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)
    ),
):
    """Retorna relatorio de sugestoes de remanejamento em JSON ou CSV."""
    if data_inicio and data_fim and data_fim < data_inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_fim deve ser maior ou igual a data_inicio",
        )
    escopo_campus = resolver_escopo_campus(current_user, campus_id)
    itens = obter_relatorio_remanejamentos(
        db=db,
        campus_id=escopo_campus,
        status_filtro=status_filtro,
        data_inicio=data_inicio,
        data_fim=data_fim,
        skip=0 if formato == "csv" else skip,
        limit=MAX_EXPORT_ROWS if formato == "csv" else limit,
    )
    if formato == "csv":
        return gerar_csv_streaming(
            (item.model_dump(mode="json") for item in itens),
            COLUNAS_CSV_REMANEJAMENTOS,
            nome_arquivo="remanejamentos.csv",
        )
    return itens
