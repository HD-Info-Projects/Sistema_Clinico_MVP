"""add exam request orientations.

Revision ID: 6f7a8b9c0d1e
Revises: 5e6f7a8b9c0d
Create Date: 2026-07-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "6f7a8b9c0d1e"
down_revision = "5e6f7a8b9c0d"
branch_labels = None
depends_on = None


def table_exists(table_name):
    return table_name in inspect(op.get_bind()).get_table_names()


def table_columns(table_name):
    if not table_exists(table_name):
        return set()
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def table_indexes(table_name):
    if not table_exists(table_name):
        return set()
    return {index["name"] for index in inspect(op.get_bind()).get_indexes(table_name)}


def upgrade():
    if "orientacao" not in table_columns("solicitacoes_exames"):
        with op.batch_alter_table("solicitacoes_exames", schema=None) as batch_op:
            batch_op.add_column(sa.Column("orientacao", sa.Text(), nullable=True))

    if not table_exists("MODELO_ORIENTACAO_EXAME"):
        op.create_table(
            "MODELO_ORIENTACAO_EXAME",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nome_modelo", sa.String(length=255), nullable=False),
            sa.Column("medico_id", sa.Integer(), nullable=False),
            sa.Column("conteudo", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["medico_id"], ["usuarios.id"], name="fk_modelo_orientacao_exame_medico_id"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_MODELO_ORIENTACAO_EXAME_medico_id",
            "MODELO_ORIENTACAO_EXAME",
            ["medico_id"],
        )


def downgrade():
    if table_exists("MODELO_ORIENTACAO_EXAME"):
        indexes = table_indexes("MODELO_ORIENTACAO_EXAME")
        with op.batch_alter_table("MODELO_ORIENTACAO_EXAME", schema=None) as batch_op:
            if "ix_MODELO_ORIENTACAO_EXAME_medico_id" in indexes:
                batch_op.drop_index("ix_MODELO_ORIENTACAO_EXAME_medico_id")
            batch_op.drop_constraint("fk_modelo_orientacao_exame_medico_id", type_="foreignkey")
        op.drop_table("MODELO_ORIENTACAO_EXAME")

    if "orientacao" in table_columns("solicitacoes_exames"):
        with op.batch_alter_table("solicitacoes_exames", schema=None) as batch_op:
            batch_op.drop_column("orientacao")
