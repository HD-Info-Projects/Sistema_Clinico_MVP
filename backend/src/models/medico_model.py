from datetime import datetime

from src.settings.extensions import db

class Medico(db.Model):
    __tablename__ = "medicos"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        unique=True,
        index=True
    )

    spdata_id = db.Column(db.Integer, nullable=True, unique=True, index=True)

    crm = db.Column(db.String(20), nullable=True)
    crm_atendimento_spdata = db.Column(db.String(50), nullable=True, index=True)
    crm_uf = db.Column(db.String(2), nullable=True)
    rqe = db.Column(db.String(30), nullable=True)
    especialidade = db.Column(db.String(255), nullable=True)

    ativo = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="medico"
    )
    
    def __init__(self, usuario_id, spdata_id, crm=None, crm_atendimento_spdata=None, crm_uf=None, rqe=None, especialidade=None, ativo=True):
        self.usuario_id = usuario_id
        self.spdata_id = spdata_id
        self.crm = crm
        self.crm_atendimento_spdata = crm_atendimento_spdata
        self.crm_uf = crm_uf
        self.rqe = rqe
        self.especialidade = especialidade
        self.ativo = ativo
        
    def _to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "spdata_id": self.spdata_id,
            "crm": self.crm,
            "crm_atendimento_spdata": self.crm_atendimento_spdata,
            "crm_uf": self.crm_uf,
            "rqe": self.rqe,
            "especialidade": self.especialidade,
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
