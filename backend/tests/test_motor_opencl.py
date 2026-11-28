"""
Testes TDD para infraestrutura e execucao OpenCL do motor de alocacao C (SPEC-M2-01 PR 2a/2b).
"""

import ctypes
import faulthandler
import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

from app.services.motor_service import (
    AlocacaoItemC,
    MetricasAlocacaoC,
    SalaC,
    TIPO_SALA_LABORATORIO,
    TIPO_SALA_REGULAR,
    TURNO_MASK_MATUTINO,
    TURNO_MASK_NOTURNO,
    TURNO_MASK_VESPERTINO,
    TURNO_MATUTINO,
    TURNO_NOTURNO,
    TURNO_VESPERTINO,
    TurmaC,
)

MOTOR_BACKEND_AUTO = 0
MOTOR_BACKEND_CPU_SEQUENCIAL = 1
MOTOR_BACKEND_OPENMP = 2
MOTOR_BACKEND_OPENCL = 3

faulthandler.enable()

MOTOR_DIR = Path(__file__).resolve().parent.parent / "motor_alocacao"


class OpenCLDeviceInfoC(ctypes.Structure):
    _fields_ = [
        ("platform_name", ctypes.c_char * 64),
        ("device_name", ctypes.c_char * 64),
        ("device_type", ctypes.c_char * 16),
        ("opencl_c_version", ctypes.c_char * 32),
        ("compute_units", ctypes.c_uint32),
        ("global_mem_mb", ctypes.c_uint32),
        ("max_work_group_size", ctypes.c_uint64),
    ]


def _opencl_headers_disponiveis() -> bool:
    candidatos = [
        Path("/usr/include/CL/cl.h"),
        Path("/usr/local/include/CL/cl.h"),
        Path("C:/msys64/ucrt64/include/CL/cl.h"),
    ]
    return any(p.exists() for p in candidatos)


def _compilar_biblioteca(destino: Path, usar_opencl: bool) -> ctypes.CDLL:
    motor_c = MOTOR_DIR / "motor.c"
    motor_opencl_c = MOTOR_DIR / "motor_opencl.c"
    assert motor_opencl_c.exists(), "Arquivo backend/motor_alocacao/motor_opencl.c ainda nao existe"

    cmd = [
        "gcc",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        "-std=c11",
        "-O3",
        "-fPIC",
        "-fopenmp",
        "-shared",
    ]
    if usar_opencl:
        cmd.append("-DUSE_OPENCL")
    cmd.extend(["-o", str(destino), str(motor_c), str(motor_opencl_c)])
    if usar_opencl:
        cmd.append("-lOpenCL")

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, f"Falha ao compilar motor C/OpenCL:\n{proc.stderr}"

    if platform.system() == "Windows" and hasattr(os, "add_dll_directory"):
        gcc_path = shutil.which("gcc")
        if gcc_path:
            os.add_dll_directory(str(Path(gcc_path).resolve().parent))

    lib = ctypes.CDLL(str(destino))
    _configurar_assinaturas_opencl(lib)
    return lib


def _configurar_assinaturas_opencl(lib: ctypes.CDLL) -> None:
    lib.obter_status_opencl.restype = ctypes.c_int
    lib.obter_status_opencl.argtypes = [
        ctypes.POINTER(ctypes.c_int32),
        ctypes.c_char_p,
        ctypes.c_int32,
    ]

    lib.obter_dispositivos_opencl.restype = ctypes.c_int
    lib.obter_dispositivos_opencl.argtypes = [
        ctypes.POINTER(OpenCLDeviceInfoC),
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32),
    ]

    lib.motor_opencl_compilar_kernel.restype = ctypes.c_int
    lib.motor_opencl_compilar_kernel.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]

    lib.liberar_recursos_motor.restype = None
    lib.liberar_recursos_motor.argtypes = []

    if hasattr(lib, "otimizar_alocacao_salas_v2"):
        lib.otimizar_alocacao_salas_v2.restype = ctypes.c_int
        lib.otimizar_alocacao_salas_v2.argtypes = [
            ctypes.POINTER(TurmaC),
            ctypes.c_int32,
            ctypes.POINTER(SalaC),
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.POINTER(AlocacaoItemC),
            ctypes.POINTER(MetricasAlocacaoC),
        ]

    if hasattr(lib, "executar_benchmark_cenario_v2"):
        lib.executar_benchmark_cenario_v2.restype = ctypes.c_int
        lib.executar_benchmark_cenario_v2.argtypes = [
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.POINTER(MetricasAlocacaoC),
        ]


