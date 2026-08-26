from datetime import datetime
from enum import Enum

from src.settings.extensions import db

"""  
    Registra ações importantes do sistema.
"""

class AcaoAuditoria(Enum):
    LOGIN_SUCESSO = "LOGIN_SUCESSO"
    LOGIN_FALHA = "LOGIN_FALHA"
    LOGOUT = "LOGOUT"
    ACESSO_NEGADO = "ACESSO_NEGADO"
    VISUALIZOU_PRONTUARIO = "VISUALIZOU_PRONTUARIO"
    VISUALIZOU_HISTORICO_BIODATA = "VISUALIZOU_HISTORICO_BIODATA"
    VISUALIZOU_HISTORICO_SPDATA = "VISUALIZOU_HISTORICO_SPDATA"
    VISUALIZOU_AGENDA = "VISUALIZOU_AGENDA"
    VISUALIZOU_CHECK_IN = "VISUALIZOU_CHECK_IN"
    VISUALIZOU_NO_SHOW = "VISUALIZOU_NO_SHOW"
    VISUALIZOU_RETENCAO_EXAMES = "VISUALIZOU_RETENCAO_EXAMES"
    VISUALIZOU_DOCUMENTOS_MEDICOS = "VISUALIZOU_DOCUMENTOS_MEDICOS"
    SALVOU_DOCUMENTO_MEDICO = "SALVOU_DOCUMENTO_MEDICO"
    ALTEROU_STATUS_AGENDA = "ALTEROU_STATUS_AGENDA"
    ALTEROU_MOTIVO_NO_SHOW = "ALTEROU_MOTIVO_NO_SHOW"
    INICIOU_ATENDIMENTO = "INICIOU_ATENDIMENTO"
    EDITOU_EVOLUCAO = "EDITOU_EVOLUCAO"
    FINALIZOU_ATENDIMENTO = "FINALIZOU_ATENDIMENTO"
    CRIOU_MODELO_MEDICO = "CRIOU_MODELO_MEDICO"
    EDITOU_MODELO_MEDICO = "EDITOU_MODELO_MEDICO"
    EXCLUIU_MODELO_MEDICO = "EXCLUIU_MODELO_MEDICO"
    TTS_SOLICITADO = "TTS_SOLICITADO"
    GEROU_RECEITA = "GEROU_RECEITA"
    GEROU_ATESTADO = "GEROU_ATESTADO"
    EXPORTOU_DADOS = "EXPORTOU_DADOS"
    SINCRONIZOU_SPDATA = "SINCRONIZOU_SPData"
    RETENCAO_DESCARTE_EXECUTADA = "RETENCAO_DESCARTE_EXECUTADA"


class Auditoria(db.Model):
    __tablename__ = "auditorias"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    medico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    acao = db.Column(
        db.String(100),
        nullable=False
    )

    entidade = db.Column(
        db.String(100),
        nullable=True
    )

    entidade_id = db.Column(
        db.Integer,
        nullable=True
    )

    descricao = db.Column(
        db.Text,
        nullable=True
    )

    ip = db.Column(
        db.String(100),
        nullable=True
    )

    user_agent = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    usuario = db.relationship(
        "Usuario",
        foreign_keys=[usuario_id],
        back_populates="auditorias"
    )

    medico = db.relationship(
        "Usuario",
        foreign_keys=[medico_id],
        back_populates="auditorias_medicas"
    )

    def __repr__(self):
        acao = self.acao.value if hasattr(self.acao, "value") else self.acao
        return (
            f"<Auditoria acao={acao} "
            f"entidade={self.entidade} "
            f"entidade_id={self.entidade_id}>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "medico_id": self.medico_id,
            "acao": self.acao.value if hasattr(self.acao, "value") else self.acao,
            "entidade": self.entidade,
            "entidade_id": self.entidade_id,
            "descricao": self.descricao,
            "ip": self.ip,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "usuario": {
                "id": self.usuario.id,
                "nome_completo": self.usuario.nome_completo,
                "email": self.usuario.email,
                "role": self.usuario.role,
            } if self.usuario else None,
        }
