"""
Testes unitarios e de integracao para o motor de alocacao C com OpenMP (Sprint 05).
"""

import pytest
from app.services.motor_service import (
    motor_service,
    SalaC,
    TurmaC,
    TIPO_SALA_REGULAR,
    TIPO_SALA_LABORATORIO,
    TURNO_MATUTINO,
    TURNO_VESPERTINO,
    TURNO_NOTURNO,
    TURNO_MASK_MATUTINO,
    TURNO_MASK_VESPERTINO,
    TURNO_MASK_NOTURNO,
)


def test_versao_motor_c():
    status = motor_service.get_status()
    assert status["status"] == "online"
    assert status["openmp_ativo"] is True
    assert "OpenMP" in status["versao"]


def test_alocacao_best_fit():
    salas = [
        SalaC(id=1, capacidade=60, tipo=TIPO_SALA_REGULAR, turnos_mask=TURNO_MASK_MATUTINO),
        SalaC(id=2, capacidade=40, tipo=TIPO_SALA_REGULAR, turnos_mask=TURNO_MASK_MATUTINO),
    ]
    turmas = [
        TurmaC(
            id=101,
            num_matriculados=35,
            tipo_exigido=TIPO_SALA_REGULAR,
            turno=TURNO_MATUTINO,
            dia_semana_sugerido=0,
            hora_inicio_min=480,  # 08:00
            hora_fim_min=600,     # 10:00
        )
    ]

    resultado, metricas = motor_service.otimizar_alocacao(turmas=turmas, salas=salas, max_threads=1)
    assert len(resultado) == 1
    assert resultado[0]["turma_id"] == 101
    assert resultado[0]["sala_id"] == 2  # Best-Fit: sala de 40 alunos (desperdicio 5 vs 25)
    assert resultado[0]["score_desperdicio"] == 5
    assert metricas["total_alocado"] == 1
    assert metricas["total_pendente"] == 0


def test_bloqueio_sala_lotada():
    salas = [
        SalaC(id=1, capacidade=30, tipo=TIPO_SALA_REGULAR, turnos_mask=TURNO_MASK_MATUTINO),
    ]
    turmas = [
        TurmaC(
            id=102,
            num_matriculados=50,  # Excede capacidade da sala
            tipo_exigido=TIPO_SALA_REGULAR,
            turno=TURNO_MATUTINO,
            dia_semana_sugerido=0,
            hora_inicio_min=480,
            hora_fim_min=600,
        )
    ]

    resultado, metricas = motor_service.otimizar_alocacao(turmas=turmas, salas=salas, max_threads=1)
    assert len(resultado) == 1
    assert resultado[0]["sala_id"] == -1
    assert metricas["total_alocado"] == 0
    assert metricas["total_pendente"] == 1


def test_incompatibilidade_laboratorio():
    salas = [
        SalaC(id=1, capacidade=50, tipo=TIPO_SALA_REGULAR, turnos_mask=TURNO_MASK_MATUTINO),
    ]
    turma_lab = TurmaC(
        id=103,
        num_matriculados=30,
        tipo_exigido=TIPO_SALA_LABORATORIO,
        turno=TURNO_MATUTINO,
        dia_semana_sugerido=1,  # Terca
        hora_inicio_min=480,
        hora_fim_min=600,
    )

    # Nao pode alocar em sala regular
    resultado, metricas = motor_service.otimizar_alocacao(turmas=[turma_lab], salas=salas, max_threads=1)
    assert resultado[0]["sala_id"] == -1
    assert metricas["total_pendente"] == 1

    # Adiciona sala de laboratorio compatível
    salas.append(SalaC(id=2, capacidade=50, tipo=TIPO_SALA_LABORATORIO, turnos_mask=TURNO_MASK_MATUTINO))
    resultado2, metricas2 = motor_service.otimizar_alocacao(turmas=[turma_lab], salas=salas, max_threads=1)
    assert resultado2[0]["sala_id"] == 2
    assert metricas2["total_alocado"] == 1


def test_incompatibilidade_turno():
    salas = [
        SalaC(id=1, capacidade=50, tipo=TIPO_SALA_REGULAR, turnos_mask=TURNO_MASK_MATUTINO),
    ]
    turma_noite = TurmaC(
        id=104,
        num_matriculados=30,
        tipo_exigido=TIPO_SALA_REGULAR,
        turno=TURNO_NOTURNO,
        dia_semana_sugerido=2,  # Quarta
        hora_inicio_min=1140,   # 19:00
        hora_fim_min=1260,     # 21:00
    )

    resultado, metricas = motor_service.otimizar_alocacao(turmas=[turma_noite], salas=salas, max_threads=1)
    assert resultado[0]["sala_id"] == -1
    assert metricas["total_pendente"] == 1


def test_nao_sobreposicao_horario():
    salas = [
        SalaC(id=1, capacidade=50, tipo=TIPO_SALA_REGULAR, turnos_mask=TURNO_MASK_MATUTINO),
    ]
    turmas = [
        TurmaC(id=201, num_matriculados=30, tipo_exigido=TIPO_SALA_REGULAR, turno=TURNO_MATUTINO, dia_semana_sugerido=0, hora_inicio_min=480, hora_fim_min=600),
        TurmaC(id=202, num_matriculados=30, tipo_exigido=TIPO_SALA_REGULAR, turno=TURNO_MATUTINO, dia_semana_sugerido=0, hora_inicio_min=540, hora_fim_min=660),
    ]

    resultado, metricas = motor_service.otimizar_alocacao(turmas=turmas, salas=salas, max_threads=1)
    # Apenas uma turma pode ocupar a sala 1 no mesmo horario
    alocados = [r for r in resultado if r["sala_id"] == 1]
    assert len(alocados) == 1
    assert metricas["total_alocado"] == 1
    assert metricas["total_pendente"] == 1


def test_speedup_concorrente():
    metricas = motor_service.executar_benchmark(num_turmas=100, num_salas=40, num_threads=4)
    assert metricas["threads_utilizadas"] == 4
    assert metricas["tempo_sequencial_ms"] > 0
    assert metricas["tempo_paralelo_ms"] > 0
    assert metricas["speedup"] >= 1.0
    assert metricas["eficiencia"] > 0
    assert 0.0 <= metricas["fracao_amdahl"] <= 1.0
