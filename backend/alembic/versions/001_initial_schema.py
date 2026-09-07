"""Schema inicial com as 14 tabelas do SIGAAS.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Campus
    op.create_table(
        "campus",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("cidade", sa.String(length=100), nullable=False),
        sa.Column("endereco", sa.String(length=255), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Usuario
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campus_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("perfil", sa.String(length=30), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["campus_id"], ["campus.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_usuario_campus_id", "usuario", ["campus_id"], unique=False)
    op.create_index("ix_usuario_email", "usuario", ["email"], unique=True)

    # 3. Equipamento
    op.create_table(
        "equipamento",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    # 4. Sala
    op.create_table(
        "sala",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campus_id", sa.Integer(), nullable=False),
        sa.Column("bloco", sa.String(length=50), nullable=False),
        sa.Column("numero", sa.String(length=50), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("capacidade", sa.Integer(), nullable=False),
        sa.Column("turnos_disponiveis", sa.JSON(), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("capacidade > 0", name="ck_sala_capacidade_positiva"),
        sa.ForeignKeyConstraint(["campus_id"], ["campus.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campus_id", "bloco", "numero", name="uq_sala_campus_bloco_numero"),
    )
    op.create_index("ix_sala_campus_id", "sala", ["campus_id"], unique=False)

    # 5. SalaEquipamento
    op.create_table(
        "sala_equipamento",
        sa.Column("sala_id", sa.Integer(), nullable=False),
        sa.Column("equipamento_id", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("quantidade > 0", name="ck_sala_equipamento_quantidade_positiva"),
        sa.ForeignKeyConstraint(["equipamento_id"], ["equipamento.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sala_id"], ["sala.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("sala_id", "equipamento_id"),
    )

    # 6. Curso
    op.create_table(
        "curso",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campus_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("codigo", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["campus_id"], ["campus.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campus_id", "codigo", name="uq_curso_campus_codigo"),
    )
    op.create_index("ix_curso_campus_id", "curso", ["campus_id"], unique=False)

    # 7. Disciplina
    op.create_table(
        "disciplina",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("curso_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("codigo", sa.String(length=30), nullable=False),
        sa.Column("carga_horaria", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("carga_horaria > 0", name="ck_disciplina_carga_horaria_positiva"),
        sa.ForeignKeyConstraint(["curso_id"], ["curso.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("curso_id", "codigo", name="uq_disciplina_curso_codigo"),
    )
    op.create_index("ix_disciplina_curso_id", "disciplina", ["curso_id"], unique=False)

    # 8. Turma
    op.create_table(
        "turma",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("disciplina_id", sa.Integer(), nullable=False),
        sa.Column("professor_id", sa.Integer(), nullable=True),
        sa.Column("periodo_letivo", sa.String(length=20), nullable=False),
        sa.Column("num_matriculados", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("turno_preferido", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("num_matriculados >= 0", name="ck_turma_num_matriculados_positivo"),
        sa.ForeignKeyConstraint(["disciplina_id"], ["disciplina.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["professor_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_turma_disciplina_id", "turma", ["disciplina_id"], unique=False)
    op.create_index("ix_turma_professor_id", "turma", ["professor_id"], unique=False)
    op.create_index("ix_turma_periodo_letivo", "turma", ["periodo_letivo"], unique=False)

    # 9. Matricula
    op.create_table(
        "matricula",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("aluno_id", sa.Integer(), nullable=False),
        sa.Column("turma_id", sa.Integer(), nullable=False),
        sa.Column("data_matricula", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="ativa", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["aluno_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["turma_id"], ["turma.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aluno_id", "turma_id", name="uq_matricula_aluno_turma"),
    )
    op.create_index("ix_matricula_aluno_id", "matricula", ["aluno_id"], unique=False)
    op.create_index("ix_matricula_turma_id", "matricula", ["turma_id"], unique=False)

    # 10. Horario
    op.create_table(
        "horario",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campus_id", sa.Integer(), nullable=False),
        sa.Column("turma_id", sa.Integer(), nullable=False),
        sa.Column("sala_id", sa.Integer(), nullable=False),
        sa.Column("dia_semana", sa.SmallInteger(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fim", sa.Time(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("hora_inicio < hora_fim", name="ck_horario_inicio_anterior_fim"),
        sa.CheckConstraint("dia_semana >= 0 AND dia_semana <= 6", name="ck_horario_dia_semana_valido"),
        sa.ForeignKeyConstraint(["campus_id"], ["campus.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sala_id"], ["sala.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["turma_id"], ["turma.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_horario_campus_id", "horario", ["campus_id"], unique=False)
    op.create_index("ix_horario_sala_id", "horario", ["sala_id"], unique=False)
    op.create_index("ix_horario_turma_id", "horario", ["turma_id"], unique=False)

    # 11. LogAlocacao
    op.create_table(
        "log_alocacao",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("horario_id", sa.Integer(), nullable=True),
        sa.Column("snapshot_evento", sa.JSON(), nullable=True),
        sa.Column("tipo_evento", sa.String(length=50), nullable=False),
        sa.Column("usuario_responsavel", sa.Integer(), nullable=False),
        sa.Column("detalhes", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["horario_id"], ["horario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_responsavel"], ["usuario.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_log_alocacao_horario_id", "log_alocacao", ["horario_id"], unique=False)
    op.create_index("ix_log_alocacao_timestamp", "log_alocacao", ["timestamp"], unique=False)

    # 12. Frequencia
    op.create_table(
        "frequencia",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("matricula_id", sa.Integer(), nullable=False),
        sa.Column("horario_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("presente", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["horario_id"], ["horario.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matricula_id"], ["matricula.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_frequencia_data", "frequencia", ["data"], unique=False)
    op.create_index("ix_frequencia_horario_id", "frequencia", ["horario_id"], unique=False)
    op.create_index("ix_frequencia_matricula_id", "frequencia", ["matricula_id"], unique=False)

    # 13. PrevisaoFalta
    op.create_table(
        "previsao_falta",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("turma_id", sa.Integer(), nullable=False),
        sa.Column("horario_id", sa.Integer(), nullable=False),
        sa.Column("data_prevista", sa.Date(), nullable=False),
        sa.Column("prob_ausencia", sa.Float(), nullable=False),
        sa.Column("versao_modelo", sa.String(length=50), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["horario_id"], ["horario.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["turma_id"], ["turma.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_previsao_falta_horario_id", "previsao_falta", ["horario_id"], unique=False)
    op.create_index("ix_previsao_falta_turma_id", "previsao_falta", ["turma_id"], unique=False)

    # 14. SugestaoRemanejamento
    op.create_table(
        "sugestao_remanejamento",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("horario_id", sa.Integer(), nullable=False),
        sa.Column("sala_atual_id", sa.Integer(), nullable=False),
        sa.Column("sala_sugerida_id", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("justificativa", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pendente", nullable=False),
        sa.Column("aprovado_por", sa.Integer(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["aprovado_por"], ["usuario.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["horario_id"], ["horario.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sala_atual_id"], ["sala.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sala_sugerida_id"], ["sala.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sugestao_remanejamento_horario_id", "sugestao_remanejamento", ["horario_id"], unique=False)


def downgrade() -> None:
    op.drop_table("sugestao_remanejamento")
    op.drop_table("previsao_falta")
    op.drop_table("frequencia")
    op.drop_table("log_alocacao")
    op.drop_table("horario")
    op.drop_table("matricula")
    op.drop_table("turma")
    op.drop_table("disciplina")
    op.drop_table("curso")
    op.drop_table("sala_equipamento")
    op.drop_table("sala")
    op.drop_table("equipamento")
    op.drop_table("usuario")
    op.drop_table("campus")
