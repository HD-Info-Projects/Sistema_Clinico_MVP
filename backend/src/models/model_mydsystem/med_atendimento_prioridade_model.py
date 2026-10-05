from datetime import datetime

from sqlalchemy import false

from src.settings.extensions import db


class MedAtendimentoPrioridade(db.Model):
    __tablename__ = "MED_ATENDIMENTO_PRIORIDADES"
    __table_args__ = (
        db.UniqueConstraint(
            "unidade_id",
            "origem",
            "spdata_id",
            name="uq_med_atendimento_prioridade_referencia",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(db.Integer, nullable=False, index=True)
    origem = db.Column(db.String(20), nullable=False)
    spdata_id = db.Column(db.Integer, nullable=False)
    prioridade = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
