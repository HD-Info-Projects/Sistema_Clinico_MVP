"""add paciente nome social to SPDATA mirrors.

Revision ID: 5e7f9a1b2c3d
Revises: f1a2b3c4d5e6
Create Date: 2026-08-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "5e7f9a1b2c3d"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


TABLES = (
    "MED_SPDATA_AGENDA",
    "MED_SPDATA_ATENDIMENTOS",
)


def table_exists(table_name):
    return table_name in inspect(op.get_bind()).get_table_names()


def table_columns(table_name):
    if not table_exists(table_name):
        return set()
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def add_column_if_missing(table_name, column):
    if column.name in table_columns(table_name):
        return
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.add_column(column)


def drop_column_if_exists(table_name, column_name):
    if column_name not in table_columns(table_name):
        return
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.drop_column(column_name)


def upgrade():
    for table_name in TABLES:
        add_column_if_missing(
            table_name,
            sa.Column("paciente_nome_social", sa.String(length=255), nullable=True),
        )


def downgrade():
    for table_name in reversed(TABLES):
        drop_column_if_exists(table_name, "paciente_nome_social")
