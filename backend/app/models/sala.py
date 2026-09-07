"""
Modelos de dados para Sala, Equipamento e associação SalaEquipamento.
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    String, Integer, Boolean, ForeignKey, UniqueConstraint,
    CheckConstraint, DateTime, func, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import TimestampMixin
from app.models.enums import TipoSala

if TYPE_CHECKING:
    from app.models.campus import Campus


class Equipamento(Base):
    __tablename__ = "equipamento"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    salas_associadas: Mapped[List["SalaEquipamento"]] = relationship("SalaEquipamento", back_populates="equipamento")


class Sala(TimestampMixin, Base):
    __tablename__ = "sala"
    __table_args__ = (
        UniqueConstraint("campus_id", "bloco", "numero", name="uq_sala_campus_bloco_numero"),
        CheckConstraint("capacidade > 0", name="ck_sala_capacidade_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campus.id", ondelete="RESTRICT"), nullable=False, index=True)
    bloco: Mapped[str] = mapped_column(String(50), nullable=False)
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo: Mapped[TipoSala] = mapped_column(
        SQLEnum(TipoSala, native_enum=False, create_constraint=True, validate_strings=True, values_callable=lambda x: [e.value for e in x], length=30),
        nullable=False
    )
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False)
    turnos_disponiveis: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    campus: Mapped["Campus"] = relationship("Campus", back_populates="salas")
    equipamentos_associados: Mapped[List["SalaEquipamento"]] = relationship(
        "SalaEquipamento", back_populates="sala", cascade="all, delete-orphan"
    )


class SalaEquipamento(Base):
    __tablename__ = "sala_equipamento"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_sala_equipamento_quantidade_positiva"),
    )

    sala_id: Mapped[int] = mapped_column(ForeignKey("sala.id", ondelete="CASCADE"), primary_key=True)
    equipamento_id: Mapped[int] = mapped_column(ForeignKey("equipamento.id", ondelete="RESTRICT"), primary_key=True)
    quantidade: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    sala: Mapped["Sala"] = relationship("Sala", back_populates="equipamentos_associados")
    equipamento: Mapped["Equipamento"] = relationship("Equipamento", back_populates="salas_associadas")
