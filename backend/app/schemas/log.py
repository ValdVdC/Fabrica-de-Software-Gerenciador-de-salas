"""Schemas Pydantic v2 para a entidade LogAlocacao (Auditoria)."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import TipoEventoLog


class LogRead(BaseModel):
    id: int
    campus_id: Optional[int] = None
    horario_id: Optional[int] = None
    snapshot_evento: Optional[Dict[str, Any]] = None
    tipo_evento: TipoEventoLog
    usuario_responsavel: int
    detalhes: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
