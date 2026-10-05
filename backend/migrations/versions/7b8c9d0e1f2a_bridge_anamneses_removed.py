"""bridge: reconcile removed MED_SPDATA_ANAMNESES migration.

This migration was removed from source history (f7ab5c5). The database
still has alembic_version = '7b8c9d0e1f2a'. Create a no-op bridge so
the migration graph resolves without changing schema.

Revision ID: 7b8c9d0e1f2a
Revises: 6a7b8c9d0e1f
Create Date: 2026-09-30 00:00:00.000000
"""

revision = "7b8c9d0e1f2a"
down_revision = "6a7b8c9d0e1f"
branch_labels = None
depends_on = None


def upgrade():
    # No-op: table MED_SPDATA_ANAMNESES remains orphan as-is (intentional)
    pass


def downgrade():
    # No-op: no schema changes
    pass