def test_alinhamento_structs_v2_64bit():
    assert ctypes.sizeof(MetricasAlocacaoC) == 144
    assert ctypes.alignment(MetricasAlocacaoC) == 8
    assert ctypes.sizeof(OpenCLDeviceInfoC) == 192
    assert ctypes.alignment(OpenCLDeviceInfoC) == 8


def test_descoberta_status_e_dispositivos_opencl(tmp_path: Path):
    ext = ".dll" if platform.system() == "Windows" else ".so"
    usar_opencl = _opencl_headers_disponiveis()
    lib = _compilar_biblioteca(tmp_path / f"motor_opencl_test{ext}", usar_opencl=usar_opencl)

    try:
        disponivel = ctypes.c_int32(-1)
        nome_buf = ctypes.create_string_buffer(64)
        rc = lib.obter_status_opencl(ctypes.byref(disponivel), nome_buf, 64)
        assert rc == 0

        dispositivos = (OpenCLDeviceInfoC * 8)()
        total = ctypes.c_int32(-1)
        rc_dev = lib.obter_dispositivos_opencl(dispositivos, 8, ctypes.byref(total))
        assert rc_dev == 0

        if usar_opencl and disponivel.value == 1:
            assert total.value >= 1
            nome_padrao = nome_buf.value.decode("utf-8", errors="replace")
            assert len(nome_padrao) > 0

            dev0 = dispositivos[0]
            plat = dev0.platform_name.decode("utf-8", errors="replace")
            dev = dev0.device_name.decode("utf-8", errors="replace")
            dtype = dev0.device_type.decode("utf-8", errors="replace")
            ocl_c = dev0.opencl_c_version.decode("utf-8", errors="replace")

            assert len(plat) > 0
            assert len(dev) > 0
            assert dtype in {"GPU", "CPU", "ACCELERATOR"}
            assert "OpenCL" in ocl_c
            assert dev0.compute_units > 0
            assert dev0.global_mem_mb > 0
            assert dev0.max_work_group_size > 0
        else:
            assert disponivel.value == 0
            assert total.value == 0
    finally:
        lib.liberar_recursos_motor()


def test_compilacao_jit_kernel_opencl_e_tratamento_erro(tmp_path: Path):
    if not _opencl_headers_disponiveis():
        pytest.skip("Headers OpenCL nao disponiveis neste ambiente")

    ext = ".dll" if platform.system() == "Windows" else ".so"
    lib = _compilar_biblioteca(tmp_path / f"motor_opencl_jit{ext}", usar_opencl=True)

    try:
        disponivel = ctypes.c_int32(0)
        assert lib.obter_status_opencl(ctypes.byref(disponivel), None, 0) == 0
        if disponivel.value != 1:
            pytest.skip("Nenhum dispositivo OpenCL ativo em runtime neste ambiente")

        kernel_valido = b"__kernel void noop(__global int* out) { if (get_global_id(0) == 0) out[0] = 42; }"
        log_buf = ctypes.create_string_buffer(2048)
        rc_ok = lib.motor_opencl_compilar_kernel(kernel_valido, b"noop", log_buf, 2048)
        assert rc_ok == 0

        kernel_invalido = b"__kernel void quebrado(__global int* out) { erro_de_sintaxe( }"
        log_err = ctypes.create_string_buffer(2048)
        rc_err = lib.motor_opencl_compilar_kernel(kernel_invalido, b"quebrado", log_err, 2048)
        assert rc_err == -3
        assert len(log_err.value) > 0

        assert lib.motor_opencl_compilar_kernel(None, b"noop", None, 0) == -1
        assert lib.motor_opencl_compilar_kernel(b"", b"noop", None, 0) == -1
        assert lib.motor_opencl_compilar_kernel(kernel_valido, b"", None, 0) == -1
    finally:
        lib.liberar_recursos_motor()


