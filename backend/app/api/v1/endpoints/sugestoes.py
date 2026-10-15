"""
Endpoints REST para IA Preditiva de Absenteismo e Remanejamento Human-in-the-Loop (Sprint 06).
"""

from datetime import datetime
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_role
from app.db.session import get_db
from app.models.academico import Turma
from app.models.alocacao import Horario, LogAlocacao
from app.models.enums import PerfilUsuario, StatusSugestao, TipoEventoLog
from app.models.ia import SugestaoRemanejamento
from app.models.usuario import Usuario
from app.schemas.ia import (
    AnaliseIARequest,
    AnaliseIAResponse,
    SugestaoAprovacaoUpdate,
    SugestaoRemanejamentoRead,
)
from app.services.ia_service import (
    converter_sugestao_para_read,
    gerar_sugestoes_remanejamento,
)

router = APIRouter()
ia_router = APIRouter()


@router.get("", response_model=List[SugestaoRemanejamentoRead])
def listar_sugestoes(
    status_filtro: Optional[StatusSugestao] = Query(None, alias="status", description="Filtrar por status"),
    campus_id: Optional[int] = Query(None, gt=0, description="Filtrar por campus (restrito a admin)"),
    skip: int = Query(0, ge=0, description="Deslocamento de paginacao"),
    limit: int = Query(50, ge=1, le=100, description="Limite de registros por pagina"),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR)),
    db: Session = Depends(get_db),
):
    """
    Lista sugestoes de remanejamento ordenadas por criacao mais recente,
    respeitando isolamento multi-campus (coordenadores so acessam seu campus).
    """
    stmt = (
        select(SugestaoRemanejamento)
        .join(SugestaoRemanejamento.horario)
        .options(
            joinedload(SugestaoRemanejamento.horario).joinedload(Horario.turma).joinedload(Turma.disciplina),
            joinedload(SugestaoRemanejamento.sala_atual),
            joinedload(SugestaoRemanejamento.sala_sugerida),
        )
    )

    # Isolamento multi-campus
    if current_user.perfil != PerfilUsuario.ADMIN:
        stmt = stmt.where(Horario.campus_id == current_user.campus_id)
    elif campus_id is not None:
        stmt = stmt.where(Horario.campus_id == campus_id)

    if status_filtro is not None:
        stmt = stmt.where(SugestaoRemanejamento.status == status_filtro)

    stmt = stmt.order_by(SugestaoRemanejamento.criado_em.desc()).offset(skip).limit(limit)
    sugestoes = db.scalars(stmt).all()

    return [converter_sugestao_para_read(s) for s in sugestoes]


