"""Make auditoria acao flexible.

Revision ID: 4b7c9d2e1f0a
Revises: 6f7a8b9c0d1e
Create Date: 2026-07-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "4b7c9d2e1f0a"
down_revision = "6f7a8b9c0d1e"
branch_labels = None
depends_on = None


OLD_ACAO_ENUM = sa.Enum(
    "VISUALIZOU_PRONTUARIO",
    "INICIOU_ATENDIMENTO",
    "EDITOU_EVOLUCAO",
    "FINALIZOU_ATENDIMENTO",
    "GEROU_RECEITA",
    "GEROU_ATESTADO",
    "SINCRONIZOU_SPDATA",
    name="acaoauditoria",
)


def upgrade():
    op.alter_column(
        "auditorias",
        "acao",
        existing_type=OLD_ACAO_ENUM,
        type_=sa.String(length=100),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "auditorias",
        "acao",
        existing_type=sa.String(length=100),
        type_=OLD_ACAO_ENUM,
        existing_nullable=False,
    )
