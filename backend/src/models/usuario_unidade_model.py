from datetime import datetime

from src.settings.extensions import db


class UsuarioUnidade(db.Model):
    __tablename__ = "usuario_unidades"
    __table_args__ = (
        db.UniqueConstraint("usuario_id", "unidade_id", name="uq_usuario_unidades_usuario_unidade"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    unidade_id = db.Column(
        db.Integer,
        db.ForeignKey("unidades.id"),
        nullable=False,
        index=True,
    )
    principal = db.Column(db.Boolean, nullable=False, default=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    usuario = db.relationship("Usuario", back_populates="unidades")
    unidade = db.relationship("Unidade", back_populates="usuarios")

    def _to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "unidade_id": self.unidade_id,
            "principal": self.principal,
            "ativo": self.ativo,
        }
