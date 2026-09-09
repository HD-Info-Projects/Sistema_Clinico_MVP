from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from src.models.auditoria_model import AcaoAuditoria
from src.services.auditoria_service import registrar_auditoria


def _usuario_autenticado_ativo():
    try:
        usuario_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None

    from src.models.usuario_model import Usuario
    from src.settings.extensions import db

    usuario = db.session.get(Usuario, usuario_id)
    if not usuario or not getattr(usuario, "ativo", True) or getattr(usuario, "bloqueado_em", None):
        return None

    return usuario


def _registrar_acesso_negado_usuario_inativo():
    registrar_auditoria(
        AcaoAuditoria.ACESSO_NEGADO,
        entidade="rota",
        descricao="Usuário inativo, bloqueado ou inexistente tentou acessar rota autenticada",
    )


def active_user_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()

            if not _usuario_autenticado_ativo():
                _registrar_acesso_negado_usuario_inativo()
                return jsonify({"error": "Não autorizado"}), 401

            return fn(*args, **kwargs)

        return decorator

    return wrapper


def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()

            claims = get_jwt()
            usuario = _usuario_autenticado_ativo()

            if not usuario:
                _registrar_acesso_negado_usuario_inativo()
                return jsonify({"error": "Não autorizado"}), 401

            role = usuario.role or claims.get("role")

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
