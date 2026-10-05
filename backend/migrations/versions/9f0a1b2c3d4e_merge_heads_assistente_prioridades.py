"""merge heads: feature assistente + main prioridades

Revision ID: 9f0a1b2c3d4e
Revises: 8d9e0f1a2b3c, 7c8d9e0f1a2b
Create Date: 2026-10-05 00:00:00.000000

Une o ramo da feature (vínculo assistente-médico + tipo de atendimento)
com o ramo da main (tabela de prioridades), que nasceram do mesmo
ancestral 6a7b8c9d0e1f com o mesmo revision ID 7c8d9e0f1a2b.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f0a1b2c3d4e"
down_revision = ("8d9e0f1a2b3c", "7c8d9e0f1a2b")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
