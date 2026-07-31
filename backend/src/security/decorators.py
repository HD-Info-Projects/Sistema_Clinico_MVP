from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from src.models.auditoria_model import AcaoAuditoria
from src.services.auditoria_service import registrar_auditoria


def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()

            claims = get_jwt()
            role = claims.get("role")

            if role not in roles:
                registrar_auditoria(
                    AcaoAuditoria.ACESSO_NEGADO,
                    entidade="rota",
                    descricao=f"Perfil {role or 'sem_perfil'} tentou acessar rota restrita a {', '.join(roles)}",
                )
                return jsonify({"error": "Acesso negado"}), 403

            return fn(*args, **kwargs)

        return decorator

    return wrapper
