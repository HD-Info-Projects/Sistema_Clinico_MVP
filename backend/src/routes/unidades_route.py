from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.security.decorators import active_user_required
from src.services.unidades_service import (
    buscar_unidade_publica,
    listar_unidades_usuario_frontend,
)


unidades_bp = Blueprint("unidades", __name__, url_prefix="/unidades")


@unidades_bp.route("/minhas", methods=["GET"])
@jwt_required()
@active_user_required()
def minhas_unidades():
    usuario_id = int(get_jwt_identity())
    return jsonify(listar_unidades_usuario_frontend(usuario_id)), 200


@unidades_bp.route("/<identificador>/publica", methods=["GET"])
def unidade_publica(identificador):
    unidade = buscar_unidade_publica(identificador)
    if not unidade:
        return jsonify({"error": "Unidade não encontrada"}), 404

    return jsonify(unidade._to_frontend_dict()), 200
