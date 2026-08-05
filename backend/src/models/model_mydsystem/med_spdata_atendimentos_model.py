from datetime import datetime

from src.settings.extensions import db


class MedSpdataAtendimento(db.Model):
    __tablename__ = "MED_SPDATA_ATENDIMENTOS"

    id = db.Column(db.Integer, primary_key=True)

    spdata_atendimento_id = db.Column(db.Integer, nullable=False, unique=True, index=True)
    cod_atendimento = db.Column(db.String(50), nullable=True, index=True)
    id_paciente_spdata = db.Column(db.Integer, nullable=True, index=True)
    id_medico_spdata = db.Column(db.Integer, nullable=True, index=True)

    medico = db.Column(db.String(255), nullable=True)
    crm_medico = db.Column(db.String(50), nullable=True, index=True)

    data_hora_entrada = db.Column(db.DateTime, nullable=False, index=True)
    data_atendimento = db.Column(db.Date, nullable=False, index=True)
    hora_entrada = db.Column(db.Time, nullable=True)
    data_hora_alta_medica = db.Column(db.DateTime, nullable=True)

    id_convenio_spdata = db.Column(db.Integer, nullable=True, index=True)
    id_centro_custo_spdata = db.Column(db.Integer, nullable=True, index=True)
    obs_atendimento = db.Column(db.Text, nullable=True)

    paciente = db.Column(db.String(255), nullable=False, index=True)
    paciente_nome_social = db.Column(db.String(255), nullable=True)
    cpf = db.Column(db.String(20), nullable=True, index=True)
    prontuario = db.Column(db.String(50), nullable=True, index=True)
    data_nascimento = db.Column(db.Date, nullable=True)
    sexo = db.Column(db.String(20), nullable=True)
    celular = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    endereco = db.Column(db.String(500), nullable=True)

    dados_spdata = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    atendimento_medsystem = db.relationship(
        "MedAtendimentos",
        back_populates="spdata_atendimento",
        uselist=False,
    )

    def _to_dict(self):
        return {
            "id": self.id,
            "spdata_atendimento_id": self.spdata_atendimento_id,
            "cod_atendimento": self.cod_atendimento,
            "id_paciente_spdata": self.id_paciente_spdata,
            "id_medico_spdata": self.id_medico_spdata,
            "medico": self.medico,
            "crm_medico": self.crm_medico,
            "data_hora_entrada": self.data_hora_entrada.isoformat() if self.data_hora_entrada else None,
            "data_atendimento": self.data_atendimento.isoformat() if self.data_atendimento else None,
            "hora_entrada": str(self.hora_entrada) if self.hora_entrada else None,
            "data_hora_alta_medica": self.data_hora_alta_medica.isoformat() if self.data_hora_alta_medica else None,
            "id_convenio_spdata": self.id_convenio_spdata,
            "id_centro_custo_spdata": self.id_centro_custo_spdata,
            "obs_atendimento": self.obs_atendimento,
            "paciente": self.paciente,
            "paciente_nome_social": self.paciente_nome_social,
            "cpf": self.cpf,
            "prontuario": self.prontuario,
            "data_nascimento": self.data_nascimento.isoformat() if self.data_nascimento else None,
            "sexo": self.sexo,
            "celular": self.celular,
            "email": self.email,
            "endereco": self.endereco,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
