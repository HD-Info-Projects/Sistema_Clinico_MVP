from datetime import datetime

from src.settings.extensions import db


class DocumentoPersonalizado(db.Model):
    __tablename__ = "documentos_medicos_personalizados"

    id = db.Column(db.Integer, primary_key=True)
    atendimento_id = db.Column(
        db.Integer,
        db.ForeignKey("atendimentos.id"),
        nullable=False,
        index=True,
    )
    titulo = db.Column(db.String(255), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    medico = db.Column(db.String(255), nullable=True)
    crm = db.Column(db.String(50), nullable=True)
    especialidade = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    atendimento = db.relationship("Atendimento")
