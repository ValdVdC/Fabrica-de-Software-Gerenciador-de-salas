"""
Endpoints para Alocacao Inteligente de Salas via Motor C com OpenMP (Sprint 05).
"""

import re
from datetime import time
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_role
from app.db.session import get_db
from app.models.academico import Curso, Disciplina, Turma
from app.models.alocacao import Horario, LogAlocacao
from app.models.enums import PerfilUsuario, TipoEventoLog, TipoSala, Turno
from app.models.sala import Sala
from app.models.usuario import Usuario
from app.schemas.alocacao import (
    AlocacaoBenchmarkRequest,
    AlocacaoBenchmarkResponse,
    AlocacaoItemResponse,
    AlocacaoOtimizarRequest,
    AlocacaoOtimizarResponse,
    MetricasAlocacaoResponse,
)
from app.services.motor_service import (
    TIPO_SALA_AUDITORIO,
    TIPO_SALA_LABORATORIO,
    TIPO_SALA_REGULAR,
    TIPO_SALA_REUNIAO,
    TURNO_INTEGRAL,
    TURNO_MASK_INTEGRAL,
    TURNO_MASK_MATUTINO,
    TURNO_MASK_NOTURNO,
    TURNO_MASK_VESPERTINO,
    TURNO_MATUTINO,
    TURNO_NOTURNO,
    TURNO_VESPERTINO,
    SalaC,
    TurmaC,
    motor_service,
)

router = APIRouter()

PADRAO_LAB = re.compile(r"\b(lab|laboratorio|laboratório|pratica|prática)\b", re.IGNORECASE)


def _converter_turno_enum(turno: Turno | str) -> int:
    val = turno.value if hasattr(turno, "value") else str(turno)
    val = val.lower()
    if val == "matutino":
        return TURNO_MATUTINO
    elif val == "vespertino":
        return TURNO_VESPERTINO
    elif val == "noturno":
        return TURNO_NOTURNO
    return TURNO_INTEGRAL


def _calcular_mask_turnos(turnos_disponiveis: list[str]) -> int:
    mask = 0
    if not turnos_disponiveis:
        return TURNO_MASK_MATUTINO | TURNO_MASK_VESPERTINO | TURNO_MASK_NOTURNO

    for t in turnos_disponiveis:
        t_str = str(t).lower()
        if "matutino" in t_str:
            mask |= TURNO_MASK_MATUTINO
        if "vespertino" in t_str:
            mask |= TURNO_MASK_VESPERTINO
        if "noturno" in t_str:
            mask |= TURNO_MASK_NOTURNO
        if "integral" in t_str:
            mask |= TURNO_MASK_INTEGRAL

    return mask if mask > 0 else (TURNO_MASK_MATUTINO | TURNO_MASK_VESPERTINO | TURNO_MASK_NOTURNO)


def _converter_tipo_sala(tipo: TipoSala | str) -> int:
    val = tipo.value if hasattr(tipo, "value") else str(tipo)
    val = val.lower()
    if val == "laboratorio":
        return TIPO_SALA_LABORATORIO
    elif val == "auditorio":
        return TIPO_SALA_AUDITORIO
    elif val == "reuniao":
        return TIPO_SALA_REUNIAO
    return TIPO_SALA_REGULAR


