"""
Servico de interoperabilidade com o motor de alocacao C (OpenMP/OpenCL) via ctypes.
"""

import atexit
import ctypes
import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Constantes de Tipos de Sala
TIPO_SALA_REGULAR = 0
TIPO_SALA_LABORATORIO = 1
TIPO_SALA_AUDITORIO = 2
TIPO_SALA_REUNIAO = 3

# Constantes de Turnos
TURNO_MATUTINO = 0
TURNO_VESPERTINO = 1
TURNO_NOTURNO = 2
TURNO_INTEGRAL = 3

# Bitmasks de Turnos
TURNO_MASK_MATUTINO = 1 << 0
TURNO_MASK_VESPERTINO = 1 << 1
TURNO_MASK_NOTURNO = 1 << 2
TURNO_MASK_INTEGRAL = 1 << 3

# Backends de execucao (espelho de MotorBackend em motor.h)
MOTOR_BACKEND_AUTO = 0
MOTOR_BACKEND_CPU_SEQUENCIAL = 1
MOTOR_BACKEND_OPENMP = 2
MOTOR_BACKEND_OPENCL = 3

BACKEND_STR_TO_INT: dict[str, int] = {
    "auto": MOTOR_BACKEND_AUTO,
    "cpu_sequencial": MOTOR_BACKEND_CPU_SEQUENCIAL,
    "openmp": MOTOR_BACKEND_OPENMP,
    "opencl": MOTOR_BACKEND_OPENCL,
}
BACKEND_INT_TO_STR: dict[int, str] = {v: k for k, v in BACKEND_STR_TO_INT.items()}


class MotorOpenCLIndisponivelError(RuntimeError):
    """Erro levantado quando o backend OpenCL e solicitado sem dispositivo disponivel."""

CARACTERIZACAO_HEURISTICA: dict[str, Any] = {
    "classificacao": (
        "Heuristica Construtiva Gulosa Deterministica com Priorizacao de "
        "Restricoes Rigidas e Capacidade Minima Viavel"
    ),
    "classe_complexidade": "NP-dificil",
    "complexidade_temporal": "O(T * S)",
    "garantia_otimo_global": False,
    "justificativa_teorica": (
        "Devido a natureza combinatorial NP-dificil do problema de Timetabling universitario, "
        "a busca exata e intratavel em escala real. O motor utiliza ordenacao Best-Fit Decreasing "
        "com multi-start perturbado deterministico em OpenMP, garantindo solucoes viaveis de alta "
        "qualidade em tempo polinomial O(T * S) por tentativa sem garantia de otimo global."
    ),
}

MATRIZ_REGRESSAO_BUGS: list[dict[str, str]] = [
    {
        "id_bug": "BUG-HPC-01",
        "descricao": "Desalinhamento de 64-bit e ausencia de padding explicito na struct MetricasAlocacaoC via ctypes",
        "commit_correcao": "2d9d8c9 (#67)",
        "teste_regressao": "tests/test_motor_c.py::test_speedup_concorrente",
    },
    {
        "id_bug": "BUG-HPC-02",
        "descricao": "Canibalizacao de laboratorios especializados por turmas regulares sem penalidade heuristica",
        "commit_correcao": "2d9d8c9 (#67)",
        "teste_regressao": "tests/test_benchmark_estatistico.py::test_matriz_rastreabilidade_bugs_e_regressao",
    },
    {
        "id_bug": "BUG-HPC-03",
        "descricao": "Falso positivo de exigencia de laboratorio por correspondencia parcial de substring ('Elaboracao')",
        "commit_correcao": "2d9d8c9 (#67)",
        "teste_regressao": "tests/test_api_alocacao.py::test_endpoint_otimizar_sucesso",
    },
    {
        "id_bug": "BUG-HPC-04",
        "descricao": "Omissao de turmas sem sala disponivel no retorno FFI quando todas as salas estao lotadas",
        "commit_correcao": "e06b008 / 2d9d8c9 (#67)",
        "teste_regressao": "tests/test_api_alocacao.py::test_endpoint_retorna_turmas_sem_sala_com_sala_negativa",
    },
]


