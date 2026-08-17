from datetime import UTC, datetime

from flask import current_app, has_app_context
from flask_jwt_extended import create_access_token

from src.models.repositories.usuario_repository import UsuarioRepository
from src.security.passwords import verify_password
from src.settings.extensions import db
from src.services.unidades_service import listar_unidades_usuario_frontend

class LoginController:
    
    def __init__(self):
        self.__repo = UsuarioRepository()

    def _agora_utc(self):
        return datetime.now(UTC).replace(tzinfo=None)

    def _max_tentativas_login(self):
        if not has_app_context():
            return 5

        if not current_app.config.get("LOGIN_ACCOUNT_LOCK_ENABLED", True):
            return 0

        return int(current_app.config.get("LOGIN_MAX_FAILED_ATTEMPTS", 5))

    def _registrar_login_falho(self, usuario):
        if hasattr(usuario, "registrar_login_falho"):
            usuario.registrar_login_falho(self._max_tentativas_login())
        else:
            agora = self._agora_utc()
            tentativas = int(getattr(usuario, "tentativas_login_falhas", 0) or 0) + 1
            usuario.tentativas_login_falhas = tentativas
            usuario.ultimo_login_falho_em = agora
            max_tentativas = self._max_tentativas_login()
            if max_tentativas and tentativas >= max_tentativas:
                usuario.bloqueado_em = agora
                usuario.bloqueio_motivo = "Excesso de tentativas de login falhas"

        db.session.commit()

    def _registrar_login_sucesso(self, usuario):
        if hasattr(usuario, "registrar_login_sucesso"):
            usuario.registrar_login_sucesso()
        else:
            usuario.ultimo_login_em = self._agora_utc()
            usuario.tentativas_login_falhas = 0
            usuario.ultimo_login_falho_em = None

        db.session.commit()
    
    def generate_JWT_usuario(self, email:str, senha: str):
        email = (email or "").strip().lower()
        usuario = self.__repo.get_usuario(email)
        
        if not usuario:
            return None

        if not getattr(usuario, "ativo", True) or getattr(usuario, "bloqueado_em", None):
            return None

        senha_valida, senha_legada = verify_password(usuario.senha, senha)

        if not senha_valida:
            self._registrar_login_falho(usuario)
            return None

        if senha_legada:
            usuario.set_senha(senha)

        self._registrar_login_sucesso(usuario)

        unidades = (
            listar_unidades_usuario_frontend(usuario.id)
            if getattr(usuario, "unidades", [])
            else []
        )
        token = create_access_token(
            identity=str(usuario.id),
            additional_claims={
                "id": usuario.id,
                "email": usuario.email,
                "nome_completo": usuario.nome_completo,
                "role": usuario.role,
                "crm": usuario.medico.crm_atendimento_spdata if usuario.medico else None,
                "especialidade": usuario.medico.especialidade if usuario.medico else None,
                "unidade_ids": [
                    unidade["id"]
                    for unidade in unidades
                ],
            }
        )
        return token
        
        
