from sqlalchemy import Boolean, Column, String, Integer, DateTime
from datetime import UTC, datetime

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
    ativo = Column(Boolean, nullable=False, default=True)
    bloqueado_em = Column(DateTime, nullable=True)
    bloqueio_motivo = Column(String(255), nullable=True)
    tentativas_login_falhas = Column(Integer, nullable=False, default=0)
    ultimo_login_falho_em = Column(DateTime, nullable=True)
    ultimo_login_em = Column(DateTime, nullable=True)
    senha_alterada_em = Column(DateTime, nullable=True)
    forcar_troca_senha = Column(Boolean, nullable=False, default=False)
    
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

    unidades = db.relationship(
        "UsuarioUnidade",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )
    
    
    def __init__(self, nome_completo, cnpj_cpf, email, senha, role="medico", ativo=True):
        self.nome_completo = nome_completo
        self.cnpj_cpf = cnpj_cpf
        self.email = email
        self.set_senha(senha)
        self.role = role
        self.ativo = ativo

    def _agora_utc(self):
        return datetime.now(UTC).replace(tzinfo=None)

    def set_senha(self, senha):
        self.senha = hash_password(senha)
        self.senha_alterada_em = self._agora_utc()
        self.forcar_troca_senha = False
        self.tentativas_login_falhas = 0
        self.ultimo_login_falho_em = None

    def registrar_login_falho(self, max_tentativas=5):
        agora = self._agora_utc()
        tentativas = int(self.tentativas_login_falhas or 0) + 1

        self.tentativas_login_falhas = tentativas
        self.ultimo_login_falho_em = agora

        if max_tentativas and tentativas >= max_tentativas:
            self.bloqueado_em = agora
            self.bloqueio_motivo = "Excesso de tentativas de login falhas"

    def registrar_login_sucesso(self):
        self.ultimo_login_em = self._agora_utc()
        self.tentativas_login_falhas = 0
        self.ultimo_login_falho_em = None

    def desbloquear(self, motivo=None):
        self.bloqueado_em = None
        self.bloqueio_motivo = None
        self.tentativas_login_falhas = 0
        self.ultimo_login_falho_em = None


    def __repr__(self):
        return f"Usuario: {self.email}"
    
    def _to_dict(self):
        return {
            "id": self.id,
            "nome_completo": self.nome_completo,
            "cnpj_cpf": self.cnpj_cpf,
            "email": self.email,
            "role": self.role,
            "ativo": self.ativo,
            "bloqueado": self.bloqueado_em is not None,
        }

    def _to_dict_(self):
        return self._to_dict()
