from flask import request
from flask_jwt_extended import get_jwt_identity

from src.services.unidades_service import resolver_unidade_usuario


def unidade_id_request():
    valor = (
        request.headers.get("X-Unidade-Id")
        or request.args.get("unidadeId")
        or request.args.get("clinicaId")
    )

    if valor is None and request.method in {"POST", "PUT", "PATCH"}:
        data = request.get_json(silent=True) or {}
        if isinstance(data, dict):
            valor = data.get("unidadeId") or data.get("clinicaId")

    if valor is None or str(valor).strip() == "":
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError("unidadeId inválido")


def unidade_atual_required():
    usuario_id = int(get_jwt_identity())
    return resolver_unidade_usuario(usuario_id, unidade_id_request())
