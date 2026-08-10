from datetime import datetime

from src.settings.extensions import db


class Unidade(db.Model):
    __tablename__ = "unidades"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    codigo_spdata_centro_custo = db.Column(db.Integer, nullable=True, index=True)
    codigo_spdata_agenda = db.Column(db.String(50), nullable=True, index=True)
    endereco = db.Column(db.String(500), nullable=True)
    telefone = db.Column(db.String(50), nullable=True)
    ativa = db.Column(db.Boolean, nullable=False, default=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    usuarios = db.relationship(
        "UsuarioUnidade",
        back_populates="unidade",
        cascade="all, delete-orphan",
    )

    def _to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "slug": self.slug,
            "codigo_spdata_centro_custo": self.codigo_spdata_centro_custo,
            "codigo_spdata_agenda": self.codigo_spdata_agenda,
            "endereco": self.endereco,
            "telefone": self.telefone,
            "ativa": self.ativa,
        }

    def _to_frontend_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "slug": self.slug,
            "codigoSpdataCentroCusto": self.codigo_spdata_centro_custo,
            "codigoSpdataAgenda": self.codigo_spdata_agenda,
            "endereco": self.endereco or "",
            "telefone": self.telefone or "",
        }
