"""
Consolidação de modelos SQLAlchemy 2.0 do SIGAAS.
"""

from app.models.enums import PerfilUsuario, TipoSala, Turno, StatusSugestao, TipoEventoLog
from app.models.campus import Campus
from app.models.usuario import Usuario
from app.models.sala import Equipamento, Sala, SalaEquipamento
from app.models.academico import Curso, Disciplina, Turma, Matricula
from app.models.alocacao import Horario, LogAlocacao
from app.models.ia import Frequencia, PrevisaoFalta, SugestaoRemanejamento

__all__ = [
    "PerfilUsuario",
    "TipoSala",
    "Turno",
    "StatusSugestao",
    "TipoEventoLog",
    "Campus",
    "Usuario",
    "Equipamento",
    "Sala",
    "SalaEquipamento",
    "Curso",
    "Disciplina",
    "Turma",
    "Matricula",
    "Horario",
    "LogAlocacao",
    "Frequencia",
    "PrevisaoFalta",
    "SugestaoRemanejamento",
]
