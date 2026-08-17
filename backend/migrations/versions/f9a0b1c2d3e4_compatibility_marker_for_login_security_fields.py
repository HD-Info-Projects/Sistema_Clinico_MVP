"""Compatibility marker for login security fields revision.

Revision ID: f9a0b1c2d3e4
Revises: e1f2a3b4c5d6
Create Date: 2026-08-17 00:00:00.000000

This no-op migration preserves compatibility with databases that were stamped
with f9a0b1c2d3e4 before the final revision ID 9a0b1c2d3e4f was introduced.
"""


revision = "f9a0b1c2d3e4"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
