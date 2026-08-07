from datetime import datetime

from src.settings.extensions import db


class MedSpdataAgenda(db.Model):
    __tablename__ = "MED_SPDATA_AGENDA"

    id = db.Column(db.Integer, primary_key=True)

    spdata_agenda_id = db.Column(db.Integer, nullable=False, unique=True, index=True)
    unidade_id = db.Column(db.Integer, nullable=True, index=True)
    codigo_unidade_spdata = db.Column(db.String(50), nullable=True, index=True)
    id_paciente_spdata = db.Column(db.Integer, nullable=True, index=True)

    registro = db.Column(db.String(50), nullable=True, index=True)
    grv_ate = db.Column(db.Integer, nullable=True)
    crm = db.Column(db.String(50), nullable=True, index=True)
    crm_atend = db.Column(db.String(50), nullable=True)
    medico = db.Column(db.String(255), nullable=True)

    data_agenda = db.Column(db.Date, nullable=False, index=True)
    hora_agenda = db.Column(db.Time, nullable=True)

    paciente = db.Column(db.String(255), nullable=False, index=True)
    paciente_nome_social = db.Column(db.String(255), nullable=True)
    cpf = db.Column(db.String(20), nullable=True, index=True)
    prontuario = db.Column(db.String(50), nullable=True, index=True)

    id_convenio_spdata = db.Column(db.Integer, nullable=True, index=True)
    convenio = db.Column(db.String(100), nullable=True)
    especialidade = db.Column(db.String(120), nullable=True)
    atendido_spdata = db.Column(db.String(1), nullable=True, index=True)

    data_nascimento = db.Column(db.Date, nullable=True)
    telefone = db.Column(db.String(30), nullable=True)
    celular = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    obs = db.Column(db.Text, nullable=True)
    motivo_no_show = db.Column(db.String(30), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __init__(
        self,
        spdata_agenda_id,
        paciente,
        data_agenda,
        unidade_id=None,
        codigo_unidade_spdata=None,
        id_paciente_spdata=None,
        registro=None,
        grv_ate=None,
        crm=None,
        crm_atend=None,
        medico=None,
        hora_agenda=None,
        paciente_nome_social=None,
        cpf=None,
        prontuario=None,
        id_convenio_spdata=None,
        convenio=None,
        especialidade=None,
        atendido_spdata=None,
        data_nascimento=None,
        telefone=None,
        celular=None,
        email=None,
        obs=None,
        motivo_no_show=None
    ):
        self.spdata_agenda_id = spdata_agenda_id
        self.unidade_id = unidade_id
        self.codigo_unidade_spdata = codigo_unidade_spdata
        self.id_paciente_spdata = id_paciente_spdata
        self.registro = registro
        self.grv_ate = grv_ate
        self.crm = crm
        self.crm_atend = crm_atend
        self.medico = medico
        self.data_agenda = data_agenda
        self.hora_agenda = hora_agenda
        self.paciente = paciente
        self.paciente_nome_social = paciente_nome_social
        self.cpf = cpf
        self.prontuario = prontuario
        self.id_convenio_spdata = id_convenio_spdata
        self.convenio = convenio
        self.especialidade = especialidade
        self.atendido_spdata = atendido_spdata
        self.data_nascimento = data_nascimento
        self.telefone = telefone
        self.celular = celular
        self.email = email
        self.obs = obs
        self.motivo_no_show = motivo_no_show

    def _to_dict(self):
        return {
            "id": self.id,
            "spdata_agenda_id": self.spdata_agenda_id,
            "unidade_id": self.unidade_id,
            "codigo_unidade_spdata": self.codigo_unidade_spdata,
            "id_paciente_spdata": self.id_paciente_spdata,
            "registro": self.registro,
            "grv_ate": self.grv_ate,
            "crm": self.crm,
            "crm_atend": self.crm_atend,
            "medico": self.medico,
            "data_agenda": self.data_agenda.isoformat() if self.data_agenda else None,
            "hora_agenda": str(self.hora_agenda) if self.hora_agenda else None,
            "paciente": self.paciente,
            "paciente_nome_social": self.paciente_nome_social,
            "cpf": self.cpf,
            "prontuario": self.prontuario,
            "id_convenio_spdata": self.id_convenio_spdata,
            "convenio": self.convenio,
            "especialidade": self.especialidade,
            "atendido_spdata": self.atendido_spdata,
            "data_nascimento": self.data_nascimento.isoformat() if self.data_nascimento else None,
            "telefone": self.telefone,
            "celular": self.celular,
            "email": self.email,
            "obs": self.obs,
            "motivo_no_show": self.motivo_no_show,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
