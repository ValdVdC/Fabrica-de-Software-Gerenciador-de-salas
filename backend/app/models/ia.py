"""
Modelos de dados para Inteligencia Artificial: Frequencia, Previsao de Falta e Sugestao de Remanejamento.
"""

from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Boolean, Date, DateTime, ForeignKey, Text, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.enums import StatusSugestao

if TYPE_CHECKING:
    from app.models.academico import Matricula, Turma
    from app.models.alocacao import Horario
    from app.models.sala import Sala
    from app.models.usuario import Usuario


class Frequencia(Base):
    __tablename__ = "frequencia"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    matricula_id: Mapped[int] = mapped_column(ForeignKey("matricula.id", ondelete="CASCADE"), nullable=False, index=True)
    horario_id: Mapped[int] = mapped_column(ForeignKey("horario.id", ondelete="CASCADE"), nullable=False, index=True)
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    presente: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    matricula: Mapped["Matricula"] = relationship("Matricula", back_populates="frequencias")
    horario: Mapped["Horario"] = relationship("Horario", back_populates="frequencias")


class PrevisaoFalta(Base):
    __tablename__ = "previsao_falta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"), nullable=False, index=True)
    horario_id: Mapped[int] = mapped_column(ForeignKey("horario.id", ondelete="CASCADE"), nullable=False, index=True)
    data_prevista: Mapped[date] = mapped_column(Date, nullable=False)
    prob_ausencia: Mapped[float] = mapped_column(Float, nullable=False)
    versao_modelo: Mapped[str] = mapped_column(String(50), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    turma: Mapped["Turma"] = relationship("Turma")
    horario: Mapped["Horario"] = relationship("Horario", back_populates="previsoes_falta")


class SugestaoRemanejamento(Base):
    __tablename__ = "sugestao_remanejamento"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    horario_id: Mapped[int] = mapped_column(ForeignKey("horario.id", ondelete="CASCADE"), nullable=False, index=True)
    sala_atual_id: Mapped[int] = mapped_column(ForeignKey("sala.id", ondelete="RESTRICT"), nullable=False)
    sala_sugerida_id: Mapped[int] = mapped_column(ForeignKey("sala.id", ondelete="RESTRICT"), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    justificativa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[StatusSugestao] = mapped_column(
        SQLEnum(StatusSugestao, native_enum=False, create_constraint=True, validate_strings=True, values_callable=lambda x: [e.value for e in x], length=20),
        default=StatusSugestao.PENDENTE,
        nullable=False
    )
    aprovado_por: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    horario: Mapped["Horario"] = relationship("Horario", back_populates="sugestoes_remanejamento")
    sala_atual: Mapped["Sala"] = relationship("Sala", foreign_keys=[sala_atual_id])
    sala_sugerida: Mapped["Sala"] = relationship("Sala", foreign_keys=[sala_sugerida_id])
    aprovador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[aprovado_por])
