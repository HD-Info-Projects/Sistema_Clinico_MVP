"""add procedimento spdata columns.

Revision ID: c4d2e6f8a1b3
Revises: 9a0b1c2d3e4f
Create Date: 2026-08-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "c4d2e6f8a1b3"
down_revision = "9a0b1c2d3e4f"
branch_labels = None
depends_on = None


def table_columns(table_name):
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def table_indexes(table_name):
    return {index["name"] for index in inspect(op.get_bind()).get_indexes(table_name)}


def add_column_if_missing(table_name, column):
    if column.name in table_columns(table_name):
        return

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.add_column(column)


def create_index_if_missing(table_name, index_name, columns, unique=False):
    if index_name in table_indexes(table_name):
        return

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.create_index(index_name, columns, unique=unique)


def drop_index_if_exists(table_name, index_name):
    if index_name not in table_indexes(table_name):
        return

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.drop_index(index_name)


def upgrade():
    add_column_if_missing(
        "MED_SPDATA_ATENDIMENTOS",
        sa.Column("cod_procedimento_spdata", sa.String(length=20), nullable=True),
    )
    add_column_if_missing(
        "MED_SPDATA_ATENDIMENTOS",
        sa.Column("procedimento_spdata", sa.String(length=255), nullable=True),
    )
    create_index_if_missing(
        "MED_SPDATA_ATENDIMENTOS",
        "ix_med_spdata_atendimentos_cod_procedimento_spdata",
        ["cod_procedimento_spdata"],
    )

    add_column_if_missing(
        "MED_SPDATA_AGENDA",
        sa.Column("cod_procedimento_spdata", sa.String(length=20), nullable=True),
    )
    add_column_if_missing(
        "MED_SPDATA_AGENDA",
        sa.Column("procedimento_spdata", sa.String(length=255), nullable=True),
    )
    create_index_if_missing(
        "MED_SPDATA_AGENDA",
        "ix_med_spdata_agenda_cod_procedimento_spdata",
        ["cod_procedimento_spdata"],
    )


def downgrade():
    drop_index_if_exists(
        "MED_SPDATA_ATENDIMENTOS",
        "ix_med_spdata_atendimentos_cod_procedimento_spdata",
    )
    with op.batch_alter_table("MED_SPDATA_ATENDIMENTOS", schema=None) as batch_op:
        batch_op.drop_column("cod_procedimento_spdata")
        batch_op.drop_column("procedimento_spdata")

    drop_index_if_exists(
        "MED_SPDATA_AGENDA",
        "ix_med_spdata_agenda_cod_procedimento_spdata",
    )
    with op.batch_alter_table("MED_SPDATA_AGENDA", schema=None) as batch_op:
        batch_op.drop_column("cod_procedimento_spdata")
        batch_op.drop_column("procedimento_spdata")