@router.patch("/{sugestao_id}", response_model=SugestaoRemanejamentoRead)
def aprovar_ou_rejeitar_sugestao(
    sugestao_id: int,
    payload: SugestaoAprovacaoUpdate,
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR)),
    db: Session = Depends(get_db),
):
    """
    Aprovacao ou rejeicao humana (Human-in-the-Loop) de sugestao de remanejamento.
    Em caso de aprovacao: atualiza atomicamente a sala do horario e registra log de auditoria.
    """
    stmt = (
        select(SugestaoRemanejamento)
        .where(SugestaoRemanejamento.id == sugestao_id)
        .options(
            joinedload(SugestaoRemanejamento.horario).joinedload(Horario.turma).joinedload(Turma.disciplina),
            joinedload(SugestaoRemanejamento.sala_atual),
            joinedload(SugestaoRemanejamento.sala_sugerida),
        )
    )
    sugestao = db.scalar(stmt)
    if not sugestao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sugestao nao encontrada",
        )

    # Mitigacao de BOLA/IDOR: Coordenador nao pode alterar sugestao de outro campus
    if current_user.perfil != PerfilUsuario.ADMIN and sugestao.horario.campus_id != current_user.campus_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sugestao nao encontrada",
        )

    # Estado imutavel: apenas sugestoes PENDENTES podem ser decididas
    if sugestao.status != StatusSugestao.PENDENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sugestao ja foi processada anteriormente com status '{sugestao.status.value}'",
        )

    horario = sugestao.horario
    sala_anterior_id = horario.sala_id

    if payload.status == StatusSugestao.APROVADO:
        # Validacao de integridade: checa se a sala sugerida permanece desocupada
        conflito = db.scalar(
            select(Horario).where(
                Horario.sala_id == sugestao.sala_sugerida_id,
                Horario.dia_semana == horario.dia_semana,
                Horario.hora_inicio < horario.hora_fim,
                Horario.hora_fim > horario.hora_inicio,
                Horario.id != horario.id,
            )
        )
        if conflito:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sala sugerida nao esta mais disponivel no horario especificado",
            )

        # Atualizacao atomica da sala do horario
        horario.sala_id = sugestao.sala_sugerida_id

        # Atualiza a sugestao
        sugestao.status = StatusSugestao.APROVADO
        sugestao.aprovado_por = current_user.id
        sugestao.justificativa = payload.justificativa
        sugestao.atualizado_em = datetime.now()

        # Trilha de auditoria em log_alocacao
        log = LogAlocacao(
            horario_id=horario.id,
            tipo_evento=TipoEventoLog.ALTERACAO,
            usuario_responsavel=current_user.id,
            snapshot_evento={
                "sugestao_id": sugestao.id,
                "sala_anterior_id": sala_anterior_id,
                "nova_sala_id": sugestao.sala_sugerida_id,
            },
            detalhes=f"Remanejamento aprovado por usuario {current_user.id}: sala {sala_anterior_id} -> {sugestao.sala_sugerida_id}",
        )
        db.add(log)

    elif payload.status == StatusSugestao.REJEITADO:
        sugestao.status = StatusSugestao.REJEITADO
        sugestao.aprovado_por = current_user.id
        sugestao.justificativa = payload.justificativa
        sugestao.atualizado_em = datetime.now()

    db.commit()
    db.refresh(sugestao)
    return converter_sugestao_para_read(sugestao)


def _executar_analise(
    payload: Optional[AnaliseIARequest],
    current_user: Usuario,
    db: Session,
) -> AnaliseIAResponse:
    """Funcao auxiliar compartilhada para disparar analise de IA."""
    if payload is None:
        payload = AnaliseIARequest()

    if current_user.perfil != PerfilUsuario.ADMIN:
        campus_alvo = current_user.campus_id
    else:
        campus_alvo = payload.campus_id

    inicio = time.perf_counter()

    sugestoes = gerar_sugestoes_remanejamento(
        db=db,
        campus_id=campus_alvo,
        periodo_letivo=payload.periodo_letivo,
        limiar_ociosidade=payload.limiar_ociosidade,
    )

    tempo_ms = (time.perf_counter() - inicio) * 1000

    # Total de turmas analisadas
    stmt_turmas = select(Turma)
    if campus_alvo is not None:
        stmt_turmas = stmt_turmas.join(Horario, Horario.turma_id == Turma.id).where(Horario.campus_id == campus_alvo)
    if payload.periodo_letivo:
        stmt_turmas = stmt_turmas.where(Turma.periodo_letivo == payload.periodo_letivo)
    total_turmas = len(db.scalars(stmt_turmas).unique().all())

    return AnaliseIAResponse(
        total_turmas_analisadas=total_turmas,
        total_sugestoes_geradas=len(sugestoes),
        sugestoes=[converter_sugestao_para_read(s) for s in sugestoes],
        tempo_processamento_ms=round(tempo_ms, 2),
    )


@router.post("/analisar", response_model=AnaliseIAResponse)
def disparar_analise_ia_sugestoes(
    payload: Optional[AnaliseIARequest] = None,
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR)),
    db: Session = Depends(get_db),
):
    """Dispara a rotina de inferencia e insercao de sugestoes pendentes via /sugestoes/analisar."""
    return _executar_analise(payload, current_user, db)


@ia_router.post("/analisar", response_model=AnaliseIAResponse)
def disparar_analise_ia(
    payload: Optional[AnaliseIARequest] = None,
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR)),
    db: Session = Depends(get_db),
):
    """Dispara a rotina de inferencia e insercao de sugestoes pendentes via /ia/analisar."""
    return _executar_analise(payload, current_user, db)