class SalaC(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int32),
        ("capacidade", ctypes.c_int32),
        ("tipo", ctypes.c_int32),
        ("turnos_mask", ctypes.c_int32),
    ]


class TurmaC(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int32),
        ("num_matriculados", ctypes.c_int32),
        ("tipo_exigido", ctypes.c_int32),
        ("turno", ctypes.c_int32),
        ("dia_semana_sugerido", ctypes.c_int32),
        ("hora_inicio_min", ctypes.c_int32),
        ("hora_fim_min", ctypes.c_int32),
        ("professor_id", ctypes.c_int32),
    ]


class AlocacaoItemC(ctypes.Structure):
    _fields_ = [
        ("turma_id", ctypes.c_int32),
        ("sala_id", ctypes.c_int32),
        ("dia_semana", ctypes.c_int32),
        ("hora_inicio_min", ctypes.c_int32),
        ("hora_fim_min", ctypes.c_int32),
        ("score_desperdicio", ctypes.c_int32),
    ]


class MetricasAlocacaoC(ctypes.Structure):
    _fields_ = [
        ("tempo_sequencial_ms", ctypes.c_double),
        ("tempo_paralelo_ms", ctypes.c_double),
        ("speedup", ctypes.c_double),
        ("eficiencia", ctypes.c_double),
        ("fracao_amdahl", ctypes.c_double),
        ("tempo_kernel_ms", ctypes.c_double),
        ("tempo_transferencia_ms", ctypes.c_double),
        ("threads_utilizadas", ctypes.c_int32),
        ("total_alocado", ctypes.c_int32),
        ("total_pendente", ctypes.c_int32),
        ("backend_solicitado", ctypes.c_int32),
        ("backend_utilizado", ctypes.c_int32),
        ("fallback_ativado", ctypes.c_int32),
        ("dispositivo_opencl", ctypes.c_char * 64),
    ]


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


for _cls, _expected in (
    (SalaC, 16),
    (TurmaC, 32),
    (AlocacaoItemC, 24),
    (MetricasAlocacaoC, 144),
    (OpenCLDeviceInfoC, 192),
):
    if ctypes.sizeof(_cls) != _expected:
        raise RuntimeError(f"ABI invalida: sizeof({_cls.__name__}) esperado {_expected}, obtido {ctypes.sizeof(_cls)}")


def _opencl_headers_disponiveis() -> bool:
    candidatos = [
        Path("/usr/include/CL/cl.h"),
        Path("/usr/local/include/CL/cl.h"),
        Path("C:/msys64/ucrt64/include/CL/cl.h"),
    ]
    gcc_path = shutil.which("gcc")
    if gcc_path:
        candidatos.append(Path(gcc_path).resolve().parent.parent / "include" / "CL" / "cl.h")
    return any(p.exists() for p in candidatos)


