"""
Testes automatizados TDD para o benchmark estatistico do motor de alocacao C com OpenMP (Sprint 09).
Valida caracterizacao formal da heuristica construtiva, calculo estatistico (media, desvio padrao,
speedup e coeficiente de variacao CV < 15%), coleta de metadados de hardware, rastreabilidade de
regressao e exportacao de relatorios estruturados (JSON e Markdown).
"""

import json
import pytest
from app.services.motor_service import (
    CARACTERIZACAO_HEURISTICA,
    MATRIZ_REGRESSAO_BUGS,
    SalaC,
    TurmaC,
    TIPO_SALA_LABORATORIO,
    TIPO_SALA_REGULAR,
    TURNO_MATUTINO,
    TURNO_MASK_MATUTINO,
    motor_service,
)
from scripts.run_benchmarks_ci import (
    calcular_estatisticas_cenario,
    coletar_metadados_ambiente,
    executar_suite_benchmark_estatistico,
    gerar_relatorio_benchmark_json,
    gerar_relatorio_benchmark_markdown,
)


def test_caracterizacao_formal_heuristica_construtiva():
    """Valida a declaracao teorica formal da heuristica e ausencia de garantia de otimo global."""
    assert isinstance(CARACTERIZACAO_HEURISTICA, dict)
    assert (
        CARACTERIZACAO_HEURISTICA["classificacao"]
        == "Heuristica Construtiva Gulosa Deterministica com Priorizacao de Restricoes Rigidas e Capacidade Minima Viavel"
    )
    assert CARACTERIZACAO_HEURISTICA["classe_complexidade"] == "NP-dificil"
    assert CARACTERIZACAO_HEURISTICA["complexidade_temporal"] == "O(T * S)"
    assert CARACTERIZACAO_HEURISTICA["garantia_otimo_global"] is False
    assert "timetabling" in CARACTERIZACAO_HEURISTICA["justificativa_teorica"].lower()

    status = motor_service.get_status()
    assert status["status"] == "online"
    assert "heuristica" in status


def test_calcular_estatisticas_cenario_precisao_matematica():
    """Garante calculo exato de media (mu), desvio padrao amostral (sigma), speedup e CV."""
    tempos_seq = [20.0, 20.2, 19.8, 20.1, 19.9, 20.0, 20.3, 19.7, 20.0, 20.0]
    tempos_par = [5.0, 5.1, 4.9, 5.0, 5.0, 5.1, 4.9, 5.0, 5.0, 5.0]

    stats = calcular_estatisticas_cenario(
        num_turmas=100,
        num_salas=40,
        threads=4,
        tempos_seq_ms=tempos_seq,
        tempos_par_ms=tempos_par,
        total_alocado=99,
        total_pendente=1,
    )

    assert stats["repeticoes"] == 10
    assert stats["mu_seq_ms"] == pytest.approx(20.0, abs=1e-2)
    assert stats["mu_par_ms"] == pytest.approx(5.0, abs=1e-2)
    assert stats["sigma_seq_ms"] > 0.0
    assert stats["sigma_par_ms"] > 0.0
    assert stats["speedup_medio"] == pytest.approx(4.0, abs=1e-2)
    assert stats["cv_seq_pct"] < 15.0
    assert stats["cv_par_pct"] < 15.0
    assert stats["estavel"] is True
    assert 0.0 <= stats["fracao_amdahl"] <= 1.0


def test_calcular_estatisticas_casos_borda_vetor_vazio_e_unitario():
    """Garante seguranca contra divisao por zero ou variancia indefinida com N < 2."""
    stats_vazio = calcular_estatisticas_cenario(10, 5, 4, [], [])
    assert stats_vazio["repeticoes"] == 0
    assert stats_vazio["mu_seq_ms"] == 0.0
    assert stats_vazio["sigma_seq_ms"] == 0.0
    assert stats_vazio["speedup_medio"] == 1.0

    stats_unico = calcular_estatisticas_cenario(10, 5, 4, [12.0], [4.0])
    assert stats_unico["repeticoes"] == 1
    assert stats_unico["sigma_seq_ms"] == 0.0
    assert stats_unico["cv_seq_pct"] == 0.0
    assert stats_unico["speedup_medio"] == 3.0


