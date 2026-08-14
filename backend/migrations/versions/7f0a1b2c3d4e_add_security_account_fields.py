"""add security account fields

Revision ID: 7f0a1b2c3d4e
Revises: 4b7c9d2e1f0a
Create Date: 2026-08-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7f0a1b2c3d4e"
down_revision = "4b7c9d2e1f0a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.add_column(sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("bloqueado_em", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("ultimo_login_em", sa.DateTime(), nullable=True))

    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.alter_column("ativo", server_default=None)


def downgrade():
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.drop_column("ultimo_login_em")
        batch_op.drop_column("bloqueado_em")
        batch_op.drop_column("ativo")
