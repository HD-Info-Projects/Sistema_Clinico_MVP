from datetime import datetime
from enum import Enum

from src.settings.extensions import db

""" 
    Muito importante para integração com o SPDATA.
"""

class StatusSincronizacao(Enum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    SINCRONIZADO = "SINCRONIZADO"
    ERRO = "ERRO"
    CANCELADO = "CANCELADO"


class TipoEventoSincronizacao(Enum):
    ATENDIMENTO_FINALIZADO = "ATENDIMENTO_FINALIZADO"
    EVOLUCAO_CRIADA = "EVOLUCAO_CRIADA"
    PRESCRICAO_CRIADA = "PRESCRICAO_CRIADA"
    EXAME_SOLICITADO = "EXAME_SOLICITADO"
    ATESTADO_GERADO = "ATESTADO_GERADO"


class FilaSincronizacao(db.Model):
    __tablename__ = "fila_sincronizacao"
    __table_args__ = (
        db.Index("ix_fila_sincronizacao_status_updated_id", "status", "updated_at", "id"),
    )

    id = db.Column(db.Integer, primary_key=True)

    tipo_evento = db.Column(
        db.Enum(TipoEventoSincronizacao),
        nullable=False
    )

    referencia_id = db.Column(
        db.Integer,
        nullable=False
    )

    payload = db.Column(
        db.JSON,
        nullable=False
    )

    status = db.Column(
        db.Enum(StatusSincronizacao),
        nullable=False,
        default=StatusSincronizacao.PENDENTE
    )

    tentativas = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    erro = db.Column(
        db.Text,
        nullable=True
    )

    ultima_tentativa = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<FilaSincronizacao tipo_evento={self.tipo_evento.value} "
            f"referencia_id={self.referencia_id} "
            f"status={self.status.value}>"
        )
