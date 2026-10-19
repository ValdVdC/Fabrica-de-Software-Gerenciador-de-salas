"""Exportacao de schemas."""
from app.schemas.campus import CampusBase, CampusCreate, CampusRead
from app.schemas.usuario import UsuarioBase, UsuarioCreate, UsuarioRead
from app.schemas.sala import SalaBase, SalaCreate, SalaRead
from app.schemas.turma import TurmaBase, TurmaCreate, TurmaRead
from app.schemas.matricula import MatriculaBase, MatriculaCreate, MatriculaRead
from app.schemas.horario import HorarioBase, HorarioCreate, HorarioRead, HorarioMeuRead
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.ia import (
    SugestaoRemanejamentoRead,
    SugestaoAprovacaoUpdate,
    AnaliseIARequest,
    AnaliseIAResponse,
    TreinamentoIAResponse,
    PrevisaoFaltaRead,
)
from app.schemas.log import LogRead
from app.schemas.dashboard import (
    DashboardOcupacaoRead,
    DashboardResumoRead,
    OcupacaoPorDiaRead,
    OcupacaoPorTurnoRead,
    SugestoesPorStatusRead,
)
from app.schemas.relatorio import RelatorioOcupacaoSalaRead, RelatorioRemanejamentoRead

__all__ = [
    "CampusBase", "CampusCreate", "CampusRead",
    "UsuarioBase", "UsuarioCreate", "UsuarioRead",
    "SalaBase", "SalaCreate", "SalaRead",
    "TurmaBase", "TurmaCreate", "TurmaRead",
    "MatriculaBase", "MatriculaCreate", "MatriculaRead",
    "HorarioBase", "HorarioCreate", "HorarioRead", "HorarioMeuRead",
    "LoginRequest", "TokenResponse",
    "SugestaoRemanejamentoRead", "SugestaoAprovacaoUpdate",
    "AnaliseIARequest", "AnaliseIAResponse", "TreinamentoIAResponse",
    "PrevisaoFaltaRead",
    "LogRead",
    "SugestoesPorStatusRead", "DashboardResumoRead",
    "OcupacaoPorDiaRead", "OcupacaoPorTurnoRead", "DashboardOcupacaoRead",
    "RelatorioOcupacaoSalaRead", "RelatorioRemanejamentoRead",
]
