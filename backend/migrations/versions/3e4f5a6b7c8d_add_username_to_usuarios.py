"""Add optional usernames for user authentication.

Revision ID: 3e4f5a6b7c8d
Revises: 4b5c6d7e8f90
"""

from alembic import op
import sqlalchemy as sa


revision = "3e4f5a6b7c8d"
down_revision = "4b5c6d7e8f90"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(length=30), nullable=True))
        batch_op.create_index("ix_usuarios_username", ["username"], unique=True)
        batch_op.alter_column("email", existing_type=sa.String(length=255), nullable=True)


def downgrade():
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(length=255), nullable=False)
        batch_op.drop_index("ix_usuarios_username")
        batch_op.drop_column("username")
