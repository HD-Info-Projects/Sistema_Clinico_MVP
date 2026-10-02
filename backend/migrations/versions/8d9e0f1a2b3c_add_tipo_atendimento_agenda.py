"""Add tipo atendimento spdata to agenda mirror.

Revision ID: 8d9e0f1a2b3c
Revises: 7c8d9e0f1a2b
Create Date: 2026-10-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "8d9e0f1a2b3c"
down_revision = "7c8d9e0f1a2b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "MED_SPDATA_AGENDA",
        sa.Column("tipo_atendimento_spdata", sa.String(50), nullable=True),
    )


def downgrade():
    op.drop_column("MED_SPDATA_AGENDA", "tipo_atendimento_spdata")