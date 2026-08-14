from datetime import datetime

from src.settings.extensions import db

""" 
    Registra tudo que foi enviado ou recebido do SPDATA.
"""

class LogIntegracao(db.Model):
    __tablename__ = "logs_integracao"

    id = db.Column(db.Integer, primary_key=True)

    acao = db.Column(
        db.String(100),
        nullable=False
    )

    metodo = db.Column(
        db.String(20),
        nullable=True
    )

    endpoint = db.Column(
        db.String(500),
        nullable=True
    )

    payload_enviado = db.Column(
        db.JSON,
        nullable=True
    )

    resposta_recebida = db.Column(
        db.JSON,
        nullable=True
    )

    status_code = db.Column(
        db.Integer,
        nullable=True
    )

    sucesso = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    erro = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    def __repr__(self):
        return (
            f"<LogIntegracao acao={self.acao} "
            f"metodo={self.metodo} "
            f"status_code={self.status_code} "
            f"sucesso={self.sucesso}>"
        )
