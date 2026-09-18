"""Add login rate limit reset version.

Revision ID: 2c3d4e5f6a7b
Revises: 1b2c3d4e5f60
Create Date: 2026-09-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "2c3d4e5f6a7b"
down_revision = "1b2c3d4e5f60"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "login_rate_limit_version",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )

    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.alter_column("login_rate_limit_version", server_default=None)


def downgrade():
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.drop_column("login_rate_limit_version")