def test_coleta_metadados_ambiente_hardware_e_compilador():
    """Verifica coleta real das especificacoes de CPU, nucleos, memoria, SO e flags GCC."""
    meta = coletar_metadados_ambiente()
    assert "cpu_modelo" in meta and len(meta["cpu_modelo"]) > 0
    assert meta["nucleos_fisicos"] >= 1
    assert meta["nucleos_logicos"] >= meta["nucleos_fisicos"]
    assert meta["memoria_total_gb"] > 0.0
    assert "sistema_operacional" in meta
    assert "-O3" in meta["flags_compilacao"]
    assert "-fopenmp" in meta["flags_compilacao"]


def test_execucao_benchmark_estatistico_estabilidade_cv():
    """Executa o harness real no motor C para as cargas de 10, 50, 100 e 500 turmas (N=10)."""
    relatorio = executar_suite_benchmark_estatistico(
        cargas=[10, 50, 100, 500],
        repeticoes=10,
        threads=4,
    )

    assert "ambiente" in relatorio
    assert "heuristica" in relatorio
    assert "resultados" in relatorio
    assert "matriz_regressao" in relatorio
    assert len(relatorio["resultados"]) == 4

    cargas_obtidas = [r["num_turmas"] for r in relatorio["resultados"]]
    assert cargas_obtidas == [10, 50, 100, 500]

    for item in relatorio["resultados"]:
        assert item["repeticoes"] == 10
        assert item["mu_seq_ms"] > 0.0
        assert item["mu_par_ms"] > 0.0
        assert item["speedup_medio"] > 0.0
        assert item["cv_seq_pct"] < 15.0
        assert item["cv_par_pct"] < 15.0


def test_matriz_rastreabilidade_bugs_e_regressao():
    """Valida o mapeamento formal de bugs historicos e executa verificacao de regressao."""
    assert len(MATRIZ_REGRESSAO_BUGS) >= 4
    codigos_bugs = {b["id_bug"] for b in MATRIZ_REGRESSAO_BUGS}
    assert {"BUG-HPC-01", "BUG-HPC-02", "BUG-HPC-03", "BUG-HPC-04"}.issubset(codigos_bugs)

    # Regressao BUG-HPC-02: Turma regular nao deve canibalizar laboratorio se houver sala regular
    salas = [
        SalaC(id=1, capacidade=40, tipo=TIPO_SALA_LABORATORIO, turnos_mask=TURNO_MASK_MATUTINO),
        SalaC(id=2, capacidade=50, tipo=TIPO_SALA_REGULAR, turnos_mask=TURNO_MASK_MATUTINO),
    ]
    turma_reg = [
        TurmaC(
            id=501,
            num_matriculados=38,
            tipo_exigido=TIPO_SALA_REGULAR,
            turno=TURNO_MATUTINO,
            dia_semana_sugerido=0,
            hora_inicio_min=480,
            hora_fim_min=600,
        )
    ]
    res, _ = motor_service.otimizar_alocacao(turmas=turma_reg, salas=salas, max_threads=2)
    assert res[0]["sala_id"] == 2


def test_exportacao_relatorios_json_e_markdown(tmp_path):
    """Testa a geracao e persistencia dos artefatos de benchmark em JSON e Markdown."""
    relatorio = executar_suite_benchmark_estatistico(cargas=[10, 50], repeticoes=3, threads=2)

    json_file = tmp_path / "relatorio_benchmark_c.json"
    md_file = tmp_path / "relatorio_benchmark_c.md"

    json_str = gerar_relatorio_benchmark_json(relatorio, filepath=json_file)
    md_str = gerar_relatorio_benchmark_markdown(relatorio, filepath=md_file)

    assert json_file.is_file()
    assert md_file.is_file()
    assert "NaN" not in json_str

    parsed = json.loads(json_str)
    assert parsed["heuristica"]["classe_complexidade"] == "NP-dificil"
    assert "Heuristica Construtiva Gulosa Deterministica" in md_str
    assert "O(T * S)" in md_str
    assert "BUG-HPC-01" in md_str
