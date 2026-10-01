"""create local atendimento priorities.

Revision ID: 7c8d9e0f1a2b
Revises: 6a7b8c9d0e1f
Create Date: 2026-10-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "7c8d9e0f1a2b"
down_revision = "6a7b8c9d0e1f"
branch_labels = None
depends_on = None


TABLE = "MED_ATENDIMENTO_PRIORIDADES"


def table_exists(table_name):
    return table_name in inspect(op.get_bind()).get_table_names()


def upgrade():
    if table_exists(TABLE):
        return

    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("unidade_id", sa.Integer(), nullable=False),
        sa.Column("origem", sa.String(length=20), nullable=False),
        sa.Column("spdata_id", sa.Integer(), nullable=False),
        sa.Column(
            "prioridade",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "unidade_id",
            "origem",
            "spdata_id",
            name="uq_med_atendimento_prioridade_referencia",
        ),
    )
    op.create_index(
        "ix_MED_ATENDIMENTO_PRIORIDADES_unidade_id",
        TABLE,
        ["unidade_id"],
        unique=False,
    )


def downgrade():
    if table_exists(TABLE):
        op.drop_table(TABLE)
