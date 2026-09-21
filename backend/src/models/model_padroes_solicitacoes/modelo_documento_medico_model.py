from datetime import datetime

from src.settings.extensions import db


class ModeloDocumentoMedico(db.Model):
    __tablename__ = "MODELO_DOCUMENTO_MEDICO"

    id = db.Column(db.Integer, primary_key=True)
    medico_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    nome_modelo = db.Column(db.String(255), nullable=False)
    titulo_documento = db.Column(db.String(255), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __init__(self, nome_modelo, titulo_documento, medico_id, conteudo):
        self.nome_modelo = nome_modelo
        self.titulo_documento = titulo_documento
        self.medico_id = medico_id
        self.conteudo = conteudo

    def _to_dict(self):
        return {
            "id": self.id,
            "nome_modelo": self.nome_modelo,
            "titulo_documento": self.titulo_documento,
            "medico_id": self.medico_id,
            "conteudo": self.conteudo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
