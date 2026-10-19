"""Servico de consultas e agregacoes SQL para Relatorios (Sprint 07 - Historia 2)."""

from datetime import date, datetime, time, timezone
from typing import List, Optional
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased

from app.models.alocacao import Horario
from app.models.enums import StatusSugestao, TipoSala
from app.models.ia import SugestaoRemanejamento
from app.models.sala import Sala
from app.models.usuario import Usuario
from app.schemas.relatorio import RelatorioOcupacaoSalaRead, RelatorioRemanejamentoRead

DIAS_LETIVOS_SEMANA = 5
COLUNAS_CSV_OCUPACAO = tuple(RelatorioOcupacaoSalaRead.model_fields.keys())
COLUNAS_CSV_REMANEJAMENTOS = tuple(RelatorioRemanejamentoRead.model_fields.keys())


def _calcular_taxa_ocupacao_semanal(
    turnos_disponiveis: Optional[list[str]], quantidade_horarios: int
) -> float:
    """Calcula percentual de ocupacao semanal com base nos turnos disponiveis da sala."""
    if quantidade_horarios <= 0:
        return 0.0
    turnos_unicos = {str(t).strip().lower() for t in (turnos_disponiveis or []) if str(t).strip()}
    num_turnos = len(turnos_unicos) if turnos_unicos else 3
    slots_semanais = max(num_turnos * DIAS_LETIVOS_SEMANA, DIAS_LETIVOS_SEMANA)
    return round(min((quantidade_horarios / slots_semanais) * 100.0, 100.0), 2)


def obter_relatorio_ocupacao_salas(
    db: Session,
    campus_id: Optional[int] = None,
    bloco: Optional[str] = None,
    tipo: Optional[TipoSala] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[RelatorioOcupacaoSalaRead]:
    """Agrega ocupacao de salas via SQL LEFT OUTER JOIN e GROUP BY sem N+1."""
    stmt = (
        select(Sala, func.count(Horario.id).label("quantidade_horarios"))
        .outerjoin(Horario, and_(Horario.sala_id == Sala.id, Horario.campus_id == Sala.campus_id))
        .where(Sala.ativo.is_(True))
    )
    if campus_id is not None:
        stmt = stmt.where(Sala.campus_id == campus_id)
    if bloco is not None and bloco.strip():
        stmt = stmt.where(func.lower(Sala.bloco) == bloco.strip().lower())
    if tipo is not None:
        stmt = stmt.where(Sala.tipo == tipo)

    stmt = (
        stmt.group_by(Sala.id)
        .order_by(Sala.bloco.asc(), Sala.numero.asc(), Sala.id.asc())
        .offset(skip)
        .limit(limit)
    )
    resultado: List[RelatorioOcupacaoSalaRead] = []
    for sala_obj, qtd in db.execute(stmt).all():
        qtd_int = int(qtd or 0)
        resultado.append(
            RelatorioOcupacaoSalaRead(
                sala_id=sala_obj.id,
                campus_id=sala_obj.campus_id,
                sala=f"{sala_obj.bloco}-{sala_obj.numero}",
                bloco=sala_obj.bloco,
                numero=sala_obj.numero,
                tipo=sala_obj.tipo,
                capacidade=sala_obj.capacidade,
                quantidade_horarios=qtd_int,
                taxa_ocupacao_semanal=_calcular_taxa_ocupacao_semanal(sala_obj.turnos_disponiveis, qtd_int),
            )
        )
    return resultado


def obter_relatorio_remanejamentos(
    db: Session,
    campus_id: Optional[int] = None,
    status_filtro: Optional[StatusSugestao] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[RelatorioRemanejamentoRead]:
    """Consulta sugestoes de remanejamento com sala origem, sala destino e decisor em 1 query SQL."""
    sala_origem = aliased(Sala)
    sala_destino = aliased(Sala)
    decisor = aliased(Usuario)

    stmt = (
        select(
            SugestaoRemanejamento,
            Horario.campus_id.label("campus_id"),
            sala_origem.bloco.label("origem_bloco"),
            sala_origem.numero.label("origem_numero"),
            sala_origem.capacidade.label("origem_cap"),
            sala_destino.bloco.label("destino_bloco"),
            sala_destino.numero.label("destino_numero"),
            sala_destino.capacidade.label("destino_cap"),
            decisor.nome.label("decisor_nome"),
        )
        .join(Horario, SugestaoRemanejamento.horario_id == Horario.id)
        .join(sala_origem, SugestaoRemanejamento.sala_atual_id == sala_origem.id)
        .join(sala_destino, SugestaoRemanejamento.sala_sugerida_id == sala_destino.id)
        .outerjoin(decisor, SugestaoRemanejamento.aprovado_por == decisor.id)
    )
    if campus_id is not None:
        stmt = stmt.where(Horario.campus_id == campus_id)
    if status_filtro is not None:
        stmt = stmt.where(SugestaoRemanejamento.status == status_filtro)
    if data_inicio is not None:
        stmt = stmt.where(
            SugestaoRemanejamento.criado_em >= datetime.combine(data_inicio, time.min).replace(tzinfo=timezone.utc)
        )
    if data_fim is not None:
        stmt = stmt.where(
            SugestaoRemanejamento.criado_em <= datetime.combine(data_fim, time.max).replace(tzinfo=timezone.utc)
        )

    stmt = stmt.order_by(SugestaoRemanejamento.criado_em.desc(), SugestaoRemanejamento.id.desc()).offset(skip).limit(limit)
    resultado: List[RelatorioRemanejamentoRead] = []
    for row in db.execute(stmt).all():
        sug = row[0]
        resultado.append(
            RelatorioRemanejamentoRead(
                id=sug.id,
                campus_id=row.campus_id,
                horario_id=sug.horario_id,
                status=sug.status,
                sala_origem_id=sug.sala_atual_id,
                sala_origem=f"{row.origem_bloco}-{row.origem_numero}",
                sala_origem_capacidade=row.origem_cap,
                sala_destino_id=sug.sala_sugerida_id,
                sala_destino=f"{row.destino_bloco}-{row.destino_numero}",
                sala_destino_capacidade=row.destino_cap,
                decisor_id=sug.aprovado_por,
                decisor=row.decisor_nome,
                motivo=sug.motivo,
                justificativa=sug.justificativa,
                criado_em=sug.criado_em,
                atualizado_em=sug.atualizado_em,
            )
        )
    return resultado
