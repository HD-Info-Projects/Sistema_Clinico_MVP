from datetime import datetime
from enum import Enum as ModelEnum

from sqlalchemy import Column, String, Integer, DateTime, Time

from src.settings.extensions import db

"""
    Responsável por armazenar cada atendimento realizado pelo médico.
"""

class StatusAtendimento(ModelEnum):
    AGENDADO = "agendado"
    EM_ATENDIMENTO = "em-atendimento"
    FINALIZADO = "finalizado"
    CANCELADO = "cancelado"


class SyncStatusAtendimento(ModelEnum):
    PENDENTE_SINCRONIZACAO = "pendente_sincronizacao"
    SINCRONIZADO = "sincronizado"
    ERRO_SINCRONIZACAO = "erro_sincronizacao"
    
    
class Atendimento(db.Model):
    
    __tablename__ = "atendimentos"
    
    id = Column(Integer, primary_key=True)
    
    # As FKs
    spdata_atendimento_id = Column(Integer, nullable=True, index=True)
    spdata_paciente_id = Column(Integer, nullable=True)
    spdata_agenda_id = Column(Integer, nullable=True, index=True)
    spdata_medico_id = Column(Integer, nullable=True)
    unidade_id = Column(Integer, nullable=True, index=True)
    
    # Colunas da tabela
    paciente_nome = Column(String(255), nullable=False)
    paciente_cpf = Column(String(20), nullable=False)
    
    data_atendimento = Column(DateTime, nullable=False) # <- recebe uma data
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=True)
    
    status = Column(String(50), default=StatusAtendimento.AGENDADO.value)
    sync_status = Column(String(50), default=SyncStatusAtendimento.PENDENTE_SINCRONIZACAO.value)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos:
    evolucoes_medicas = db.relationship(
        "EvolucaoMedica",
        back_populates="atendimento",
        cascade="all, delete-orphan",
        order_by="EvolucaoMedica.versao.desc()"
    )
    
    diagnosticos = db.relationship(
        "Diagnostico",
        back_populates="atendimento",
        cascade="all, delete-orphan",
        order_by="Diagnostico.created_at.desc()"
    )
    
    prescricoes = db.relationship(
        "Prescricao",
        back_populates="atendimento",
        cascade="all, delete-orphan",
        order_by="Prescricao.created_at.desc()"
    )
    
    solicitacoes_exames = db.relationship(
        "SolicitacaoExame",
        back_populates="atendimento",
        cascade="all, delete-orphan",
        order_by="SolicitacaoExame.created_at.desc()"
    )
    
    documentos_medicos = db.relationship(
        "DocumentoMedico",
        back_populates="atendimento",
        cascade="all, delete-orphan",
        order_by="DocumentoMedico.created_at.desc()"
    )
    
    anamnese = db.relationship(
        "Anamnese",
        back_populates="atendimento",
        cascade="all, delete-orphan",
        uselist=False
    )
        
    def __init__(
        self,
        spdata_paciente_id,
        spdata_agenda_id,
        spdata_medico_id,
        paciente_nome,
        paciente_cpf,
        data_atendimento,
        hora_inicio,
        hora_fim,
        spdata_atendimento_id=None,
        unidade_id=None,
    ):
        self.spdata_atendimento_id = spdata_atendimento_id
        self.unidade_id = unidade_id
        self.spdata_paciente_id = spdata_paciente_id
        self.spdata_agenda_id = spdata_agenda_id
        self.spdata_medico_id = spdata_medico_id
        self.paciente_nome = paciente_nome
        self.paciente_cpf = paciente_cpf
        self.data_atendimento = data_atendimento
        self.hora_inicio = hora_inicio
        self.hora_fim = hora_fim
        
    def __repr__(self):
        return f"<Atendimento id={self.id} paciente={self.paciente_nome}>"

    def to_dict(self):
        return {
            "id": self.id,
            "spdata_atendimento_id": self.spdata_atendimento_id,
            "unidade_id": self.unidade_id,
            "spdata_paciente_id": self.spdata_paciente_id,
            "spdata_agenda_id": self.spdata_agenda_id,
            "spdata_medico_id": self.spdata_medico_id,
            "paciente_nome": self.paciente_nome,
            "paciente_cpf": self.paciente_cpf,
            "data_atendimento": self.data_atendimento.isoformat() if self.data_atendimento else None,
            "hora_inicio": str(self.hora_inicio) if self.hora_inicio else None,
            "hora_fim": str(self.hora_fim) if self.hora_fim else None,
            "status": self.status.value if hasattr(self.status, "value") else self.status,
            "sync_status": self.sync_status.value if hasattr(self.sync_status, "value") else self.sync_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
