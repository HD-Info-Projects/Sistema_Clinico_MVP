"""Add login attempt security fields.

Revision ID: 9a0b1c2d3e4f
Revises: e1f2a3b4c5d6
Create Date: 2026-08-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "9a0b1c2d3e4f"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def table_columns(table_name):
    return {
        column["name"]
        for column in inspect(op.get_bind()).get_columns(table_name)
    }


def upgrade():
    columns = table_columns("usuarios")
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        if "bloqueio_motivo" not in columns:
            batch_op.add_column(sa.Column("bloqueio_motivo", sa.String(length=255), nullable=True))
        if "tentativas_login_falhas" not in columns:
            batch_op.add_column(sa.Column("tentativas_login_falhas", sa.Integer(), nullable=False, server_default="0"))
        if "ultimo_login_falho_em" not in columns:
            batch_op.add_column(sa.Column("ultimo_login_falho_em", sa.DateTime(), nullable=True))
        if "senha_alterada_em" not in columns:
            batch_op.add_column(sa.Column("senha_alterada_em", sa.DateTime(), nullable=True))
        if "forcar_troca_senha" not in columns:
            batch_op.add_column(sa.Column("forcar_troca_senha", sa.Boolean(), nullable=False, server_default=sa.false()))

    columns = table_columns("usuarios")
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        if "tentativas_login_falhas" in columns:
            batch_op.alter_column("tentativas_login_falhas", server_default=None)
        if "forcar_troca_senha" in columns:
            batch_op.alter_column("forcar_troca_senha", server_default=None)


def downgrade():
    columns = table_columns("usuarios")
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        for column_name in (
            "forcar_troca_senha",
            "senha_alterada_em",
            "ultimo_login_falho_em",
            "tentativas_login_falhas",
            "bloqueio_motivo",
        ):
            if column_name in columns:
                batch_op.drop_column(column_name)
