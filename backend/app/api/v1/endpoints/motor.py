"""
Endpoints para integracao e teste do Motor C (OpenMP).
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.motor_service import motor_service

router = APIRouter()


class MotorTestePayload(BaseModel):
    a: int = Field(..., ge=-1_000_000, le=1_000_000, description="Primeiro operando inteiro")
    b: int = Field(..., ge=-1_000_000, le=1_000_000, description="Segundo operando inteiro")


class MotorStatusResponse(BaseModel):
    status: str
    versao: str | None
    biblioteca: str | None
    openmp_ativo: bool


class MotorTesteResponse(BaseModel):
    resultado: int
    ctypes_ok: bool
    operacao: str


@router.get(
    "/status",
    response_model=MotorStatusResponse,
    summary="Consultar status do motor C/OpenMP",
    description=(
        "Verifica se a biblioteca compartilhada motor_alocacao.so esta carregada via ctypes "
        "e se o suporte a paralelismo OpenMP esta ativo no processo FastAPI."
    ),
)
def obter_status_motor():
    return motor_service.get_status()


@router.post(
    "/teste-integracao",
    response_model=MotorTesteResponse,
    summary="Executar teste de integracao FFI com o motor C",
    description=(
        "Valida a ponte Python-C via ctypes enviando dois operandos inteiros dentro de limites seguros "
        "para execucao nativa na biblioteca compartilhada."
    ),
    responses={
        400: {"description": "Operandos fora dos limites permitidos ou overflow."},
        503: {"description": "Biblioteca compartilhada do motor C indisponivel."},
    },
)
def executar_teste_motor(payload: MotorTestePayload):
    try:
        return motor_service.executar_teste(payload.a, payload.b)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except (OverflowError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
