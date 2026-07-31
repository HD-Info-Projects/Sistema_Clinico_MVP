from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime

from src.security.passwords import hash_password
from src.settings.extensions import db

class Usuario(db.Model):
    
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nome_completo = Column(String(255), nullable=False)
    cnpj_cpf = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    senha = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="medico")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relações
    evolucoes_medicas = db.relationship(
        "EvolucaoMedica",
        back_populates="medico"
    )


    alteracoes_evolucoes = db.relationship(
        "EvolucaoMedicaVersao",
        back_populates="usuario_alteracao"
    )

    prescricoes = db.relationship(
        "Prescricao",
        back_populates="medico"
    )

    auditorias = db.relationship(
        "Auditoria",
        foreign_keys="Auditoria.usuario_id",
        back_populates="usuario"
    )

    auditorias_medicas = db.relationship(
        "Auditoria",
        foreign_keys="Auditoria.medico_id",
        back_populates="medico"
    )
    
    
    ## Tipos de usuários:
    medico = db.relationship(
        "Medico",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    
    def __init__(self, nome_completo, cnpj_cpf, email, senha, role="medico"):
        self.nome_completo = nome_completo
        self.cnpj_cpf = cnpj_cpf
        self.email = email
        self.set_senha(senha)
        self.role = role

    def set_senha(self, senha):
        self.senha = hash_password(senha)


    def __repr__(self):
        return f"Usuario: {self.email}"
    
    def _to_dict(self):
        return {
            "id": self.id,
            "nome_completo": self.nome_completo,
            "cnpj_cpf": self.cnpj_cpf,
            "email": self.email,
            "role": self.role,
        }

    def _to_dict_(self):
        return self._to_dict()