def test_validacao_argumentos_nulos_e_limpeza_idempotente(tmp_path: Path):
    ext = ".dll" if platform.system() == "Windows" else ".so"
    usar_opencl = _opencl_headers_disponiveis()
    lib = _compilar_biblioteca(tmp_path / f"motor_opencl_clean{ext}", usar_opencl=usar_opencl)

    assert lib.obter_status_opencl(None, None, 0) == -1
    assert lib.obter_dispositivos_opencl(None, 0, None) == -1

    lib.liberar_recursos_motor()
    lib.liberar_recursos_motor()

    disponivel = ctypes.c_int32(-1)
    rc = lib.obter_status_opencl(ctypes.byref(disponivel), None, 0)
    assert rc == 0
    assert disponivel.value in (0, 1)
    lib.liberar_recursos_motor()


def test_compilacao_fallback_sem_opencl(tmp_path: Path):
    ext = ".dll" if platform.system() == "Windows" else ".so"
    lib = _compilar_biblioteca(tmp_path / f"motor_sem_opencl{ext}", usar_opencl=False)

    disponivel = ctypes.c_int32(-1)
    nome_buf = ctypes.create_string_buffer(64)
    assert lib.obter_status_opencl(ctypes.byref(disponivel), nome_buf, 64) == 0
    assert disponivel.value == 0
    assert nome_buf.value == b""

    dispositivos = (OpenCLDeviceInfoC * 4)()
    total = ctypes.c_int32(-1)
    assert lib.obter_dispositivos_opencl(dispositivos, 4, ctypes.byref(total)) == 0
    assert total.value == 0

    assert lib.motor_opencl_compilar_kernel(b"__kernel void k(){}", b"k", None, 0) == -3
    lib.liberar_recursos_motor()


def _montar_cenario_conflitos():
    mask_todos = TURNO_MASK_MATUTINO | TURNO_MASK_VESPERTINO | TURNO_MASK_NOTURNO
    salas = [
        SalaC(id=1, capacidade=40, tipo=TIPO_SALA_REGULAR, turnos_mask=TURNO_MASK_MATUTINO),
        SalaC(id=2, capacidade=60, tipo=TIPO_SALA_REGULAR, turnos_mask=mask_todos),
        SalaC(id=3, capacidade=35, tipo=TIPO_SALA_LABORATORIO, turnos_mask=mask_todos),
    ]
    turmas = [
        # Mesmo professor 42 em horarios sobrepostos: apenas 1 pode ser alocada
        TurmaC(id=10, num_matriculados=30, tipo_exigido=TIPO_SALA_REGULAR, turno=TURNO_MATUTINO, dia_semana_sugerido=0, hora_inicio_min=480, hora_fim_min=600, professor_id=42),
        TurmaC(id=11, num_matriculados=30, tipo_exigido=TIPO_SALA_REGULAR, turno=TURNO_MATUTINO, dia_semana_sugerido=0, hora_inicio_min=540, hora_fim_min=660, professor_id=42),
        # Lab obrigatorio
        TurmaC(id=12, num_matriculados=30, tipo_exigido=TIPO_SALA_LABORATORIO, turno=TURNO_VESPERTINO, dia_semana_sugerido=1, hora_inicio_min=840, hora_fim_min=960, professor_id=7),
        # Conflito na unica sala lab no mesmo horario
        TurmaC(id=13, num_matriculados=25, tipo_exigido=TIPO_SALA_LABORATORIO, turno=TURNO_VESPERTINO, dia_semana_sugerido=1, hora_inicio_min=900, hora_fim_min=1020, professor_id=8),
        # Capacidade excedida (nenhuma sala suporta 90)
        TurmaC(id=14, num_matriculados=90, tipo_exigido=TIPO_SALA_REGULAR, turno=TURNO_NOTURNO, dia_semana_sugerido=2, hora_inicio_min=1140, hora_fim_min=1260, professor_id=9),
        # Duas turmas sem professor no mesmo horario (ambas alocaveis)
        TurmaC(id=15, num_matriculados=35, tipo_exigido=TIPO_SALA_REGULAR, turno=TURNO_MATUTINO, dia_semana_sugerido=3, hora_inicio_min=480, hora_fim_min=600, professor_id=0),
        TurmaC(id=16, num_matriculados=50, tipo_exigido=TIPO_SALA_REGULAR, turno=TURNO_MATUTINO, dia_semana_sugerido=3, hora_inicio_min=480, hora_fim_min=600, professor_id=0),
    ]
    return turmas, salas


