"""
Enumerações de domínio do SIGAAS (Infraestrutura e Perfis).
"""

from enum import Enum


class PerfilUsuario(str, Enum):
    ADMIN = "admin"
    COORDENADOR = "coordenador"
    PROFESSOR = "professor"
    ALUNO = "aluno"
    SECRETARIA = "secretaria"


class TipoSala(str, Enum):
    REGULAR = "regular"
    LABORATORIO = "laboratorio"
    AUDITORIO = "auditorio"
    REUNIAO = "reuniao"
