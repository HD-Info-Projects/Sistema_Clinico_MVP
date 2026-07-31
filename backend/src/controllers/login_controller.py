from flask_jwt_extended import create_access_token

from src.models.repositories.usuario_repository import UsuarioRepository
from src.security.passwords import verify_password
from src.settings.extensions import db

class LoginController:
    
    def __init__(self):
        self.__repo = UsuarioRepository()
    
    def generate_JWT_usuario(self, email:str, senha: str):
        usuario = self.__repo.get_usuario(email)
        
        if not usuario:
            return None

        senha_valida, senha_legada = verify_password(usuario.senha, senha)

        if not senha_valida:
            return None

        if senha_legada:
            usuario.set_senha(senha)
            db.session.commit()

        token = create_access_token(
            identity=str(usuario.id),
            additional_claims={
                "id": usuario.id,
                "email": usuario.email,
                "nome_completo": usuario.nome_completo,
                "role": usuario.role,
                "crm": usuario.medico.crm_atendimento_spdata if usuario.medico else None,
                "especialidade": usuario.medico.especialidade if usuario.medico else None
            }
        )
        return token
        
        
