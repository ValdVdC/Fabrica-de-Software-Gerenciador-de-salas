"""Adiciona campus_id em log_alocacao com indice composto e backfill.

Revision ID: 002_add_campus_id_to_log_alocacao
Revises: 001_initial_schema
Create Date: 2026-10-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_add_campus_id_to_log_alocacao"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("log_alocacao") as batch_op:
        batch_op.add_column(sa.Column("campus_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_log_alocacao_campus_id", "campus", ["campus_id"], ["id"], ondelete="SET NULL"
        )
        batch_op.create_index("ix_log_alocacao_campus_id", ["campus_id"], unique=False)
        batch_op.create_index(
            "ix_log_alocacao_campus_id_timestamp", ["campus_id", "timestamp"], unique=False
        )

    op.execute(
        """
        UPDATE log_alocacao
        SET campus_id = (
            SELECT h.campus_id FROM horario h WHERE h.id = log_alocacao.horario_id
        )
        WHERE log_alocacao.horario_id IS NOT NULL AND log_alocacao.campus_id IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("log_alocacao") as batch_op:
        batch_op.drop_index("ix_log_alocacao_campus_id_timestamp")
        batch_op.drop_index("ix_log_alocacao_campus_id")
        batch_op.drop_constraint("fk_log_alocacao_campus_id", type_="foreignkey")
        batch_op.drop_column("campus_id")
