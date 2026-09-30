"""create MED_SPDATA_ANAMNESES mirror table.

Revision ID: 7b8c9d0e1f2a
Revises: 6a7b8c9d0e1f
Create Date: 2026-09-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "7b8c9d0e1f2a"
down_revision = "6a7b8c9d0e1f"
branch_labels = None
depends_on = None


TABLE = "MED_SPDATA_ANAMNESES"


def upgrade():
    if TABLE in inspect(op.get_bind()).get_table_names():
        return

    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_cabevol", sa.BigInteger(), nullable=False),
        sa.Column("id_htatendimento", sa.BigInteger(), nullable=True),
        sa.Column("id_evolucao", sa.BigInteger(), nullable=True),
        sa.Column("modelo_cod", sa.String(length=20), nullable=True),
        sa.Column("modelo_descricao", sa.String(length=255), nullable=True),
        sa.Column("id_paciente_spdata", sa.BigInteger(), nullable=True),
        sa.Column("prontuario", sa.String(length=50), nullable=True),
        sa.Column("paciente", sa.String(length=255), nullable=True),
        sa.Column("data_hora_evolucao", sa.DateTime(), nullable=True),
        sa.Column("anamnese", sa.Text(), nullable=True),
        sa.Column("dados_spdata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table(TABLE, schema=None) as batch_op:
        batch_op.create_index("ix_MED_SPDATA_ANAMNESES_id_cabevol", ["id_cabevol"], unique=True)
        batch_op.create_index("ix_MED_SPDATA_ANAMNESES_id_htatendimento", ["id_htatendimento"], unique=False)
        batch_op.create_index("ix_MED_SPDATA_ANAMNESES_id_paciente_spdata", ["id_paciente_spdata"], unique=False)
        batch_op.create_index("ix_MED_SPDATA_ANAMNESES_prontuario", ["prontuario"], unique=False)
        batch_op.create_index("ix_MED_SPDATA_ANAMNESES_data_hora_evolucao", ["data_hora_evolucao"], unique=False)


def downgrade():
    if TABLE not in inspect(op.get_bind()).get_table_names():
        return

    op.drop_table(TABLE)
