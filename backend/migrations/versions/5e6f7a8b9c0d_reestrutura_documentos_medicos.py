from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import mysql


revision = "5e6f7a8b9c0d"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


TABLE = "documentos_medicos"
UNIQUE_NAME = "uq_documentos_medicos_atendimento_tipo"
OLD_TIPO = mysql.ENUM(
    "ATESTADO",
    "DECLARACAO",
    "ENCAMINHAMENTO",
    "RELATORIO",
    "RECEITA",
    name="tipodocumentomedico",
)


def table_columns():
    inspector = inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(TABLE)}


def table_indexes():
    inspector = inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(TABLE)}


def assert_table_empty():
    total = op.get_bind().execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar()
    if total:
        raise RuntimeError(
            f"A tabela {TABLE} possui {total} registro(s). "
            "A migration foi interrompida para evitar perda de dados."
        )


def upgrade():
    assert_table_empty()
    columns = table_columns()

    with op.batch_alter_table(TABLE, schema=None) as batch_op:
        batch_op.alter_column(
            "tipo_documento",
            existing_type=OLD_TIPO,
            type_=sa.String(length=50),
            existing_nullable=False,
        )

        if "dados" not in columns:
            batch_op.add_column(sa.Column("dados", sa.JSON(), nullable=False))
        if "updated_at" not in columns:
            batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=False))
        if "conteudo" in columns:
            batch_op.drop_column("conteudo")
        if "arquivo_pdf" in columns:
            batch_op.drop_column("arquivo_pdf")
        if "assinado" in columns:
            batch_op.drop_column("assinado")

    if UNIQUE_NAME not in table_indexes():
        with op.batch_alter_table(TABLE, schema=None) as batch_op:
            batch_op.create_index(
                UNIQUE_NAME,
                ["atendimento_id", "tipo_documento"],
                unique=True,
            )


def downgrade():
    assert_table_empty()
    columns = table_columns()

    if UNIQUE_NAME in table_indexes():
        with op.batch_alter_table(TABLE, schema=None) as batch_op:
            batch_op.drop_index(UNIQUE_NAME)

    with op.batch_alter_table(TABLE, schema=None) as batch_op:
        if "conteudo" not in columns:
            batch_op.add_column(sa.Column("conteudo", sa.Text(), nullable=False))
        if "arquivo_pdf" not in columns:
            batch_op.add_column(sa.Column("arquivo_pdf", sa.String(length=255), nullable=True))
        if "assinado" not in columns:
            batch_op.add_column(sa.Column("assinado", sa.Boolean(), nullable=False))
        if "dados" in columns:
            batch_op.drop_column("dados")
        if "updated_at" in columns:
            batch_op.drop_column("updated_at")

        batch_op.alter_column(
            "tipo_documento",
            existing_type=sa.String(length=50),
            type_=OLD_TIPO,
            existing_nullable=False,
        )