class MotorAlocacaoService:
    def __init__(self):
        self.lib = None
        self.lib_path = None
        self._carregar_biblioteca()
        atexit.register(self._liberar_ao_encerrar)

    def _liberar_ao_encerrar(self):
        try:
            if self.lib is not None and hasattr(self.lib, "liberar_recursos_motor"):
                self.lib.liberar_recursos_motor()
        except Exception:
            pass

    def _obter_diretorio_motor(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent / "motor_alocacao"

    def _compilar_se_necessario(self, destino: Path, dir_motor: Path):
        motor_opencl_c = dir_motor / "motor_opencl.c"
        fontes = (
            dir_motor / "motor.c",
            dir_motor / "motor.h",
            motor_opencl_c,
            dir_motor / "motor_opencl.h",
            dir_motor / "kernels" / "alocacao.cl",
        )
        desatualizado = not destino.exists() or any(
            f.exists() and f.stat().st_mtime > destino.stat().st_mtime for f in fontes
        )
        if not (desatualizado and shutil.which("gcc")):
            return
        base_cmd = ["gcc", "-Wall", "-Wextra", "-pedantic", "-std=c11", "-O3", "-fPIC", "-fopenmp", "-shared"]
        src_files = [str(dir_motor / "motor.c")] + ([str(motor_opencl_c)] if motor_opencl_c.exists() else [])
        if motor_opencl_c.exists() and _opencl_headers_disponiveis():
            try:
                subprocess.run(
                    [*base_cmd, "-DUSE_OPENCL", "-o", str(destino), *src_files, "-lOpenCL"],
                    check=True,
                    capture_output=True,
                    timeout=30,
                )
                return
            except subprocess.CalledProcessError as exc:
                logger.warning("Compilacao OpenCL falhou, usando fallback OpenMP: %s", exc)
        subprocess.run([*base_cmd, "-o", str(destino), *src_files], check=True, capture_output=True, timeout=30)

    def _carregar_biblioteca(self):
        dir_motor = self._obter_diretorio_motor()
        is_windows = platform.system() == "Windows"
        ext = ".dll" if is_windows else ".so"
        env_path = os.environ.get("MOTOR_LIB_PATH", "").strip()
        self.lib_path = Path(env_path) if env_path else (dir_motor / f"motor_alocacao{ext}")

        if is_windows and hasattr(os, "add_dll_directory"):
            gcc_path = shutil.which("gcc")
            if gcc_path:
                try:
                    os.add_dll_directory(str(Path(gcc_path).resolve().parent))
                except Exception as exc:
                    logger.debug("Nao foi possivel adicionar diretorio DLL do gcc: %s", exc)

        try:
            if not env_path:
                self._compilar_se_necessario(self.lib_path, dir_motor)
            if self.lib_path.is_file():
                self.lib = ctypes.CDLL(str(self.lib_path))
                self._configurar_assinaturas()
        except Exception as exc:
            logger.warning("Nao foi possivel carregar a biblioteca do motor C: %s", exc)
            self.lib = None

    def _configurar_assinaturas(self):
        if not self.lib:
            return
        self.lib.obter_versao_motor.restype = ctypes.c_char_p
        self.lib.obter_versao_motor.argtypes = []
        self.lib.testar_integracao_ctypes.restype = ctypes.c_int
        self.lib.testar_integracao_ctypes.argtypes = [ctypes.c_int, ctypes.c_int]
        self.lib.otimizar_alocacao_salas.restype = ctypes.c_int
        self.lib.otimizar_alocacao_salas.argtypes = [
            ctypes.POINTER(TurmaC), ctypes.c_int, ctypes.POINTER(SalaC), ctypes.c_int,
            ctypes.c_int, ctypes.POINTER(AlocacaoItemC), ctypes.POINTER(MetricasAlocacaoC),
        ]
        self.lib.executar_benchmark_cenario.restype = ctypes.c_int
        self.lib.executar_benchmark_cenario.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(MetricasAlocacaoC),
        ]
        self.lib.otimizar_alocacao_salas_v2.restype = ctypes.c_int
        self.lib.otimizar_alocacao_salas_v2.argtypes = [
            ctypes.POINTER(TurmaC), ctypes.c_int32, ctypes.POINTER(SalaC), ctypes.c_int32,
            ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
            ctypes.POINTER(AlocacaoItemC), ctypes.POINTER(MetricasAlocacaoC),
        ]
        self.lib.executar_benchmark_cenario_v2.restype = ctypes.c_int
        self.lib.executar_benchmark_cenario_v2.argtypes = [
            ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.POINTER(MetricasAlocacaoC),
        ]
        self.lib.obter_status_opencl.restype = ctypes.c_int
        self.lib.obter_status_opencl.argtypes = [ctypes.POINTER(ctypes.c_int32), ctypes.c_char_p, ctypes.c_int32]
        self.lib.obter_dispositivos_opencl.restype = ctypes.c_int
        self.lib.obter_dispositivos_opencl.argtypes = [
            ctypes.POINTER(OpenCLDeviceInfoC), ctypes.c_int32, ctypes.POINTER(ctypes.c_int32),
        ]
        self.lib.liberar_recursos_motor.restype = None
        self.lib.liberar_recursos_motor.argtypes = []

    def _resolver_backend(self, backend: str) -> int:
        chave = (backend or "auto").strip().lower()
        if chave not in BACKEND_STR_TO_INT:
            raise ValueError(f"Backend invalido: {backend}")
        return BACKEND_STR_TO_INT[chave]

    def _serializar_metricas(self, metricas: MetricasAlocacaoC) -> dict[str, Any]:
        dev_raw = metricas.dispositivo_opencl.decode("utf-8", errors="replace").strip()
        return {
            "tempo_sequencial_ms": round(metricas.tempo_sequencial_ms, 2),
            "tempo_paralelo_ms": round(metricas.tempo_paralelo_ms, 2),
            "speedup": round(metricas.speedup, 2),
            "eficiencia": round(metricas.eficiencia, 2),
            "fracao_amdahl": round(metricas.fracao_amdahl, 4),
            "threads_utilizadas": metricas.threads_utilizadas,
            "total_alocado": metricas.total_alocado,
            "total_pendente": metricas.total_pendente,
            "backend_usado": BACKEND_INT_TO_STR.get(metricas.backend_utilizado, "openmp"),
            "fallback_ativado": bool(metricas.fallback_ativado),
            "dispositivo_opencl": dev_raw or None,
            "tempo_kernel_ms": round(metricas.tempo_kernel_ms, 4),
            "tempo_transferencia_ms": round(metricas.tempo_transferencia_ms, 4),
        }

    def obter_dispositivos_opencl(self, max_dispositivos: int = 16) -> list[dict[str, Any]]:
        if not self.lib:
            raise RuntimeError("Biblioteca do motor C nao esta carregada")
        limite = max(1, min(int(max_dispositivos), 64))
        buf = (OpenCLDeviceInfoC * limite)()
        total = ctypes.c_int32(0)
        rc = self.lib.obter_dispositivos_opencl(buf, ctypes.c_int32(limite), ctypes.byref(total))
        if rc != 0:
            return []
        qtd = min(max(0, total.value), limite)
        return [
            {
                "platform_name": buf[i].platform_name.decode("utf-8", errors="replace").strip(),
                "device_name": buf[i].device_name.decode("utf-8", errors="replace").strip(),
                "device_type": buf[i].device_type.decode("utf-8", errors="replace").strip(),
                "opencl_c_version": buf[i].opencl_c_version.decode("utf-8", errors="replace").strip(),
                "compute_units": int(buf[i].compute_units),
                "global_mem_mb": int(buf[i].global_mem_mb),
                "max_work_group_size": int(buf[i].max_work_group_size),
            }
            for i in range(qtd)
        ]

    def get_status(self) -> dict[str, Any]:
        if not self.lib:
            return {
                "status": "unavailable",
                "versao": None,
                "biblioteca": None,
                "openmp_ativo": False,
                "heuristica": None,
                "opencl_disponivel": False,
                "dispositivo_opencl_padrao": None,
                "backends_suportados": [],
            }
        raw_versao = self.lib.obter_versao_motor()
        versao = raw_versao.decode("utf-8", errors="replace") if raw_versao else "Desconhecida"
        disp_flag = ctypes.c_int32(0)
        dev_buf = ctypes.create_string_buffer(64)
        self.lib.obter_status_opencl(ctypes.byref(disp_flag), dev_buf, ctypes.c_int32(64))
        opencl_ok = bool(disp_flag.value)
        dev_padrao = dev_buf.value.decode("utf-8", errors="replace").strip() if opencl_ok else None
        backends = ["auto", "cpu_sequencial", "openmp"] + (["opencl"] if opencl_ok else [])
        return {
            "status": "online",
            "versao": versao,
            "biblioteca": self.lib_path.name if self.lib_path else None,
            "openmp_ativo": "OpenMP" in versao,
            "heuristica": CARACTERIZACAO_HEURISTICA["classificacao"],
            "opencl_disponivel": opencl_ok,
            "dispositivo_opencl_padrao": dev_padrao or None,
            "backends_suportados": backends,
        }

    def executar_teste(self, a: int, b: int) -> dict[str, Any]:
        if not self.lib:
            raise RuntimeError("Biblioteca do motor C nao esta carregada")
        resultado = self.lib.testar_integracao_ctypes(a, b)
        return {"resultado": resultado, "ctypes_ok": True, "operacao": f"{a} + {b}"}

    def otimizar_alocacao(
        self,
        turmas: list[TurmaC],
        salas: list[SalaC],
        max_threads: int = 4,
        backend: str = "auto",
        executar_baseline_sequencial: bool = True,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if not self.lib:
            raise RuntimeError("Biblioteca do motor C nao esta carregada")
        backend_int = self._resolver_backend(backend)
        if not turmas or not salas:
            return [], {
                "tempo_sequencial_ms": 0.0,
                "tempo_paralelo_ms": 0.0,
                "speedup": 1.0,
                "eficiencia": 100.0,
                "fracao_amdahl": 1.0,
                "threads_utilizadas": max_threads,
                "total_alocado": 0,
                "total_pendente": len(turmas),
                "backend_usado": BACKEND_INT_TO_STR[backend_int] if backend_int != MOTOR_BACKEND_AUTO else "openmp",
                "fallback_ativado": False,
                "dispositivo_opencl": None,
                "tempo_kernel_ms": 0.0,
                "tempo_transferencia_ms": 0.0,
            }

        num_turmas, num_salas = len(turmas), len(salas)
        turmas_array = (TurmaC * num_turmas)(*turmas)
        salas_array = (SalaC * num_salas)(*salas)
        resultados_array = (AlocacaoItemC * num_turmas)()
        metricas = MetricasAlocacaoC()

        rc = self.lib.otimizar_alocacao_salas_v2(
            turmas_array,
            ctypes.c_int32(num_turmas),
            salas_array,
            ctypes.c_int32(num_salas),
            ctypes.c_int32(max_threads),
            ctypes.c_int32(backend_int),
            ctypes.c_int32(1 if executar_baseline_sequencial else 0),
            resultados_array,
            ctypes.byref(metricas),
        )
        if rc == -3:
            raise MotorOpenCLIndisponivelError("Backend OpenCL indisponivel no ambiente atual")
        if rc != 0:
            raise RuntimeError(f"Erro na execucao do motor de alocacao C (codigo {rc})")

        alocacoes = [
            {
                "turma_id": resultados_array[i].turma_id,
                "sala_id": resultados_array[i].sala_id,
                "dia_semana": resultados_array[i].dia_semana,
                "hora_inicio_min": resultados_array[i].hora_inicio_min,
                "hora_fim_min": resultados_array[i].hora_fim_min,
                "score_desperdicio": resultados_array[i].score_desperdicio,
            }
            for i in range(num_turmas)
        ]
        return alocacoes, self._serializar_metricas(metricas)

    def executar_benchmark(
        self,
        num_turmas: int,
        num_salas: int,
        num_threads: int,
        backend: str = "openmp",
    ) -> dict[str, Any]:
        if not self.lib:
            raise RuntimeError("Biblioteca do motor C nao esta carregada")
        backend_int = self._resolver_backend(backend)
        metricas = MetricasAlocacaoC()
        rc = self.lib.executar_benchmark_cenario_v2(
            ctypes.c_int32(num_turmas),
            ctypes.c_int32(num_salas),
            ctypes.c_int32(num_threads),
            ctypes.c_int32(backend_int),
            ctypes.byref(metricas),
        )
        if rc == -3:
            raise MotorOpenCLIndisponivelError("Backend OpenCL indisponivel no ambiente atual")
        if rc != 0:
            raise RuntimeError(f"Erro ao executar benchmark no motor C (codigo {rc})")
        return self._serializar_metricas(metricas)


motor_service = MotorAlocacaoService()
