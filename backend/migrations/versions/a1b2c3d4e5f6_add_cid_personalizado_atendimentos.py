"""add cid personalizado to atendimentos

Revision ID: a1b2c3d4e5f6
Revises: 9f0a1b2c3d4e
Create Date: 2026-10-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "9f0a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "atendimentos",
        sa.Column("cid_personalizado", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "atendimentos",
        sa.Column(
            "cid_personalizado_descricao",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("atendimentos", "cid_personalizado_descricao")
    op.drop_column("atendimentos", "cid_personalizado")
