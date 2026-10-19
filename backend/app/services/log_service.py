"""
Servico unificado de auditoria e registro de operacoes no SIGAAS.
Gera trilhas rastreaveis em log_alocacao com snapshot_evento e isolamento de campus.
"""

from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session

from app.models.alocacao import Horario, LogAlocacao
from app.models.enums import TipoEventoLog
from app.models.usuario import Usuario


def registrar_evento(
    db: Session,
    tipo: Union[TipoEventoLog, str],
    usuario: Union[Usuario, int],
    campus_id: Optional[int] = None,
    entidade: Optional[str] = None,
    entidade_id: Optional[int] = None,
    detalhes: Optional[str] = None,
    horario_id: Optional[int] = None,
    snapshot_extra: Optional[Dict[str, Any]] = None,
) -> LogAlocacao:
    """Registra evento de auditoria padronizado em log_alocacao."""
    usuario_id = usuario.id if isinstance(usuario, Usuario) else int(usuario)
    tipo_evento = tipo if isinstance(tipo, TipoEventoLog) else TipoEventoLog(tipo)

    if campus_id is None and horario_id is not None:
        horario = db.get(Horario, horario_id)
        if horario is not None:
            campus_id = horario.campus_id

    snapshot: Dict[str, Any] = {}
    if entidade:
        snapshot["entidade"] = entidade
    if entidade_id is not None:
        snapshot["entidade_id"] = entidade_id
    if snapshot_extra:
        snapshot.update(snapshot_extra)

    log = LogAlocacao(
        campus_id=campus_id,
        horario_id=horario_id,
        tipo_evento=tipo_evento,
        usuario_responsavel=usuario_id,
        snapshot_evento=snapshot if snapshot else None,
        detalhes=detalhes,
    )
    db.add(log)
    db.flush()
    return log
