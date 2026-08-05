"""add admin users status and units.

Revision ID: 4b7c9d1e2f03
Revises: d4e5f6a7b8c9
Create Date: 2026-08-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "4b7c9d1e2f03"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def table_exists(table_name):
    return table_name in inspect(op.get_bind()).get_table_names()


def table_columns(table_name):
    if not table_exists(table_name):
        return set()
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def upgrade():
    if "ativo" not in table_columns("usuarios"):
        with op.batch_alter_table("usuarios", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "ativo",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                )
            )

    if not table_exists("unidades"):
        op.create_table(
            "unidades",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=255), nullable=False),
            sa.Column("slug", sa.String(length=120), nullable=False),
            sa.Column("codigo_spdata_centro_custo", sa.Integer(), nullable=True),
            sa.Column("codigo_spdata_agenda", sa.String(length=50), nullable=True),
            sa.Column("endereco", sa.String(length=500), nullable=True),
            sa.Column("telefone", sa.String(length=50), nullable=True),
            sa.Column("ativa", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug", name="uq_unidades_slug"),
        )
        op.create_index(
            "ix_unidades_codigo_spdata_centro_custo",
            "unidades",
            ["codigo_spdata_centro_custo"],
        )
        op.create_index(
            "ix_unidades_codigo_spdata_agenda",
            "unidades",
            ["codigo_spdata_agenda"],
        )


def downgrade():
    if table_exists("unidades"):
        op.drop_table("unidades")

    if "ativo" in table_columns("usuarios"):
        with op.batch_alter_table("usuarios", schema=None) as batch_op:
            batch_op.drop_column("ativo")
