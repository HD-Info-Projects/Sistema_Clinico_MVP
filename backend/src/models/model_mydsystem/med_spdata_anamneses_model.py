from datetime import datetime

from src.settings.extensions import db


class MedSpdataAnamnese(db.Model):
    """Espelho local das anamneses (evoluções modelo MED26) do SPDATA/Firebird.

    Uma linha por evolução (PRCABEVOL). Alimentada manualmente pelo comando
    `flask importar-anamneses-spdata`.
    """

    __tablename__ = "MED_SPDATA_ANAMNESES"

    id = db.Column(db.Integer, primary_key=True)
    id_cabevol = db.Column(db.BigInteger, nullable=False, unique=True, index=True)
    id_htatendimento = db.Column(db.BigInteger, nullable=True, index=True)
    id_evolucao = db.Column(db.BigInteger, nullable=True)
    modelo_cod = db.Column(db.String(20), nullable=True)
    modelo_descricao = db.Column(db.String(255), nullable=True)

    id_paciente_spdata = db.Column(db.BigInteger, nullable=True, index=True)
    prontuario = db.Column(db.String(50), nullable=True, index=True)
    paciente = db.Column(db.String(255), nullable=True)

    data_hora_evolucao = db.Column(db.DateTime, nullable=True, index=True)
    anamnese = db.Column(db.Text, nullable=True)
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
            "id_cabevol": self.id_cabevol,
            "id_htatendimento": self.id_htatendimento,
            "id_evolucao": self.id_evolucao,
            "modelo_cod": self.modelo_cod,
            "modelo_descricao": self.modelo_descricao,
            "id_paciente_spdata": self.id_paciente_spdata,
            "prontuario": self.prontuario,
            "paciente": self.paciente,
            "data_hora_evolucao": self.data_hora_evolucao.isoformat() if self.data_hora_evolucao else None,
            "anamnese": self.anamnese,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
