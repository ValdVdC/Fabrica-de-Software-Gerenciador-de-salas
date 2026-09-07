"""
Consolidação de modelos SQLAlchemy 2.0 do SIGAAS (Infraestrutura e Espaços).
"""

from app.models.enums import PerfilUsuario, TipoSala
from app.models.campus import Campus
from app.models.usuario import Usuario
from app.models.sala import Equipamento, Sala, SalaEquipamento

__all__ = [
    "PerfilUsuario",
    "TipoSala",
    "Campus",
    "Usuario",
    "Equipamento",
    "Sala",
    "SalaEquipamento",
]