def _executar_v2(lib: ctypes.CDLL, turmas, salas, backend: int, max_threads: int = 2, medir_baseline: int = 0):
    arr_t = (TurmaC * len(turmas))(*turmas)
    arr_s = (SalaC * len(salas))(*salas)
    arr_out = (AlocacaoItemC * len(turmas))()
    met = MetricasAlocacaoC()
    rc = lib.otimizar_alocacao_salas_v2(
        arr_t, len(turmas), arr_s, len(salas), max_threads, backend, medir_baseline, arr_out, ctypes.byref(met)
    )
    itens = [
        (r.turma_id, r.sala_id, r.dia_semana, r.hora_inicio_min, r.hora_fim_min, r.score_desperdicio)
        for r in arr_out
    ]
    return rc, itens, met


def test_execucao_kernel_opencl_determinismo_conflitos_e_profiling(tmp_path: Path):
    if not _opencl_headers_disponiveis():
        pytest.skip("Headers OpenCL nao disponiveis neste ambiente")

    ext = ".dll" if platform.system() == "Windows" else ".so"
    lib = _compilar_biblioteca(tmp_path / f"motor_opencl_exec{ext}", usar_opencl=True)

    try:
        disponivel = ctypes.c_int32(0)
        assert lib.obter_status_opencl(ctypes.byref(disponivel), None, 0) == 0
        if disponivel.value != 1:
            pytest.skip("Nenhum dispositivo OpenCL ativo em runtime neste ambiente")

        turmas, salas = _montar_cenario_conflitos()
        rc1, itens1, met1 = _executar_v2(lib, turmas, salas, MOTOR_BACKEND_OPENCL, max_threads=2, medir_baseline=0)
        rc2, itens2, met2 = _executar_v2(lib, turmas, salas, MOTOR_BACKEND_OPENCL, max_threads=2, medir_baseline=0)
        rc_omp, itens_omp, met_omp = _executar_v2(lib, turmas, salas, MOTOR_BACKEND_OPENMP, max_threads=2, medir_baseline=0)

        assert rc1 == 0 and rc2 == 0 and rc_omp == 0
        assert met1.backend_utilizado == MOTOR_BACKEND_OPENCL
        assert met1.fallback_ativado == 0
        assert len(met1.dispositivo_opencl.decode("utf-8", errors="replace")) > 0
        assert met1.tempo_kernel_ms > 0.0
        assert met1.tempo_transferencia_ms > 0.0
        assert met1.tempo_paralelo_ms > 0.0
        assert met1.tempo_sequencial_ms == 0.0

        # Determinismo OpenCL e equivalencia exata com OpenMP
        assert itens1 == itens2
        assert itens1 == itens_omp
        assert met1.total_alocado == met_omp.total_alocado == 4
        assert met1.total_pendente == met_omp.total_pendente == 3

        mapa = {tid: sid for tid, sid, *_ in itens1}
        assert (mapa[10] > 0) != (mapa[11] > 0)
        assert (mapa[12] == 3) != (mapa[13] == 3)
        assert mapa[14] == -1
        assert mapa[15] > 0 and mapa[16] > 0 and mapa[15] != mapa[16]

        # Benchmark v2 em OpenCL mede baseline sequencial e speedup
        met_bench = MetricasAlocacaoC()
        rc_bench = lib.executar_benchmark_cenario_v2(40, 15, 2, MOTOR_BACKEND_OPENCL, ctypes.byref(met_bench))
        assert rc_bench == 0
        assert met_bench.backend_utilizado == MOTOR_BACKEND_OPENCL
        assert met_bench.tempo_sequencial_ms > 0.0
        assert met_bench.tempo_paralelo_ms > 0.0
        assert met_bench.tempo_kernel_ms > 0.0
        assert met_bench.tempo_transferencia_ms > 0.0
        assert met_bench.speedup > 0.0
    finally:
        lib.liberar_recursos_motor()


