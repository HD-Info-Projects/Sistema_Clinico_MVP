from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from src.modules.procedimentos.service import (
    buscar_procedimentos_catalogo,
    procedimento_para_dict,
)
from src.security.decorators import roles_required
from src.security.roles import MEDICO_ROLES


procedimentos_bp = Blueprint("procedimentos", __name__, url_prefix="/procedimentos")


@procedimentos_bp.route("/buscar", methods=["GET"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def buscar_procedimentos():
    procedimentos = buscar_procedimentos_catalogo(request.args.get("q"))

    return jsonify({
        "procedimentos": [
            procedimento_para_dict(procedimento)
            for procedimento in procedimentos
        ]
    }), 200
