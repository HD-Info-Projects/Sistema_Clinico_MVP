from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.modules.unidades.service import (
    UnidadePayloadError,
    atualizar_unidade as atualizar_unidade_service,
    buscar_unidade_publica,
    criar_unidade as criar_unidade_service,
    inativar_unidade as inativar_unidade_service,
    listar_unidades_admin,
    listar_unidades_usuario_frontend,
)
from src.security.decorators import active_user_required, roles_required


unidades_bp = Blueprint("unidades", __name__, url_prefix="/unidades")


def _payload_error_response(error):
    return jsonify({"error": error.message, "fields": error.fields}), 400


@unidades_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("admin")
def listar_unidades():
    unidades = listar_unidades_admin()
    return jsonify([unidade._to_dict() for unidade in unidades]), 200


@unidades_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin")
def criar_unidade():
    data = request.get_json(silent=True) or {}
    try:
        unidade = criar_unidade_service(data)
    except UnidadePayloadError as error:
        return _payload_error_response(error)

    return jsonify({
        "message": "Unidade cadastrada com sucesso.",
        "unidade": unidade._to_dict(),
    }), 201


@unidades_bp.route("/<int:unidade_id>", methods=["PUT"])
@jwt_required()
@roles_required("admin")
def atualizar_unidade(unidade_id):
    data = request.get_json(silent=True) or {}
    try:
        unidade = atualizar_unidade_service(unidade_id, data)
    except UnidadePayloadError as error:
        return _payload_error_response(error)

    if not unidade:
        return jsonify({"error": "Unidade não encontrada."}), 404

    return jsonify({
        "message": "Unidade atualizada com sucesso.",
        "unidade": unidade._to_dict(),
    }), 200


@unidades_bp.route("/<int:unidade_id>", methods=["DELETE"])
@jwt_required()
@roles_required("admin")
def inativar_unidade(unidade_id):
    unidade = inativar_unidade_service(unidade_id)
    if not unidade:
        return jsonify({"error": "Unidade não encontrada."}), 404

    return jsonify({
        "message": "Unidade inativada com sucesso.",
        "unidade": unidade._to_dict(),
    }), 200


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
