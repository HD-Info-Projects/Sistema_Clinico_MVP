"""create reusable medical document templates."""

from alembic import op
import sqlalchemy as sa


revision = "4b5c6d7e8f90"
down_revision = "3a4b5c6d7e8f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "MODELO_DOCUMENTO_MEDICO",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("medico_id", sa.Integer(), nullable=False),
        sa.Column("nome_modelo", sa.String(length=255), nullable=False),
        sa.Column("titulo_documento", sa.String(length=255), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["medico_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_MODELO_DOCUMENTO_MEDICO_medico_id",
        "MODELO_DOCUMENTO_MEDICO",
        ["medico_id"],
    )


def downgrade():
    op.drop_index(
        "ix_MODELO_DOCUMENTO_MEDICO_medico_id",
        table_name="MODELO_DOCUMENTO_MEDICO",
    )
    op.drop_table("MODELO_DOCUMENTO_MEDICO")
