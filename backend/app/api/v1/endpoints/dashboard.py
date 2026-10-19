"""
Endpoints REST para indicadores consolidados do Dashboard (Sprint 07 - Historia 1).
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.dashboard import DashboardOcupacaoRead, DashboardResumoRead
from app.services.dashboard_service import (
    obter_ocupacao_dashboard,
    obter_resumo_dashboard,
    resolver_escopo_campus,
)

router = APIRouter()


@router.get("/resumo", response_model=DashboardResumoRead)
def get_dashboard_resumo(
    campus_id: Optional[int] = Query(
        default=None, gt=0, description="Filtro de campus (exclusivo para admin)"
    ),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)
    ),
):
    """Retorna indicadores consolidados de salas ativas, turmas, horarios, sugestoes, vagas e logs."""
    escopo_campus = resolver_escopo_campus(current_user, campus_id)
    return obter_resumo_dashboard(db=db, campus_id=escopo_campus)


@router.get("/ocupacao", response_model=DashboardOcupacaoRead)
def get_dashboard_ocupacao(
    campus_id: Optional[int] = Query(
        default=None, gt=0, description="Filtro de campus (exclusivo para admin)"
    ),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)
    ),
):
    """Retorna distribuicao de horarios alocados por dia da semana (0 a 6) e por turno."""
    escopo_campus = resolver_escopo_campus(current_user, campus_id)
    return obter_ocupacao_dashboard(db=db, campus_id=escopo_campus)
