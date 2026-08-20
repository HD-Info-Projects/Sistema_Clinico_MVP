from sqlalchemy.orm import joinedload, selectinload

from src.models.interfaces.usuario_interface import IUsuario

from src.settings.extensions import db
from src.models.usuario_model import Usuario

class UsuarioRepository(IUsuario):
    
    def get_usuario(self, email: str):
        try:    
            usuario = (
                db.session.query(Usuario)
                .options(
                    joinedload(Usuario.medico),
                    selectinload(Usuario.unidades),
                )
                .filter(Usuario.email == email)
                .first()
            )
            return usuario
        
        except Exception:
            db.session.rollback()
            return None