@router.post(
    "/otimizar",
    response_model=AlocacaoOtimizarResponse,
    status_code=status.HTTP_200_OK,
    summary="Executar alocacao inteligente de salas com motor C e paralelismo OpenMP",
)
def otimizar_alocacao_endpoint(
    payload: AlocacaoOtimizarRequest,
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR)),
    db: Session = Depends(get_db),
):
    """Executa a alocacao combinatoria de salas com OpenMP e persiste atomicamente no PostgreSQL."""
    # Blindagem estrita de isolamento multi-campus (SEC-01 / BOLA)
    if current_user.perfil == PerfilUsuario.COORDENADOR:
        if not current_user.campus_id or current_user.campus_id != payload.campus_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: coordenador restrito ao seu proprio campus.",
            )

    # 1. Buscar turmas daquele campus e periodo letivo
    stmt_turmas = (
        select(Turma)
        .join(Disciplina, Turma.disciplina_id == Disciplina.id)
        .join(Curso, Disciplina.curso_id == Curso.id)
        .options(selectinload(Turma.disciplina))
        .where(
            Curso.campus_id == payload.campus_id,
            Turma.periodo_letivo == payload.periodo_letivo,
        )
        .order_by(Turma.id.asc())
    )
    turmas_db = db.scalars(stmt_turmas).all()

    # 2. Buscar salas ativas do campus
    stmt_salas = (
        select(Sala)
        .where(Sala.campus_id == payload.campus_id, Sala.ativo.is_(True))
        .order_by(Sala.capacidade.asc(), Sala.id.asc())
    )
    salas_db = db.scalars(stmt_salas).all()

    if not turmas_db:
        return AlocacaoOtimizarResponse(
            sucesso=True,
            mensagem="Nenhuma turma pendente encontrada para o periodo e campus informados.",
            metricas=MetricasAlocacaoResponse(
                tempo_sequencial_ms=0.0,
                tempo_paralelo_ms=0.0,
                speedup=1.0,
                eficiencia_pct=100.0,
                fracao_amdahl=1.0,
                threads=payload.max_threads,
                total_turmas=0,
                alocadas=0,
                conflitos=0,
            ),
            alocacoes=[],
        )

    if not salas_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma sala ativa cadastrada no campus selecionado.",
        )

    # 3. Preparar structs para o motor C
    turmas_c: List[TurmaC] = []
    mapa_turmas_info: Dict[int, Turma] = {}

    for idx, t in enumerate(turmas_db):
        mapa_turmas_info[t.id] = t
        tipo_exigido = TIPO_SALA_LABORATORIO if (
            PADRAO_LAB.search(t.disciplina.nome) or PADRAO_LAB.search(t.disciplina.codigo)
        ) else TIPO_SALA_REGULAR

        turno_int = _converter_turno_enum(t.turno_preferido)
        dia_sugerido = idx % 5  # Segunda (0) a Sexta (4)

        if turno_int == TURNO_MATUTINO:
            ini_min, fim_min = 480, 600  # 08:00 - 10:00
        elif turno_int == TURNO_VESPERTINO:
            ini_min, fim_min = 840, 960  # 14:00 - 16:00
        elif turno_int == TURNO_NOTURNO:
            ini_min, fim_min = 1140, 1260  # 19:00 - 21:00
        else:
            ini_min, fim_min = 480, 720  # 08:00 - 12:00

        turmas_c.append(
            TurmaC(
                id=t.id,
                num_matriculados=t.num_matriculados,
                tipo_exigido=tipo_exigido,
                turno=turno_int,
                dia_semana_sugerido=dia_sugerido,
                hora_inicio_min=ini_min,
                hora_fim_min=fim_min,
            )
        )

    salas_c: List[SalaC] = []
    mapa_salas_info: Dict[int, Sala] = {}

    for s in salas_db:
        mapa_salas_info[s.id] = s
        salas_c.append(
            SalaC(
                id=s.id,
                capacidade=s.capacidade,
                tipo=_converter_tipo_sala(s.tipo),
                turnos_mask=_calcular_mask_turnos(s.turnos_disponiveis or []),
            )
        )

    # 4. Executar algoritmo de alocacao no motor C
    try:
        alocacoes_c, metricas_c = motor_service.otimizar_alocacao(
            turmas=turmas_c,
            salas=salas_c,
            max_threads=payload.max_threads,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Motor de alocacao C indisponivel: {exc}",
        )

    horarios_novos: List[Horario] = []
    itens_resposta: List[AlocacaoItemResponse] = []

    for item in alocacoes_c:
        t = mapa_turmas_info[item["turma_id"]]
        hora_ini = time(item["hora_inicio_min"] // 60, item["hora_inicio_min"] % 60)
        hora_fim = time(item["hora_fim_min"] // 60, item["hora_fim_min"] % 60)

        if item["sala_id"] > 0:
            s = mapa_salas_info[item["sala_id"]]
            itens_resposta.append(
                AlocacaoItemResponse(
                    turma_id=t.id,
                    disciplina_codigo=t.disciplina.codigo,
                    disciplina_nome=t.disciplina.nome,
                    sala_id=s.id,
                    sala_bloco=s.bloco,
                    sala_numero=s.numero,
                    dia_semana=item["dia_semana"],
                    hora_inicio=hora_ini.strftime("%H:%M"),
                    hora_fim=hora_fim.strftime("%H:%M"),
                    score_desperdicio=item["score_desperdicio"],
                )
            )

            if payload.salvar_no_banco:
                horarios_novos.append(
                    Horario(
                        campus_id=payload.campus_id,
                        turma_id=t.id,
                        sala_id=s.id,
                        dia_semana=item["dia_semana"],
                        hora_inicio=hora_ini,
                        hora_fim=hora_fim,
                    )
                )
        else:
            # Turma com conflito ou sem sala compativel disponivel
            itens_resposta.append(
                AlocacaoItemResponse(
                    turma_id=t.id,
                    disciplina_codigo=t.disciplina.codigo,
                    disciplina_nome=t.disciplina.nome,
                    sala_id=-1,
                    sala_bloco="",
                    sala_numero="",
                    dia_semana=item["dia_semana"],
                    hora_inicio=hora_ini.strftime("%H:%M"),
                    hora_fim=hora_fim.strftime("%H:%M"),
                    score_desperdicio=-1,
                )
            )

    # 5. Persistencia atomica e idempotente no PostgreSQL (SEC-04)
    if payload.salvar_no_banco:
        try:
            # Idempotencia: remove horarios previamente alocados para este lote de turmas
            turmas_ids = [t.id for t in turmas_db]
            if turmas_ids:
                db.execute(delete(Horario).where(Horario.turma_id.in_(turmas_ids)))

            if horarios_novos:
                db.add_all(horarios_novos)
                db.flush()

            # Registro de Auditoria
            log_auditoria = LogAlocacao(
                horario_id=horarios_novos[0].id if horarios_novos else None,
                snapshot_evento={
                    "periodo_letivo": payload.periodo_letivo,
                    "campus_id": payload.campus_id,
                    "metricas": metricas_c,
                    "total_alocados": len(horarios_novos),
                },
                tipo_evento=TipoEventoLog.CRIACAO,
                usuario_responsavel=current_user.id,
                detalhes=(
                    f"Alocacao inteligente OpenMP: {metricas_c['threads_utilizadas']} threads, "
                    f"speedup {metricas_c['speedup']}x, eficiencia {metricas_c['eficiencia']}%, "
                    f"{len(horarios_novos)}/{len(turmas_c)} turmas alocadas."
                ),
            )
            db.add(log_auditoria)
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao persistir transacao de alocacao no PostgreSQL: {exc}",
            )

    metricas_resp = MetricasAlocacaoResponse(
        tempo_sequencial_ms=metricas_c["tempo_sequencial_ms"],
        tempo_paralelo_ms=metricas_c["tempo_paralelo_ms"],
        speedup=metricas_c["speedup"],
        eficiencia_pct=metricas_c["eficiencia"],
        fracao_amdahl=metricas_c["fracao_amdahl"],
        threads=metricas_c["threads_utilizadas"],
        total_turmas=len(turmas_c),
        alocadas=metricas_c["total_alocado"],
        conflitos=metricas_c["total_pendente"],
    )

    return AlocacaoOtimizarResponse(
        sucesso=True,
        mensagem=f"Alocacao executada com sucesso. {metricas_c['total_alocado']} turmas alocadas.",
        metricas=metricas_resp,
        alocacoes=itens_resposta,
    )


@router.post(
    "/benchmark",
    response_model=AlocacaoBenchmarkResponse,
    status_code=status.HTTP_200_OK,
    summary="Executar benchmark cientifico de alocacao com metricas OpenMP (Admin Exclusivo)",
)
def benchmark_alocacao_endpoint(
    payload: AlocacaoBenchmarkRequest,
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN)),
):
    """Executa a rotina de benchmark nos cenarios cientificos (Pequeno, Medio ou Stress)."""
    _ = current_user
    cenario_lower = payload.cenario.lower()
    if cenario_lower == "pequeno":
        num_turmas, num_salas = 20, 10
    elif cenario_lower == "stress":
        num_turmas, num_salas = 500, 150
    else:
        cenario_lower = "medio"
        num_turmas, num_salas = 100, 40

    try:
        metricas = motor_service.executar_benchmark(
            num_turmas=num_turmas,
            num_salas=num_salas,
            num_threads=payload.threads,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Motor de benchmark C indisponivel: {exc}",
        )

    return AlocacaoBenchmarkResponse(
        cenario=cenario_lower,
        num_turmas=num_turmas,
        num_salas=num_salas,
        metricas=MetricasAlocacaoResponse(
            tempo_sequencial_ms=metricas["tempo_sequencial_ms"],
            tempo_paralelo_ms=metricas["tempo_paralelo_ms"],
            speedup=metricas["speedup"],
            eficiencia_pct=metricas["eficiencia"],
            fracao_amdahl=metricas["fracao_amdahl"],
            threads=metricas["threads_utilizadas"],
            total_turmas=num_turmas,
            alocadas=metricas["total_alocado"],
            conflitos=metricas["total_pendente"],
        ),
    )
