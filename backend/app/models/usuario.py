"""
Modelo de dados para Usuário e perfis de acesso.
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import TimestampMixin
from app.models.enums import PerfilUsuario

if TYPE_CHECKING:
    from app.models.campus import Campus


class Usuario(TimestampMixin, Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campus.id", ondelete="RESTRICT"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilUsuario] = mapped_column(
        SQLEnum(PerfilUsuario, native_enum=False, create_constraint=True, validate_strings=True, values_callable=lambda x: [e.value for e in x], length=30),
        nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    campus: Mapped["Campus"] = relationship("Campus", back_populates="usuarios")