def test_fallback_opencl_para_openmp_e_validacao_v2(tmp_path: Path, monkeypatch):
    ext = ".dll" if platform.system() == "Windows" else ".so"
    lib = _compilar_biblioteca(tmp_path / f"motor_fallback_v2{ext}", usar_opencl=False)

    try:
        turmas, salas = _montar_cenario_conflitos()

        # AUTO sem OpenCL faz fallback auditavel para OpenMP
        rc_auto, itens_auto, met_auto = _executar_v2(lib, turmas, salas, MOTOR_BACKEND_AUTO, max_threads=2, medir_baseline=0)
        assert rc_auto == 0
        assert met_auto.backend_solicitado == MOTOR_BACKEND_AUTO
        assert met_auto.backend_utilizado == MOTOR_BACKEND_OPENMP
        assert met_auto.fallback_ativado == 1
        assert met_auto.tempo_sequencial_ms == 0.0
        assert met_auto.total_alocado == 4

        # OPENMP explicito nao marca fallback
        rc_omp, itens_omp, met_omp = _executar_v2(lib, turmas, salas, MOTOR_BACKEND_OPENMP, max_threads=2, medir_baseline=1)
        assert rc_omp == 0
        assert met_omp.backend_utilizado == MOTOR_BACKEND_OPENMP
        assert met_omp.fallback_ativado == 0
        assert met_omp.tempo_sequencial_ms >= 0.0
        assert itens_auto == itens_omp

        # Benchmark v2 em OpenMP mede baseline sequencial > 0.0
        met_bench_omp = MetricasAlocacaoC()
        assert lib.executar_benchmark_cenario_v2(40, 15, 2, MOTOR_BACKEND_OPENMP, ctypes.byref(met_bench_omp)) == 0
        assert met_bench_omp.backend_utilizado == MOTOR_BACKEND_OPENMP
        assert met_bench_omp.tempo_sequencial_ms > 0.0
        assert met_bench_omp.tempo_paralelo_ms > 0.0

        # CPU_SEQUENCIAL explicito executa em 1 thread
        rc_seq, itens_seq, met_seq = _executar_v2(lib, turmas, salas, MOTOR_BACKEND_CPU_SEQUENCIAL, max_threads=4, medir_baseline=0)
        assert rc_seq == 0
        assert met_seq.backend_utilizado == MOTOR_BACKEND_CPU_SEQUENCIAL
        assert met_seq.threads_utilizadas == 1
        assert itens_seq == itens_omp

        # OPENCL forcado sem dispositivo retorna -3
        rc_ocl, _, _ = _executar_v2(lib, turmas, salas, MOTOR_BACKEND_OPENCL, max_threads=2, medir_baseline=0)
        assert rc_ocl == -3

        # Argumentos invalidos retornam -1
        rc_inv, _, _ = _executar_v2(lib, turmas, salas, 99, max_threads=2, medir_baseline=0)
        assert rc_inv == -1

        # Simulacao de indisponibilidade em runtime com OpenCL habilitado (kernel ausente)
        if _opencl_headers_disponiveis():
            lib_ocl = _compilar_biblioteca(tmp_path / f"motor_ocl_missing_kernel{ext}", usar_opencl=True)
            try:
                monkeypatch.setenv("MOTOR_KERNEL_PATH", str(tmp_path / "nao_existe.cl"))
                rc_sim, _, met_sim = _executar_v2(lib_ocl, turmas, salas, MOTOR_BACKEND_AUTO, max_threads=2, medir_baseline=0)
                assert rc_sim == 0
                assert met_sim.backend_utilizado == MOTOR_BACKEND_OPENMP
                assert met_sim.fallback_ativado == 1

                rc_sim_forca, _, _ = _executar_v2(lib_ocl, turmas, salas, MOTOR_BACKEND_OPENCL, max_threads=2, medir_baseline=0)
                assert rc_sim_forca == -3
            finally:
                lib_ocl.liberar_recursos_motor()
    finally:
        lib.liberar_recursos_motor()
