"""
Servico de interoperabilidade com o motor de alocacao C via ctypes.
"""

import ctypes
import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class AlocacaoItemC(ctypes.Structure):
    _fields_ = [
        ("turma_id", ctypes.c_int),
        ("sala_id", ctypes.c_int),
        ("dia_semana", ctypes.c_int),
        ("hora_inicio", ctypes.c_int),
        ("hora_fim", ctypes.c_int),
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
            cmd = ["gcc", "-Wall", "-Wextra", "-O3", "-fPIC", "-fopenmp", "-shared", "-o", str(destino), str(dir_motor / "motor.c")]
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
                self.lib.obter_versao_motor.restype = ctypes.c_char_p
                self.lib.obter_versao_motor.argtypes = []
                self.lib.testar_integracao_ctypes.restype = ctypes.c_int
                self.lib.testar_integracao_ctypes.argtypes = [ctypes.c_int, ctypes.c_int]
        except Exception as exc:
            logger.warning("Nao foi possivel carregar a biblioteca do motor C: %s", exc)
            self.lib = None

    def get_status(self) -> dict:
        if not self.lib:
            return {"status": "unavailable", "versao": None, "biblioteca": None, "openmp_ativo": False}
        raw_versao = self.lib.obter_versao_motor()
        versao = raw_versao.decode("utf-8", errors="replace") if raw_versao else "Desconhecida"
        return {
            "status": "online",
            "versao": versao,
            "biblioteca": self.lib_path.name if self.lib_path else None,
            "openmp_ativo": "OpenMP" in versao,
        }

    def executar_teste(self, a: int, b: int) -> dict:
        if not self.lib:
            raise RuntimeError("Biblioteca do motor C nao esta carregada")
        resultado = self.lib.testar_integracao_ctypes(a, b)
        return {"resultado": resultado, "ctypes_ok": True, "operacao": f"{a} + {b}"}


motor_service = MotorAlocacaoService()
