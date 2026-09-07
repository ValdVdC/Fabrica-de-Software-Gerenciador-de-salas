"""
Enumerações de domínio do SIGAAS.
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


class Turno(str, Enum):
    MATUTINO = "matutino"
    VESPERTINO = "vespertino"
    NOTURNO = "noturno"
    INTEGRAL = "integral"


class StatusSugestao(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"


class TipoEventoLog(str, Enum):
    CRIACAO = "criacao"
    REMANEJAMENTO = "remanejamento"
    CANCELAMENTO = "cancelamento"
