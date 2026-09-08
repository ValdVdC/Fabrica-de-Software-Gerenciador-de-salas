"""
Roteador central da API versao 1 (v1).
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    campi,
    cursos,
    disciplinas,
    equipamentos,
    horarios,
    motor,
    salas,
    turmas,
    usuarios,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticacao"])
api_router.include_router(campi.router, prefix="/campi", tags=["Campi"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
api_router.include_router(cursos.router, prefix="/cursos", tags=["Cursos"])
api_router.include_router(disciplinas.router, prefix="/disciplinas", tags=["Disciplinas"])
api_router.include_router(salas.router, prefix="/salas", tags=["Salas"])
api_router.include_router(equipamentos.router, prefix="/equipamentos", tags=["Equipamentos"])
api_router.include_router(turmas.router, prefix="/turmas", tags=["Turmas"])
api_router.include_router(horarios.router, prefix="/horarios", tags=["Horarios"])
api_router.include_router(motor.router, prefix="/motor", tags=["Motor"])

