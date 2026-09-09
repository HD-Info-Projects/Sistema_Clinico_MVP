"""Ensure SPDATA agenda codes for unidades.

Revision ID: 1b2c3d4e5f60
Revises: 0bd880e6f82f
Create Date: 2026-08-26 00:00:00.000000
"""

from alembic import op


revision = "1b2c3d4e5f60"
down_revision = "0bd880e6f82f"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE unidades
        SET codigo_spdata_agenda = '16',
            updated_at = CURRENT_TIMESTAMP
        WHERE slug = 'natus'
          AND codigo_spdata_centro_custo = 340
    """)
    op.execute("""
        UPDATE unidades
        SET codigo_spdata_agenda = '17',
            updated_at = CURRENT_TIMESTAMP
        WHERE slug = 'centro-ami'
          AND codigo_spdata_centro_custo = 350
    """)


def downgrade():
    op.execute("""
        UPDATE unidades
        SET codigo_spdata_agenda = '340',
            updated_at = CURRENT_TIMESTAMP
        WHERE slug = 'natus'
          AND codigo_spdata_centro_custo = 340
    """)
    op.execute("""
        UPDATE unidades
        SET codigo_spdata_agenda = '350',
            updated_at = CURRENT_TIMESTAMP
        WHERE slug = 'centro-ami'
          AND codigo_spdata_centro_custo = 350
    """)
