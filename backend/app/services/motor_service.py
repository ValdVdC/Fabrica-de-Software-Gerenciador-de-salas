"""
Servico de interoperabilidade com o motor de alocacao C com OpenMP via ctypes.
"""

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


class SalaC(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("capacidade", ctypes.c_int),
        ("tipo", ctypes.c_int),
        ("turnos_mask", ctypes.c_int),
    ]


class TurmaC(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("num_matriculados", ctypes.c_int),
        ("tipo_exigido", ctypes.c_int),
        ("turno", ctypes.c_int),
        ("dia_semana_sugerido", ctypes.c_int),
        ("hora_inicio_min", ctypes.c_int),
        ("hora_fim_min", ctypes.c_int),
    ]


class AlocacaoItemC(ctypes.Structure):
    _fields_ = [
        ("turma_id", ctypes.c_int),
        ("sala_id", ctypes.c_int),
        ("dia_semana", ctypes.c_int),
        ("hora_inicio_min", ctypes.c_int),
        ("hora_fim_min", ctypes.c_int),
        ("score_desperdicio", ctypes.c_int),
    ]


class MetricasAlocacaoC(ctypes.Structure):
    _fields_ = [
        ("tempo_sequencial_ms", ctypes.c_double),
        ("tempo_paralelo_ms", ctypes.c_double),
        ("speedup", ctypes.c_double),
        ("eficiencia", ctypes.c_double),
        ("fracao_amdahl", ctypes.c_double),
        ("threads_utilizadas", ctypes.c_int),
        ("total_alocado", ctypes.c_int),
        ("total_pendente", ctypes.c_int),
        ("padding", ctypes.c_int),
    ]


class MotorAlocacaoService:
    def __init__(self):
        self.lib = None
        self.lib_path = None
        self._carregar_biblioteca()

    def _obter_diretorio_motor(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent / "motor_alocacao"

    def _compilar_se_necessario(self, destino: Path, dir_motor: Path):
        if not destino.exists() and shutil.which("gcc"):
            cmd = [
                "gcc",
                "-Wall",
                "-Wextra",
                "-pedantic",
                "-std=c11",
                "-O3",
                "-fPIC",
                "-fopenmp",
                "-shared",
                "-o",
                str(destino),
                str(dir_motor / "motor.c"),
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)

    def _carregar_biblioteca(self):
        dir_motor = self._obter_diretorio_motor()
        is_windows = platform.system() == "Windows"
        ext = ".dll" if is_windows else ".so"
        self.lib_path = dir_motor / f"motor_alocacao{ext}"

        if is_windows and hasattr(os, "add_dll_directory"):
            gcc_path = shutil.which("gcc")
            if gcc_path:
                try:
                    os.add_dll_directory(str(Path(gcc_path).resolve().parent))
                except Exception:
                    pass

        try:
            self._compilar_se_necessario(self.lib_path, dir_motor)
            if self.lib_path.exists():
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
            ctypes.POINTER(TurmaC),
            ctypes.c_int,
            ctypes.POINTER(SalaC),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(AlocacaoItemC),
            ctypes.POINTER(MetricasAlocacaoC),
        ]

        self.lib.executar_benchmark_cenario.restype = ctypes.c_int
        self.lib.executar_benchmark_cenario.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(MetricasAlocacaoC),
        ]

    def get_status(self) -> dict[str, Any]:
        if not self.lib:
            return {
                "status": "unavailable",
                "versao": None,
                "biblioteca": None,
                "openmp_ativo": False,
            }
        raw_versao = self.lib.obter_versao_motor()
        versao = raw_versao.decode("utf-8", errors="replace") if raw_versao else "Desconhecida"
        return {
            "status": "online",
            "versao": versao,
            "biblioteca": self.lib_path.name if self.lib_path else None,
            "openmp_ativo": "OpenMP" in versao,
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
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if not self.lib:
            raise RuntimeError("Biblioteca do motor C nao esta carregada")

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
            }

        num_turmas = len(turmas)
        num_salas = len(salas)

        turmas_array = (TurmaC * num_turmas)(*turmas)
        salas_array = (SalaC * num_salas)(*salas)
        resultados_array = (AlocacaoItemC * num_turmas)()
        metricas = MetricasAlocacaoC()

        rc = self.lib.otimizar_alocacao_salas(
            turmas_array,
            ctypes.c_int(num_turmas),
            salas_array,
            ctypes.c_int(num_salas),
            ctypes.c_int(max_threads),
            resultados_array,
            ctypes.byref(metricas),
        )

        if rc != 0:
            raise RuntimeError(f"Erro na execucao do motor de alocacao C (codigo {rc})")

        alocacoes: list[dict[str, Any]] = []
        for i in range(num_turmas):
            item = resultados_array[i]
            alocacoes.append(
                {
                    "turma_id": item.turma_id,
                    "sala_id": item.sala_id,
                    "dia_semana": item.dia_semana,
                    "hora_inicio_min": item.hora_inicio_min,
                    "hora_fim_min": item.hora_fim_min,
                    "score_desperdicio": item.score_desperdicio,
                }
            )

        metricas_dict = {
            "tempo_sequencial_ms": round(metricas.tempo_sequencial_ms, 2),
            "tempo_paralelo_ms": round(metricas.tempo_paralelo_ms, 2),
            "speedup": round(metricas.speedup, 2),
            "eficiencia": round(metricas.eficiencia, 2),
            "fracao_amdahl": round(metricas.fracao_amdahl, 4),
            "threads_utilizadas": metricas.threads_utilizadas,
            "total_alocado": metricas.total_alocado,
            "total_pendente": metricas.total_pendente,
        }

        return alocacoes, metricas_dict

    def executar_benchmark(
        self,
        num_turmas: int,
        num_salas: int,
        num_threads: int,
    ) -> dict[str, Any]:
        if not self.lib:
            raise RuntimeError("Biblioteca do motor C nao esta carregada")

        metricas = MetricasAlocacaoC()
        rc = self.lib.executar_benchmark_cenario(
            ctypes.c_int(num_turmas),
            ctypes.c_int(num_salas),
            ctypes.c_int(num_threads),
            ctypes.byref(metricas),
        )

        if rc != 0:
            raise RuntimeError(f"Erro ao executar benchmark no motor C (codigo {rc})")

        return {
            "tempo_sequencial_ms": round(metricas.tempo_sequencial_ms, 2),
            "tempo_paralelo_ms": round(metricas.tempo_paralelo_ms, 2),
            "speedup": round(metricas.speedup, 2),
            "eficiencia": round(metricas.eficiencia, 2),
            "fracao_amdahl": round(metricas.fracao_amdahl, 4),
            "threads_utilizadas": metricas.threads_utilizadas,
            "total_alocado": metricas.total_alocado,
            "total_pendente": metricas.total_pendente,
        }


motor_service = MotorAlocacaoService()
