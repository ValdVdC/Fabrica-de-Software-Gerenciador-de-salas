"""
Modelos de dados academicos: Curso, Disciplina, Turma e Matricula.
"""

from datetime import date, datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import TimestampMixin
from app.models.enums import Turno

if TYPE_CHECKING:
    from app.models.campus import Campus
    from app.models.usuario import Usuario
    from app.models.alocacao import Horario
    from app.models.ia import Frequencia


class Curso(TimestampMixin, Base):
    __tablename__ = "curso"
    __table_args__ = (
        UniqueConstraint("campus_id", "codigo", name="uq_curso_campus_codigo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campus.id", ondelete="RESTRICT"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    codigo: Mapped[str] = mapped_column(String(30), nullable=False)

    campus: Mapped["Campus"] = relationship("Campus")
    disciplinas: Mapped[List["Disciplina"]] = relationship("Disciplina", back_populates="curso")


class Disciplina(TimestampMixin, Base):
    __tablename__ = "disciplina"
    __table_args__ = (
        UniqueConstraint("curso_id", "codigo", name="uq_disciplina_curso_codigo"),
        CheckConstraint("carga_horaria > 0", name="ck_disciplina_carga_horaria_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    curso_id: Mapped[int] = mapped_column(ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    codigo: Mapped[str] = mapped_column(String(30), nullable=False)
    carga_horaria: Mapped[int] = mapped_column(Integer, nullable=False)

    curso: Mapped["Curso"] = relationship("Curso", back_populates="disciplinas")
    turmas: Mapped[List["Turma"]] = relationship("Turma", back_populates="disciplina")


class Turma(TimestampMixin, Base):
    __tablename__ = "turma"
    __table_args__ = (
        CheckConstraint("num_matriculados >= 0", name="ck_turma_num_matriculados_positivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    disciplina_id: Mapped[int] = mapped_column(ForeignKey("disciplina.id", ondelete="RESTRICT"), nullable=False, index=True)
    professor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True, index=True)
    periodo_letivo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    num_matriculados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    turno_preferido: Mapped[Turno] = mapped_column(
        SQLEnum(Turno, native_enum=False, create_constraint=True, validate_strings=True, values_callable=lambda x: [e.value for e in x], length=20),
        nullable=False
    )

    disciplina: Mapped["Disciplina"] = relationship("Disciplina", back_populates="turmas")
    professor: Mapped[Optional["Usuario"]] = relationship("Usuario")
    matriculas: Mapped[List["Matricula"]] = relationship("Matricula", back_populates="turma")
    horarios: Mapped[List["Horario"]] = relationship("Horario", back_populates="turma")


class Matricula(Base):
    __tablename__ = "matricula"
    __table_args__ = (
        UniqueConstraint("aluno_id", "turma_id", name="uq_matricula_aluno_turma"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False, index=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turma.id", ondelete="CASCADE"), nullable=False, index=True)
    data_matricula: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ativa", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    aluno: Mapped["Usuario"] = relationship("Usuario")
    turma: Mapped["Turma"] = relationship("Turma", back_populates="matriculas")
    frequencias: Mapped[List["Frequencia"]] = relationship("Frequencia", back_populates="matricula")
