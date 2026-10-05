"""Add assistente medico link.

Revision ID: 7d9e0f1a2b3d
Revises: 7b8c9d0e1f2a
Create Date: 2026-09-30 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "7d9e0f1a2b3d"
down_revision = "7b8c9d0e1f2a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "usuarios",
        sa.Column("medico_assistente_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_usuarios_medico_assistente_id_medicos",
        "usuarios",
        "medicos",
        ["medico_assistente_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_usuarios_medico_assistente_id",
        "usuarios",
        ["medico_assistente_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_usuarios_medico_assistente_id", table_name="usuarios")
    op.drop_constraint(
        "fk_usuarios_medico_assistente_id_medicos",
        "usuarios",
        type_="foreignkey",
    )
    op.drop_column("usuarios", "medico_assistente_id")
