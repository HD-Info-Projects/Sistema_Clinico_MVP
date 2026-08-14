"""Fix SPDATA agenda codes for unidades.

Revision ID: f9a0b1c2d3e4
Revises: e1f2a3b4c5d6, 3c5d7e9f1a2b
Create Date: 2026-08-14 00:00:00.000000

"""

from alembic import op


revision = "f9a0b1c2d3e4"
down_revision = ("e1f2a3b4c5d6", "3c5d7e9f1a2b")
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
