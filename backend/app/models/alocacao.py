"""
Modelos de dados para Alocacao de Horarios e Auditoria (LogAlocacao).
"""

from datetime import time, datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import SmallInteger, Time, DateTime, ForeignKey, CheckConstraint, Text, JSON, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import TimestampMixin
from app.models.enums import TipoEventoLog

if TYPE_CHECKING:
    from app.models.campus import Campus
    from app.models.academico import Turma
    from app.models.sala import Sala
    from app.models.usuario import Usuario
    from app.models.ia import Frequencia, PrevisaoFalta, SugestaoRemanejamento


class Horario(TimestampMixin, Base):
    __tablename__ = "horario"
    __table_args__ = (
        CheckConstraint("hora_inicio < hora_fim", name="ck_horario_inicio_anterior_fim"),
        CheckConstraint("dia_semana >= 0 AND dia_semana <= 6", name="ck_horario_dia_semana_valido"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campus.id", ondelete="RESTRICT"), nullable=False, index=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"), nullable=False, index=True)
    sala_id: Mapped[int] = mapped_column(ForeignKey("sala.id", ondelete="RESTRICT"), nullable=False, index=True)
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[time] = mapped_column(Time, nullable=False)

    campus: Mapped["Campus"] = relationship("Campus")
    turma: Mapped["Turma"] = relationship("Turma", back_populates="horarios")
    sala: Mapped["Sala"] = relationship("Sala")
    frequencias: Mapped[List["Frequencia"]] = relationship("Frequencia", back_populates="horario")
    previsoes_falta: Mapped[List["PrevisaoFalta"]] = relationship("PrevisaoFalta", back_populates="horario")
    sugestoes_remanejamento: Mapped[List["SugestaoRemanejamento"]] = relationship("SugestaoRemanejamento", back_populates="horario")
    logs_alocacao: Mapped[List["LogAlocacao"]] = relationship("LogAlocacao", back_populates="horario")


class LogAlocacao(Base):
    __tablename__ = "log_alocacao"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    horario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("horario.id", ondelete="SET NULL"), nullable=True, index=True)
    snapshot_evento: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tipo_evento: Mapped[TipoEventoLog] = mapped_column(
        SQLEnum(TipoEventoLog, native_enum=False, create_constraint=True, validate_strings=True, values_callable=lambda x: [e.value for e in x], length=50),
        nullable=False
    )
    usuario_responsavel: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False)
    detalhes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    horario: Mapped[Optional["Horario"]] = relationship("Horario", back_populates="logs_alocacao")
    responsavel: Mapped["Usuario"] = relationship("Usuario")
