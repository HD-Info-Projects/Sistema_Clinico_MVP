from datetime import datetime, time
from importlib import import_module

from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa


def test_migration_identifica_apenas_reaberturas_com_consulta_finalizada(monkeypatch):
    migration = import_module("migrations.versions.b2c3d4e5f6a7_add_em_edicao_atendimentos")
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    controle = sa.Table("MED_ATENDIMENTOS", metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("spdata_atendimento_id", sa.Integer),
        sa.Column("status", sa.String),
        sa.Column("finished_at", sa.DateTime))
    clinico = sa.Table("atendimentos", metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("spdata_atendimento_id", sa.Integer),
        sa.Column("status", sa.String),
        sa.Column("data_atendimento", sa.DateTime),
        sa.Column("hora_fim", sa.Time))
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(controle.insert(), [
            {"id": 1, "spdata_atendimento_id": 11, "status": "EM_ATENDIMENTO"},
            {"id": 2, "spdata_atendimento_id": 22, "status": "EM_ATENDIMENTO"},
            {"id": 3, "spdata_atendimento_id": 33, "status": "ATENDIDO"},
        ])
        connection.execute(clinico.insert(), [
            {"id": 1, "spdata_atendimento_id": 11, "status": "finalizado",
             "data_atendimento": datetime(2026, 10, 7, 9), "hora_fim": time(9, 30)},
            {"id": 2, "spdata_atendimento_id": 22, "status": "em-atendimento",
             "data_atendimento": datetime(2026, 10, 7, 10), "hora_fim": None},
        ])
        monkeypatch.setattr(migration, "op", Operations(MigrationContext.configure(connection)))
        migration.upgrade()
        atualizado = sa.Table("MED_ATENDIMENTOS", sa.MetaData(), autoload_with=connection)
        rows = connection.execute(sa.select(atualizado).order_by(atualizado.c.id)).mappings().all()
        assert rows[0]["em_edicao"] is True
        assert rows[0]["finished_at"] == datetime(2026, 10, 7, 9, 30)
        assert rows[1]["em_edicao"] is False
        assert rows[1]["finished_at"] is None
        assert rows[2]["em_edicao"] is False
        migration.downgrade()
        assert "em_edicao" not in {column["name"] for column in sa.inspect(connection).get_columns("MED_ATENDIMENTOS")}
