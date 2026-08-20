"""create procedimentos cache.

Revision ID: 0f1e2d3c4b5a
Revises: d4e5f6a7b8c9
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0f1e2d3c4b5a"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "procedimentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("spdata_tp_id", sa.Integer(), nullable=False),
        sa.Column("id_tbctrthm", sa.Integer(), nullable=False),
        sa.Column("codigo_procedimento", sa.BigInteger(), nullable=False),
        sa.Column("tab", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("apelido_procedimento", sa.String(length=100), nullable=True),
        sa.Column("tipo_modulo", sa.String(length=10), nullable=True),
        sa.Column("tipo_ato_codigo", sa.Integer(), nullable=True),
        sa.Column("tipo_ato_nome", sa.String(length=100), nullable=True),
        sa.Column("centro_tabela_nome", sa.String(length=100), nullable=True),
        sa.Column("centro_tabela_situacao", sa.String(length=10), nullable=True),
        sa.Column("situacao", sa.String(length=10), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("ch", sa.Float(), nullable=True),
        sa.Column("aux", sa.Integer(), nullable=True),
        sa.Column("filme", sa.Float(), nullable=True),
        sa.Column("cope", sa.Float(), nullable=True),
        sa.Column("procmed", sa.String(length=10), nullable=True),
        sa.Column("stand", sa.String(length=10), nullable=True),
        sa.Column("pacote", sa.String(length=10), nullable=True),
        sa.Column("tab_ref", sa.Integer(), nullable=True),
        sa.Column("proc_ref", sa.BigInteger(), nullable=True),
        sa.Column("tab_ref_tuss", sa.Integer(), nullable=True),
        sa.Column("proc_ref_tuss", sa.BigInteger(), nullable=True),
        sa.Column("exige_autorizacao", sa.Integer(), nullable=True),
        sa.Column("qtde_max_guia", sa.Integer(), nullable=True),
        sa.Column("bloqueio", sa.String(length=10), nullable=True),
        sa.Column("dados_spdata", sa.JSON(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tab", "codigo_procedimento", name="uq_procedimentos_tab_codigo"),
    )
    op.create_index("ix_procedimentos_apelido_procedimento", "procedimentos", ["apelido_procedimento"])
    op.create_index("ix_procedimentos_ativo", "procedimentos", ["ativo"])
    op.create_index("ix_procedimentos_codigo_procedimento", "procedimentos", ["codigo_procedimento"])
    op.create_index("ix_procedimentos_id_tbctrthm", "procedimentos", ["id_tbctrthm"])
    op.create_index("ix_procedimentos_nome", "procedimentos", ["nome"])
    op.create_index("ix_procedimentos_situacao", "procedimentos", ["situacao"])
    op.create_index("ix_procedimentos_spdata_tp_id", "procedimentos", ["spdata_tp_id"])
    op.create_index("ix_procedimentos_tab", "procedimentos", ["tab"])
    op.create_index("ix_procedimentos_tipo_ato_codigo", "procedimentos", ["tipo_ato_codigo"])
    op.create_index("ix_procedimentos_tipo_ato_nome", "procedimentos", ["tipo_ato_nome"])


def downgrade():
    op.drop_index("ix_procedimentos_tipo_ato_nome", table_name="procedimentos")
    op.drop_index("ix_procedimentos_tipo_ato_codigo", table_name="procedimentos")
    op.drop_index("ix_procedimentos_tab", table_name="procedimentos")
    op.drop_index("ix_procedimentos_spdata_tp_id", table_name="procedimentos")
    op.drop_index("ix_procedimentos_situacao", table_name="procedimentos")
    op.drop_index("ix_procedimentos_nome", table_name="procedimentos")
    op.drop_index("ix_procedimentos_id_tbctrthm", table_name="procedimentos")
    op.drop_index("ix_procedimentos_codigo_procedimento", table_name="procedimentos")
    op.drop_index("ix_procedimentos_ativo", table_name="procedimentos")
    op.drop_index("ix_procedimentos_apelido_procedimento", table_name="procedimentos")
    op.drop_table("procedimentos")
