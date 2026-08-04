from flask_jwt_extended import create_access_token

from src.models.repositories.usuario_repository import UsuarioRepository
from src.services.unidades_service import listar_unidades_usuario_frontend

class LoginController:
    
    def __init__(self):
        self.__repo = UsuarioRepository()
    
    def generate_JWT_usuario(self, email:str, senha: str):
        usuario = self.__repo.get_usuario(email)
        
        if not usuario:
            return None

        if usuario.senha != senha:
            return None

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
                    for unidade in listar_unidades_usuario_frontend(usuario.id)
                ],
            }
        )
        return token
        
        
