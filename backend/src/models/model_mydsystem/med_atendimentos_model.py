from datetime import datetime
from enum import Enum

from src.settings.extensions import db


class StatusAtendimentoMedSystem(Enum):
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    ATENDIDO = "ATENDIDO"
    FALTOU = "FALTOU"


class MedAtendimentos(db.Model):
    __tablename__ = "MED_ATENDIMENTOS"

    id = db.Column(db.Integer, primary_key=True)

    med_spdata_atendimento_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "MED_SPDATA_ATENDIMENTOS.id",
            name="fk_med_atendimentos_med_spdata_atendimento_id"
        ),
        nullable=False,
        unique=True,
        index=True
    )

    spdata_atendimento_id = db.Column(db.Integer, nullable=False, index=True)
    unidade_id = db.Column(db.Integer, nullable=True, index=True)
    cod_atendimento = db.Column(db.String(50), nullable=True, index=True)

    id_medico_spdata = db.Column(db.Integer, nullable=True, index=True)
    medico = db.Column(db.String(255), nullable=True)

    data_agenda = db.Column(db.Date, nullable=False, index=True)
    hora_agenda = db.Column(db.Time, nullable=True)

    id_paciente_spdata = db.Column(db.Integer, nullable=True, index=True)
    paciente = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(20), nullable=True, index=True)
    prontuario = db.Column(db.String(50), nullable=True, index=True)

    status = db.Column(
        db.String(50),
        nullable=False,
        default=StatusAtendimentoMedSystem.EM_ATENDIMENTO.value,
        index=True
    )

    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    faltou_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    spdata_atendimento = db.relationship(
        "MedSpdataAtendimento",
        back_populates="atendimento_medsystem"
    )

    def __init__(
        self,
        med_spdata_atendimento_id,
        spdata_atendimento_id,
        data_agenda,
        paciente,
        status=StatusAtendimentoMedSystem.EM_ATENDIMENTO,
        unidade_id=None,
        cod_atendimento=None,
        id_medico_spdata=None,
        medico=None,
        hora_agenda=None,
        id_paciente_spdata=None,
        cpf=None,
        prontuario=None,
        started_at=None,
        finished_at=None,
        faltou_at=None
    ):
        self.med_spdata_atendimento_id = med_spdata_atendimento_id
        self.spdata_atendimento_id = spdata_atendimento_id
        self.unidade_id = unidade_id
        self.cod_atendimento = cod_atendimento
        self.id_medico_spdata = id_medico_spdata
        self.medico = medico
        self.data_agenda = data_agenda
        self.hora_agenda = hora_agenda
        self.id_paciente_spdata = id_paciente_spdata
        self.paciente = paciente
        self.cpf = cpf
        self.prontuario = prontuario
        self.status = status.value if hasattr(status, "value") else status
        self.started_at = started_at or datetime.utcnow()
        self.finished_at = finished_at
        self.faltou_at = faltou_at

    def marcar_em_atendimento(self):
        self.status = StatusAtendimentoMedSystem.EM_ATENDIMENTO.value
        self.started_at = self.started_at or datetime.utcnow()
        self.finished_at = None
        self.faltou_at = None

    def marcar_atendido(self):
        self.status = StatusAtendimentoMedSystem.ATENDIDO.value
        self.finished_at = datetime.utcnow()

    def marcar_faltou(self):
        self.status = StatusAtendimentoMedSystem.FALTOU.value
        self.faltou_at = datetime.utcnow()

    def _to_dict(self):
        status = self.status.value if hasattr(self.status, "value") else self.status

        return {
            "id": self.id,
            "med_spdata_atendimento_id": self.med_spdata_atendimento_id,
            "spdata_atendimento_id": self.spdata_atendimento_id,
            "unidade_id": self.unidade_id,
            "cod_atendimento": self.cod_atendimento,
            "id_medico_spdata": self.id_medico_spdata,
            "medico": self.medico,
            "data_agenda": self.data_agenda.isoformat() if self.data_agenda else None,
            "hora_agenda": str(self.hora_agenda) if self.hora_agenda else None,
            "id_paciente_spdata": self.id_paciente_spdata,
            "paciente": self.paciente,
            "cpf": self.cpf,
            "prontuario": self.prontuario,
            "status": status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "faltou_at": self.faltou_at.isoformat() if self.faltou_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
