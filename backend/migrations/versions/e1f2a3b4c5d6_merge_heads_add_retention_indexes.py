"""Merge heads and add retention indexes.

Revision ID: e1f2a3b4c5d6
Revises: 0f1e2d3c4b5a, 7f0a1b2c3d4e
Create Date: 2026-08-13 00:00:00.000000
"""

from alembic import op


revision = "e1f2a3b4c5d6"
down_revision = ("0f1e2d3c4b5a", "7f0a1b2c3d4e")
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_logs_integracao_created_at",
        "logs_integracao",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_auditorias_created_at",
        "auditorias",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_fila_sincronizacao_status_updated_id",
        "fila_sincronizacao",
        ["status", "updated_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_atendimentos_spdata_agenda_id",
        "atendimentos",
        ["spdata_agenda_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_atendimentos_spdata_agenda_id",
        table_name="atendimentos",
    )
    op.drop_index(
        "ix_fila_sincronizacao_status_updated_id",
        table_name="fila_sincronizacao",
    )
    op.drop_index("ix_auditorias_created_at", table_name="auditorias")
    op.drop_index("ix_logs_integracao_created_at", table_name="logs_integracao")
