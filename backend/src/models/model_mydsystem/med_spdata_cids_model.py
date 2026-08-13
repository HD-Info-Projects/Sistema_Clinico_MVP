from datetime import datetime

from src.settings.extensions import db


class MedSpdataCid(db.Model):
    __tablename__ = "MED_SPDATA_CIDS"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True, index=True)
    nome = db.Column(db.String(255), nullable=False, index=True)
    dados_spdata = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def _to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nome": self.nome,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
