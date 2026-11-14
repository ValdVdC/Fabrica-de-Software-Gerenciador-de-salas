"""Adiciona indices compostos de desempenho para o Release Candidate.

Revision ID: 003_release_candidate_indexes
Revises: 002_add_campus_id_to_log_alocacao
Create Date: 2026-11-14

"""
from typing import Sequence, Union
from alembic import op

revision: str = "003_release_candidate_indexes"
down_revision: Union[str, None] = "002_add_campus_id_to_log_alocacao"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_horario_turma_dia_hora",
        "horario",
        ["turma_id", "dia_semana", "hora_inicio"],
        unique=False,
    )
    op.create_index(
        "ix_horario_sala_dia_hora",
        "horario",
        ["sala_id", "dia_semana", "hora_inicio", "hora_fim"],
        unique=False,
    )
    op.create_index(
        "ix_horario_campus_dia_hora",
        "horario",
        ["campus_id", "dia_semana", "hora_inicio"],
        unique=False,
    )
    op.create_index(
        "ix_frequencia_horario_data",
        "frequencia",
        ["horario_id", "data"],
        unique=False,
    )
    op.create_index(
        "ix_previsao_falta_horario_data",
        "previsao_falta",
        ["horario_id", "data_prevista"],
        unique=False,
    )
    op.create_index(
        "ix_sugestao_remanejamento_status_criado_em",
        "sugestao_remanejamento",
        ["status", "criado_em"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sugestao_remanejamento_status_criado_em", table_name="sugestao_remanejamento")
    op.drop_index("ix_previsao_falta_horario_data", table_name="previsao_falta")
    op.drop_index("ix_frequencia_horario_data", table_name="frequencia")
    op.drop_index("ix_horario_campus_dia_hora", table_name="horario")
    op.drop_index("ix_horario_sala_dia_hora", table_name="horario")
    op.drop_index("ix_horario_turma_dia_hora", table_name="horario")
