"""Identifica edições de atendimentos concluídos.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("MED_ATENDIMENTOS", sa.Column("em_edicao", sa.Boolean(), nullable=False, server_default=sa.false()))

    # Recupera reaberturas antigas somente quando há uma consulta clínica finalizada.
    controle = sa.table("MED_ATENDIMENTOS", sa.column("id"), sa.column("spdata_atendimento_id"),
                        sa.column("status"), sa.column("finished_at", sa.DateTime()), sa.column("em_edicao"))
    clinico = sa.table("atendimentos", sa.column("spdata_atendimento_id"), sa.column("status"),
                       sa.column("data_atendimento", sa.DateTime()), sa.column("hora_fim", sa.Time()))
    bind = op.get_bind()
    registros = bind.execute(sa.select(controle.c.id, clinico.c.data_atendimento, clinico.c.hora_fim)
        .select_from(controle.join(clinico, controle.c.spdata_atendimento_id == clinico.c.spdata_atendimento_id))
        .where(controle.c.status.in_(["EM_ATENDIMENTO", "em-atendimento", "em_atendimento"]),
               clinico.c.status == "finalizado")).all()
    for registro in registros:
        valores = {"em_edicao": True}
        if registro.data_atendimento and registro.hora_fim:
            valores["finished_at"] = datetime.combine(registro.data_atendimento.date(), registro.hora_fim)
        bind.execute(controle.update().where(controle.c.id == registro.id).values(**valores))


def downgrade():
    op.drop_column("MED_ATENDIMENTOS", "em_edicao")
