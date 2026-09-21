"""create personalized printable medical documents."""

from alembic import op
import sqlalchemy as sa


revision = "3a4b5c6d7e8f"
down_revision = "2c3d4e5f6a7b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "documentos_medicos_personalizados",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("atendimento_id", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("medico", sa.String(length=255), nullable=True),
        sa.Column("crm", sa.String(length=50), nullable=True),
        sa.Column("especialidade", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["atendimento_id"], ["atendimentos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_documentos_medicos_personalizados_atendimento_id",
        "documentos_medicos_personalizados",
        ["atendimento_id"],
    )


def downgrade():
    op.drop_index(
        "ix_documentos_medicos_personalizados_atendimento_id",
        table_name="documentos_medicos_personalizados",
    )
    op.drop_table("documentos_medicos_personalizados")
