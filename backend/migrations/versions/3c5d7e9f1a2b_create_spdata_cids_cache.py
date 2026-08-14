"""create SPDATA CIDs cache.

Revision ID: 3c5d7e9f1a2b
Revises: 0f1e2d3c4b5a
Create Date: 2026-08-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "3c5d7e9f1a2b"
down_revision = "0f1e2d3c4b5a"
branch_labels = None
depends_on = None


TABLE = "MED_SPDATA_CIDS"


def table_exists(table_name):
    return table_name in inspect(op.get_bind()).get_table_names()


def table_indexes(table_name):
    if not table_exists(table_name):
        return set()
    return {index["name"] for index in inspect(op.get_bind()).get_indexes(table_name)}


def create_index_if_missing(table_name, index_name, columns):
    if index_name in table_indexes(table_name):
        return
    op.create_index(index_name, table_name, columns)


def upgrade():
    if table_exists(TABLE):
        return

    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("dados_spdata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo", name="uq_MED_SPDATA_CIDS_codigo"),
    )
    create_index_if_missing(TABLE, "ix_MED_SPDATA_CIDS_codigo", ["codigo"])
    create_index_if_missing(TABLE, "ix_MED_SPDATA_CIDS_nome", ["nome"])


def downgrade():
    if table_exists(TABLE):
        op.drop_table(TABLE)
