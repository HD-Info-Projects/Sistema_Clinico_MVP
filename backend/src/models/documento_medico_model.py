from datetime import datetime

from src.settings.extensions import db

TIPO_ATESTADO = "ATESTADO"
TIPO_ENCAMINHAMENTO = "ENCAMINHAMENTO"
TIPO_SOLICITACAO_PROCEDIMENTO = "SOLICITACAO_PROCEDIMENTO"
TIPO_SOLICITACAO_OPME = "SOLICITACAO_OPME"

TIPOS_DOCUMENTO_VALIDOS = {
    TIPO_ATESTADO,
    TIPO_ENCAMINHAMENTO,
    TIPO_SOLICITACAO_PROCEDIMENTO,
    TIPO_SOLICITACAO_OPME,
}


class DocumentoMedico(db.Model):
    __tablename__ = "documentos_medicos"
    __table_args__ = (
        db.UniqueConstraint(
            "atendimento_id",
            "tipo_documento",
            name="uq_documentos_medicos_atendimento_tipo",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    atendimento_id = db.Column(
        db.Integer,
        db.ForeignKey("atendimentos.id"),
        nullable=False
    )

    tipo_documento = db.Column(
        db.String(50),
        nullable=False
    )

    dados = db.Column(
        db.JSON,
        nullable=False
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

    atendimento = db.relationship(
        "Atendimento",
        back_populates="documentos_medicos"
    )

    def __repr__(self):
        return (
            f"<DocumentoMedico atendimento_id={self.atendimento_id} "
            f"tipo_documento={self.tipo_documento}>"
        )
