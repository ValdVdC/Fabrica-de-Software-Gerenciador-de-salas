"""
Endpoint RESTful para consulta e auditoria do historico de operacoes (LogAlocacao).
Suporta filtros combinados, paginacao, ordenacao decrescente e isolamento multi-campus.
"""

from datetime import date, datetime, time, timezone
import json
from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.alocacao import LogAlocacao
from app.models.enums import PerfilUsuario, TipoEventoLog
from app.models.usuario import Usuario
from app.schemas.log import LogRead
from app.services.export_service import MAX_EXPORT_ROWS, gerar_csv_streaming

router = APIRouter()

COLUNAS_CSV_LOGS = tuple(LogRead.model_fields.keys())


@router.get("", response_model=List[LogRead])
def listar_logs(
    skip: int = Query(default=0, ge=0, description="Offset de paginacao"),
    limit: int = Query(default=50, ge=1, le=100, description="Limite de registros por pagina"),
    campus_id: Optional[int] = Query(default=None, gt=0, description="Filtro de campus (exclusivo para admin)"),
    tipo_evento: Optional[TipoEventoLog] = Query(default=None, description="Filtro por tipo de evento"),
    usuario_id: Optional[int] = Query(default=None, gt=0, description="Filtro por usuario responsavel"),
    data_inicio: Optional[date] = Query(default=None, description="Data inicial do periodo"),
    data_fim: Optional[date] = Query(default=None, description="Data final do periodo"),
    horario_id: Optional[int] = Query(default=None, gt=0, description="Filtro por ID de horario alocado"),
    formato: Optional[Literal["json", "csv"]] = Query(default=None, description="Formato de retorno (json ou csv)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)
    ),
):
    """Consulta historico de operacoes com filtros combinados, isolamento de campus e exportacao CSV."""
    if data_inicio and data_fim and data_fim < data_inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_fim deve ser maior ou igual a data_inicio",
        )

    stmt = select(LogAlocacao)

    if current_user.perfil == PerfilUsuario.ADMIN:
        if campus_id is not None:
            stmt = stmt.where(LogAlocacao.campus_id == campus_id)
    else:
        stmt = stmt.where(LogAlocacao.campus_id == current_user.campus_id)

    if tipo_evento is not None:
        stmt = stmt.where(LogAlocacao.tipo_evento == tipo_evento)

    if usuario_id is not None:
        stmt = stmt.where(LogAlocacao.usuario_responsavel == usuario_id)

    if horario_id is not None:
        stmt = stmt.where(LogAlocacao.horario_id == horario_id)

    if data_inicio is not None:
        dt_inicio = datetime.combine(data_inicio, time.min).replace(tzinfo=timezone.utc)
        stmt = stmt.where(LogAlocacao.timestamp >= dt_inicio)

    if data_fim is not None:
        dt_fim = datetime.combine(data_fim, time.max).replace(tzinfo=timezone.utc)
        stmt = stmt.where(LogAlocacao.timestamp <= dt_fim)

    limite_efetivo = MAX_EXPORT_ROWS if formato == "csv" else limit
    offset_efetivo = 0 if formato == "csv" else skip
    stmt = stmt.order_by(LogAlocacao.timestamp.desc(), LogAlocacao.id.desc()).offset(offset_efetivo).limit(limite_efetivo)
    registros = db.scalars(stmt).all()

    if formato == "csv":
        linhas_csv = (
            {
                "id": reg.id,
                "campus_id": reg.campus_id,
                "horario_id": reg.horario_id,
                "tipo_evento": reg.tipo_evento.value if hasattr(reg.tipo_evento, "value") else str(reg.tipo_evento),
                "usuario_responsavel": reg.usuario_responsavel,
                "detalhes": reg.detalhes,
                "snapshot_evento": json.dumps(reg.snapshot_evento, ensure_ascii=False) if reg.snapshot_evento else "",
                "timestamp": reg.timestamp.isoformat() if reg.timestamp else "",
            }
            for reg in registros
        )
        return gerar_csv_streaming(linhas_csv, COLUNAS_CSV_LOGS, nome_arquivo="historico_logs.csv")

    return registros
