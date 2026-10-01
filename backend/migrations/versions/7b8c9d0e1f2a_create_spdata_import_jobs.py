"""create spdata import jobs.

Revision ID: 7b8c9d0e1f2a
Revises: 6a7b8c9d0e1f
Create Date: 2026-10-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7b8c9d0e1f2a"
down_revision = "6a7b8c9d0e1f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "spdata_import_jobs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("rq_job_id", sa.String(length=100), nullable=True),
        sa.Column("target", sa.String(length=30), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("active_key", sa.String(length=64), nullable=True),
        sa.Column("requested_by_id", sa.Integer(), nullable=True),
        sa.Column("batch_size", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("current_stage", sa.String(length=30), nullable=True),
        sa.Column("progress", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("queued_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("active_key", name="uq_spdata_import_jobs_active_key"),
        sa.UniqueConstraint("rq_job_id", name="uq_spdata_import_jobs_rq_job_id"),
    )
    op.create_index("ix_spdata_import_jobs_created_at", "spdata_import_jobs", ["created_at"])
    op.create_index("ix_spdata_import_jobs_requested_by_id", "spdata_import_jobs", ["requested_by_id"])
    op.create_index(
        "ix_spdata_import_jobs_status_created",
        "spdata_import_jobs",
        ["status", "created_at", "id"],
    )


def downgrade():
    op.drop_index("ix_spdata_import_jobs_status_created", table_name="spdata_import_jobs")
    op.drop_index("ix_spdata_import_jobs_requested_by_id", table_name="spdata_import_jobs")
    op.drop_index("ix_spdata_import_jobs_created_at", table_name="spdata_import_jobs")
    op.drop_table("spdata_import_jobs")
