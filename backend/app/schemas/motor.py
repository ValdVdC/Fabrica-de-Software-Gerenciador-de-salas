"""
Schemas Pydantic para endpoints de diagnostico e dispositivos do Motor C (OpenMP/OpenCL).
"""

from pydantic import BaseModel, Field


class MotorTestePayload(BaseModel):
    a: int = Field(..., ge=-1_000_000, le=1_000_000, description="Primeiro operando inteiro")
    b: int = Field(..., ge=-1_000_000, le=1_000_000, description="Segundo operando inteiro")


class MotorStatusResponse(BaseModel):
    status: str
    versao: str | None
    biblioteca: str | None
    openmp_ativo: bool
    heuristica: str | None = None
    opencl_disponivel: bool = False
    dispositivo_opencl_padrao: str | None = None
    backends_suportados: list[str] = Field(default_factory=list)


class MotorTesteResponse(BaseModel):
    resultado: int
    ctypes_ok: bool
    operacao: str


class OpenCLDeviceInfoSchema(BaseModel):
    platform_name: str
    device_name: str
    device_type: str
    opencl_c_version: str
    compute_units: int
    global_mem_mb: int
    max_work_group_size: int


class MotorDispositivosResponse(BaseModel):
    opencl_disponivel: bool
    total: int
    dispositivos: list[OpenCLDeviceInfoSchema] = Field(default_factory=list)
