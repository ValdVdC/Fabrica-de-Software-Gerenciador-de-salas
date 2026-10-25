"""Exportacao de schemas."""
from app.schemas.campus import CampusBase, CampusCreate, CampusRead
from app.schemas.usuario import UsuarioBase, UsuarioCreate, UsuarioUpdate, UsuarioRead
from app.schemas.sala import SalaBase, SalaCreate, SalaUpdate, SalaRead
from app.schemas.turma import TurmaBase, TurmaCreate, TurmaUpdate, TurmaRead
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
    "UsuarioBase", "UsuarioCreate", "UsuarioUpdate", "UsuarioRead",
    "SalaBase", "SalaCreate", "SalaUpdate", "SalaRead",
    "TurmaBase", "TurmaCreate", "TurmaUpdate", "TurmaRead",
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
