"""Exportacao de schemas."""
from app.schemas.campus import CampusBase, CampusCreate, CampusRead
from app.schemas.usuario import UsuarioBase, UsuarioCreate, UsuarioRead
from app.schemas.sala import SalaBase, SalaCreate, SalaRead
from app.schemas.turma import TurmaBase, TurmaCreate, TurmaRead
from app.schemas.matricula import MatriculaBase, MatriculaCreate, MatriculaRead
from app.schemas.horario import HorarioBase, HorarioCreate, HorarioRead
from app.schemas.auth import LoginRequest, TokenResponse

__all__ = ["CampusBase", "CampusCreate", "CampusRead", "UsuarioBase", "UsuarioCreate", "UsuarioRead", "SalaBase", "SalaCreate", "SalaRead", "TurmaBase", "TurmaCreate", "TurmaRead", "MatriculaBase", "MatriculaCreate", "MatriculaRead", "HorarioBase", "HorarioCreate", "HorarioRead", "LoginRequest", "TokenResponse"]

