"""
Testes TDD para infraestrutura OpenCL do motor de alocacao C (SPEC-M2-01 PR 2a).
"""

import ctypes
import faulthandler
import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

from app.services.motor_service import MetricasAlocacaoC

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
