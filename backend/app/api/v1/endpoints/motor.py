"""
Endpoints para integracao, status e descoberta de dispositivos do Motor C (OpenMP/OpenCL).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_role
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.motor import (
    MotorDispositivosResponse,
    MotorStatusResponse,
    MotorTestePayload,
    MotorTesteResponse,
)
from app.services.motor_service import motor_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/status",
    response_model=MotorStatusResponse,
    summary="Consultar status do motor C/OpenMP/OpenCL",
    description=(
        "Verifica se a biblioteca compartilhada do motor C esta carregada via ctypes, "
        "expondo a heuristica ativa, suporte OpenMP e disponibilidade OpenCL."
    ),
)
def obter_status_motor():
    return motor_service.get_status()


@router.get(
    "/dispositivos",
    response_model=MotorDispositivosResponse,
    summary="Listar dispositivos OpenCL detectados pelo motor C",
    description=(
        "Consulta os dispositivos OpenCL (GPU, aceleradores ou CPU/PoCL) detectados pela biblioteca "
        "nativa do motor de alocacao. Requer autenticacao JWT com perfil Admin ou Coordenador."
    ),
    responses={
        401: {"description": "Token JWT ausente, invalido ou expirado."},
        403: {"description": "Acesso negado por perfil RBAC."},
        503: {"description": "Biblioteca compartilhada do motor C indisponivel."},
    },
)
def listar_dispositivos_opencl(
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR)),
):
    _ = current_user
    try:
        dispositivos = motor_service.obter_dispositivos_opencl()
    except RuntimeError as e:
        logger.error("Motor de alocacao C indisponivel ao listar dispositivos OpenCL: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Motor de alocacao C indisponivel no momento.",
        ) from e
    return {
        "opencl_disponivel": len(dispositivos) > 0,
        "total": len(dispositivos),
        "dispositivos": dispositivos,
    }


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
        logger.error("Motor de alocacao C indisponivel no teste de integracao: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Motor de alocacao C indisponivel no momento.",
        ) from e
    except (OverflowError, ValueError) as e:
        logger.warning("Operandos invalidos no teste de integracao do motor C: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operandos invalidos ou fora dos limites permitidos.",
        ) from e
