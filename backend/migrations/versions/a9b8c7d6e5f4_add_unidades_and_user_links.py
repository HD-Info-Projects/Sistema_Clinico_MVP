"""add unidades and user links.

Revision ID: a9b8c7d6e5f4
Revises: 4b7c9d2e1f0a
Create Date: 2026-08-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "a9b8c7d6e5f4"
down_revision = "4b7c9d2e1f0a"
branch_labels = None
depends_on = None


def table_exists(table_name):
    return table_name in inspect(op.get_bind()).get_table_names()


def table_columns(table_name):
    if not table_exists(table_name):
        return set()
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def table_indexes(table_name):
    if not table_exists(table_name):
        return set()
    return {index["name"] for index in inspect(op.get_bind()).get_indexes(table_name)}


def add_column_if_missing(table_name, column):
    if not table_exists(table_name) or column.name in table_columns(table_name):
        return

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.add_column(column)


def create_index_if_missing(table_name, index_name, columns, unique=False):
    if not table_exists(table_name) or index_name in table_indexes(table_name):
        return

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.create_index(index_name, columns, unique=unique)


def drop_index_if_exists(table_name, index_name):
    if not table_exists(table_name) or index_name not in table_indexes(table_name):
        return

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.drop_index(index_name)


def create_unidades_table():
    if table_exists("unidades"):
        return

    op.create_table(
        "unidades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("codigo_spdata_centro_custo", sa.Integer(), nullable=True),
        sa.Column("codigo_spdata_agenda", sa.String(length=50), nullable=True),
        sa.Column("endereco", sa.String(length=500), nullable=True),
        sa.Column("telefone", sa.String(length=50), nullable=True),
        sa.Column("ativa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_unidades_slug"),
    )
    create_index_if_missing("unidades", "ix_unidades_codigo_spdata_centro_custo", ["codigo_spdata_centro_custo"])
    create_index_if_missing("unidades", "ix_unidades_codigo_spdata_agenda", ["codigo_spdata_agenda"])
    create_index_if_missing("unidades", "ix_unidades_ativa", ["ativa"])


def create_usuario_unidades_table():
    if table_exists("usuario_unidades"):
        return

    op.create_table(
        "usuario_unidades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("unidade_id", sa.Integer(), nullable=False),
        sa.Column("principal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["unidade_id"], ["unidades.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "unidade_id", name="uq_usuario_unidades_usuario_unidade"),
    )
    create_index_if_missing("usuario_unidades", "ix_usuario_unidades_usuario_id", ["usuario_id"])
    create_index_if_missing("usuario_unidades", "ix_usuario_unidades_unidade_id", ["unidade_id"])
    create_index_if_missing("usuario_unidades", "ix_usuario_unidades_ativo", ["ativo"])


def seed_unidades():
    op.execute("""
        INSERT INTO unidades
            (id, nome, slug, codigo_spdata_centro_custo, codigo_spdata_agenda, endereco, telefone, ativa, created_at, updated_at)
        SELECT 1, 'Natus', 'natus', 340, '340', NULL, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        WHERE NOT EXISTS (SELECT 1 FROM unidades WHERE id = 1 OR slug = 'natus')
    """)
    op.execute("""
        INSERT INTO unidades
            (id, nome, slug, codigo_spdata_centro_custo, codigo_spdata_agenda, endereco, telefone, ativa, created_at, updated_at)
        SELECT 2, 'Centro AMI', 'centro-ami', 350, '350', NULL, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        WHERE NOT EXISTS (SELECT 1 FROM unidades WHERE id = 2 OR slug = 'centro-ami')
    """)


def seed_usuario_unidades():
    if not table_exists("usuarios"):
        return

    op.execute("""
        INSERT INTO usuario_unidades (usuario_id, unidade_id, principal, ativo, created_at, updated_at)
        SELECT u.id, 2, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM usuarios u
        WHERE u.role = 'medico'
          AND NOT EXISTS (
              SELECT 1 FROM usuario_unidades uu
              WHERE uu.usuario_id = u.id AND uu.unidade_id = 2
          )
    """)
    op.execute("""
        INSERT INTO usuario_unidades (usuario_id, unidade_id, principal, ativo, created_at, updated_at)
        SELECT u.id, 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM usuarios u
        WHERE u.role = 'recepcao'
          AND NOT EXISTS (
              SELECT 1 FROM usuario_unidades uu
              WHERE uu.usuario_id = u.id AND uu.unidade_id = 1
          )
    """)
    op.execute("""
        INSERT INTO usuario_unidades (usuario_id, unidade_id, principal, ativo, created_at, updated_at)
        SELECT u.id, 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM usuarios u
        WHERE u.role = 'admin'
          AND NOT EXISTS (
              SELECT 1 FROM usuario_unidades uu
              WHERE uu.usuario_id = u.id AND uu.unidade_id = 1
          )
    """)
    op.execute("""
        INSERT INTO usuario_unidades (usuario_id, unidade_id, principal, ativo, created_at, updated_at)
        SELECT u.id, 2, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM usuarios u
        WHERE u.role = 'admin'
          AND NOT EXISTS (
              SELECT 1 FROM usuario_unidades uu
              WHERE uu.usuario_id = u.id AND uu.unidade_id = 2
          )
    """)


def add_unidade_columns():
    add_column_if_missing("MED_SPDATA_AGENDA", sa.Column("unidade_id", sa.Integer(), nullable=True))
    add_column_if_missing("MED_SPDATA_AGENDA", sa.Column("codigo_unidade_spdata", sa.String(length=50), nullable=True))
    create_index_if_missing("MED_SPDATA_AGENDA", "ix_MED_SPDATA_AGENDA_unidade_id", ["unidade_id"])
    create_index_if_missing("MED_SPDATA_AGENDA", "ix_MED_SPDATA_AGENDA_codigo_unidade_spdata", ["codigo_unidade_spdata"])

    add_column_if_missing("MED_SPDATA_ATENDIMENTOS", sa.Column("unidade_id", sa.Integer(), nullable=True))
    create_index_if_missing("MED_SPDATA_ATENDIMENTOS", "ix_MED_SPDATA_ATENDIMENTOS_unidade_id", ["unidade_id"])

    add_column_if_missing("MED_ATENDIMENTOS", sa.Column("unidade_id", sa.Integer(), nullable=True))
    create_index_if_missing("MED_ATENDIMENTOS", "ix_MED_ATENDIMENTOS_unidade_id", ["unidade_id"])

    add_column_if_missing("atendimentos", sa.Column("unidade_id", sa.Integer(), nullable=True))
    create_index_if_missing("atendimentos", "ix_atendimentos_unidade_id", ["unidade_id"])


def backfill_unidade_columns():
    if table_exists("MED_SPDATA_ATENDIMENTOS") and "unidade_id" in table_columns("MED_SPDATA_ATENDIMENTOS"):
        op.execute("""
            UPDATE MED_SPDATA_ATENDIMENTOS
            SET unidade_id = (
                SELECT unidades.id
                FROM unidades
                WHERE unidades.codigo_spdata_centro_custo = MED_SPDATA_ATENDIMENTOS.id_centro_custo_spdata
                LIMIT 1
            )
            WHERE unidade_id IS NULL
        """)

    if table_exists("MED_ATENDIMENTOS") and "unidade_id" in table_columns("MED_ATENDIMENTOS"):
        op.execute("""
            UPDATE MED_ATENDIMENTOS
            SET unidade_id = (
                SELECT MED_SPDATA_ATENDIMENTOS.unidade_id
                FROM MED_SPDATA_ATENDIMENTOS
                WHERE MED_SPDATA_ATENDIMENTOS.id = MED_ATENDIMENTOS.med_spdata_atendimento_id
                LIMIT 1
            )
            WHERE unidade_id IS NULL
        """)

    if table_exists("atendimentos") and "unidade_id" in table_columns("atendimentos"):
        op.execute("""
            UPDATE atendimentos
            SET unidade_id = (
                SELECT MED_SPDATA_ATENDIMENTOS.unidade_id
                FROM MED_SPDATA_ATENDIMENTOS
                WHERE MED_SPDATA_ATENDIMENTOS.spdata_atendimento_id = atendimentos.spdata_atendimento_id
                LIMIT 1
            )
            WHERE unidade_id IS NULL
        """)


def upgrade():
    create_unidades_table()
    create_usuario_unidades_table()
    seed_unidades()
    seed_usuario_unidades()
    add_unidade_columns()
    backfill_unidade_columns()


def downgrade():
    drop_index_if_exists("atendimentos", "ix_atendimentos_unidade_id")
    if table_exists("atendimentos") and "unidade_id" in table_columns("atendimentos"):
        with op.batch_alter_table("atendimentos", schema=None) as batch_op:
            batch_op.drop_column("unidade_id")

    drop_index_if_exists("MED_ATENDIMENTOS", "ix_MED_ATENDIMENTOS_unidade_id")
    if table_exists("MED_ATENDIMENTOS") and "unidade_id" in table_columns("MED_ATENDIMENTOS"):
        with op.batch_alter_table("MED_ATENDIMENTOS", schema=None) as batch_op:
            batch_op.drop_column("unidade_id")

    drop_index_if_exists("MED_SPDATA_ATENDIMENTOS", "ix_MED_SPDATA_ATENDIMENTOS_unidade_id")
    if table_exists("MED_SPDATA_ATENDIMENTOS") and "unidade_id" in table_columns("MED_SPDATA_ATENDIMENTOS"):
        with op.batch_alter_table("MED_SPDATA_ATENDIMENTOS", schema=None) as batch_op:
            batch_op.drop_column("unidade_id")

    drop_index_if_exists("MED_SPDATA_AGENDA", "ix_MED_SPDATA_AGENDA_codigo_unidade_spdata")
    drop_index_if_exists("MED_SPDATA_AGENDA", "ix_MED_SPDATA_AGENDA_unidade_id")
    if table_exists("MED_SPDATA_AGENDA"):
        columns = table_columns("MED_SPDATA_AGENDA")
        with op.batch_alter_table("MED_SPDATA_AGENDA", schema=None) as batch_op:
            if "codigo_unidade_spdata" in columns:
                batch_op.drop_column("codigo_unidade_spdata")
            if "unidade_id" in columns:
                batch_op.drop_column("unidade_id")

    if table_exists("usuario_unidades"):
        op.drop_table("usuario_unidades")
    if table_exists("unidades"):
        op.drop_table("unidades")
