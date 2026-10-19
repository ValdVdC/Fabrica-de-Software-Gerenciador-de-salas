"""
Servico de agregacao SQL para o Dashboard (Sprint 07 - Historia 1).
Executa consultas consolidadas via func.count, func.sum e group_by sem N+1.
"""

from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.models.academico import Curso, Disciplina, Turma
from app.models.alocacao import Horario, LogAlocacao
from app.models.enums import PerfilUsuario, StatusSugestao, Turno
from app.models.ia import SugestaoRemanejamento
from app.models.sala import Sala
from app.models.usuario import Usuario
from app.schemas.dashboard import (
    DashboardOcupacaoRead,
    DashboardResumoRead,
    OcupacaoPorDiaRead,
    OcupacaoPorTurnoRead,
    SugestoesPorStatusRead,
)
from app.schemas.log import LogRead


def resolver_escopo_campus(current_user: Usuario, campus_id: Optional[int]) -> Optional[int]:
    """Determina o campus_id efetivo respeitando isolamento multi-tenant (BOLA)."""
    if current_user.perfil == PerfilUsuario.ADMIN:
        return campus_id
    return current_user.campus_id


def obter_resumo_dashboard(db: Session, campus_id: Optional[int] = None) -> DashboardResumoRead:
    """Calcula indicadores consolidados do campus exclusivamente via agregacoes SQL."""
    stmt_salas = select(func.count(Sala.id)).where(Sala.ativo.is_(True))
    if campus_id is not None:
        stmt_salas = stmt_salas.where(Sala.campus_id == campus_id)
    salas_ativas = int(db.scalar(stmt_salas) or 0)

    stmt_turmas = select(func.count(Turma.id))
    if campus_id is not None:
        stmt_turmas = (
            stmt_turmas.join(Disciplina, Turma.disciplina_id == Disciplina.id)
            .join(Curso, Disciplina.curso_id == Curso.id)
            .where(Curso.campus_id == campus_id)
        )
    turmas = int(db.scalar(stmt_turmas) or 0)

    stmt_horarios = select(func.count(Horario.id))
    if campus_id is not None:
        stmt_horarios = stmt_horarios.where(Horario.campus_id == campus_id)
    horarios = int(db.scalar(stmt_horarios) or 0)

    stmt_sugestoes = (
        select(SugestaoRemanejamento.status, func.count(SugestaoRemanejamento.id))
        .join(Horario, SugestaoRemanejamento.horario_id == Horario.id)
    )
    if campus_id is not None:
        stmt_sugestoes = stmt_sugestoes.where(Horario.campus_id == campus_id)
    stmt_sugestoes = stmt_sugestoes.group_by(SugestaoRemanejamento.status)

    contagem_status = {s.value: 0 for s in StatusSugestao}
    for status_row, qtd in db.execute(stmt_sugestoes).all():
        chave = status_row.value if hasattr(status_row, "value") else str(status_row)
        if chave in contagem_status:
            contagem_status[chave] = int(qtd)

    sugestoes_read = SugestoesPorStatusRead(
        pendente=contagem_status[StatusSugestao.PENDENTE.value],
        aprovado=contagem_status[StatusSugestao.APROVADO.value],
        rejeitado=contagem_status[StatusSugestao.REJEITADO.value],
        total=sum(contagem_status.values()),
    )

    sala_atual = aliased(Sala)
    sala_sugerida = aliased(Sala)
    diff_cap = sala_atual.capacidade - sala_sugerida.capacidade
    stmt_vagas = (
        select(func.coalesce(func.sum(diff_cap), 0))
        .select_from(SugestaoRemanejamento)
        .join(Horario, SugestaoRemanejamento.horario_id == Horario.id)
        .join(sala_atual, SugestaoRemanejamento.sala_atual_id == sala_atual.id)
        .join(sala_sugerida, SugestaoRemanejamento.sala_sugerida_id == sala_sugerida.id)
        .where(
            SugestaoRemanejamento.status == StatusSugestao.APROVADO,
            sala_atual.capacidade > sala_sugerida.capacidade,
        )
    )
    if campus_id is not None:
        stmt_vagas = stmt_vagas.where(Horario.campus_id == campus_id)
    vagas_recuperadas = max(0, int(db.scalar(stmt_vagas) or 0))

    stmt_logs = select(LogAlocacao)
    if campus_id is not None:
        stmt_logs = stmt_logs.where(LogAlocacao.campus_id == campus_id)
    stmt_logs = stmt_logs.order_by(LogAlocacao.timestamp.desc(), LogAlocacao.id.desc()).limit(10)
    eventos_recentes = [LogRead.model_validate(log) for log in db.scalars(stmt_logs).all()]

    return DashboardResumoRead(
        salas_ativas=salas_ativas,
        turmas=turmas,
        horarios=horarios,
        sugestoes=sugestoes_read,
        vagas_recuperadas=vagas_recuperadas,
        eventos_recentes=eventos_recentes,
    )


def obter_ocupacao_dashboard(db: Session, campus_id: Optional[int] = None) -> DashboardOcupacaoRead:
    """Agrega contagem de horarios por dia da semana (0..6) e por turno via SQL."""
    stmt_dias = select(Horario.dia_semana, func.count(Horario.id))
    if campus_id is not None:
        stmt_dias = stmt_dias.where(Horario.campus_id == campus_id)
    stmt_dias = stmt_dias.group_by(Horario.dia_semana)

    mapa_dias = {dia: 0 for dia in range(7)}
    for dia_row, qtd in db.execute(stmt_dias).all():
        if dia_row in mapa_dias:
            mapa_dias[dia_row] = int(qtd)

    stmt_turnos = (
        select(Turma.turno_preferido, func.count(Horario.id))
        .join(Turma, Horario.turma_id == Turma.id)
    )
    if campus_id is not None:
        stmt_turnos = stmt_turnos.where(Horario.campus_id == campus_id)
    stmt_turnos = stmt_turnos.group_by(Turma.turno_preferido)

    mapa_turnos = {t.value: 0 for t in Turno}
    for turno_row, qtd in db.execute(stmt_turnos).all():
        chave = turno_row.value if hasattr(turno_row, "value") else str(turno_row)
        if chave in mapa_turnos:
            mapa_turnos[chave] = int(qtd)

    return DashboardOcupacaoRead(
        por_dia_semana=[
            OcupacaoPorDiaRead(dia_semana=d, total_horarios=mapa_dias[d]) for d in range(7)
        ],
        por_turno=[
            OcupacaoPorTurnoRead(turno=t.value, total_horarios=mapa_turnos[t.value]) for t in Turno
        ],
    )
