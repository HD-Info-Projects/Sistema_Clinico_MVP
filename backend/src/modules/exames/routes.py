from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from src.modules.exames.service import (
    buscar_exames_catalogo,
    exame_para_dict,
    listar_exames_catalogo,
)
from src.security.decorators import roles_required
from src.security.roles import MEDICO_ROLES


exames_bp = Blueprint("exames", __name__, url_prefix="/exames")


@exames_bp.route("", methods=["GET"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def listar_exames():
    return jsonify({
        "exames": [
            exame_para_dict(exame)
            for exame in listar_exames_catalogo()
        ]
    }), 200


@exames_bp.route("/buscar", methods=["GET"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def buscar_exames():
    return jsonify({
        "exames": [
            exame_para_dict(exame)
            for exame in buscar_exames_catalogo(request.args.get("q"))
        ]
    }), 200
