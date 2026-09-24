"""add recepcao performance composite indexes.

Revision ID: 6a7b8c9d0e1f
Revises: 3e4f5a6b7c8d
Create Date: 2026-09-24 00:00:00.000000

"""
from alembic import op
from sqlalchemy import inspect


revision = "6a7b8c9d0e1f"
down_revision = "3e4f5a6b7c8d"
branch_labels = None
depends_on = None


INDEXES = [
    ("MED_SPDATA_AGENDA", "ix_spdata_agenda_unidade_data", ["unidade_id", "data_agenda"]),
    ("MED_SPDATA_AGENDA", "ix_spdata_agenda_unidade_data_crm", ["unidade_id", "data_agenda", "crm"]),
    ("MED_SPDATA_AGENDA", "ix_spdata_agenda_unidade_data_crm_atend", ["unidade_id", "data_agenda", "crm_atend"]),
    ("MED_SPDATA_AGENDA", "ix_spdata_agenda_registro_unidade", ["registro", "unidade_id"]),
    ("MED_SPDATA_ATENDIMENTOS", "ix_spdata_atend_unidade_data", ["unidade_id", "data_atendimento"]),
    ("MED_SPDATA_ATENDIMENTOS", "ix_spdata_atend_unidade_data_crm", ["unidade_id", "data_atendimento", "crm_medico"]),
    ("MED_ATENDIMENTOS", "ix_med_atend_unidade_data_status", ["unidade_id", "data_agenda", "status"]),
    ("MED_ATENDIMENTOS", "ix_med_atend_cod_unidade", ["cod_atendimento", "unidade_id"]),
]


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


def create_index_if_missing(table_name, index_name, columns):
    if not set(columns).issubset(table_columns(table_name)):
        return
    if index_name in table_indexes(table_name):
        return

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.create_index(index_name, columns, unique=False)


def drop_index_if_exists(table_name, index_name):
    if index_name not in table_indexes(table_name):
        return

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.drop_index(index_name)


def upgrade():
    for table_name, index_name, columns in INDEXES:
        create_index_if_missing(table_name, index_name, columns)


def downgrade():
    for table_name, index_name, _columns in reversed(INDEXES):
        drop_index_if_exists(table_name, index_name)
