from sqlalchemy import String, cast, or_

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from src.models.model_mydsystem.med_procedimentos_model import Procedimento
from src.settings.extensions import db


procedimentos_bp = Blueprint("procedimentos", __name__, url_prefix="/procedimentos")


def procedimento_para_dict(procedimento):
    return {
        "id": procedimento.id,
        "nome": procedimento.nome,
        "codigo_procedimento": procedimento.codigo_procedimento,
        "tipo_ato_codigo": procedimento.tipo_ato_codigo,
        "tipo_ato_nome": procedimento.tipo_ato_nome,
        "apelido_procedimento": procedimento.apelido_procedimento,
        "exige_autorizacao": procedimento.exige_autorizacao,
        "qtde_max_guia": procedimento.qtde_max_guia,
    }


@procedimentos_bp.route("/buscar", methods=["GET"])
@jwt_required()
def buscar_procedimentos():
    q = (request.args.get("q") or "").strip()

    if len(q) < 2:
        return jsonify({"procedimentos": []}), 200

    like = f"%{q}%"
    resultados = (
        db.session.query(Procedimento)
        .filter(
            Procedimento.ativo.is_(True),
            or_(
                Procedimento.nome.ilike(like),
                Procedimento.apelido_procedimento.ilike(like),
                Procedimento.tipo_ato_nome.ilike(like),
                cast(Procedimento.codigo_procedimento, String).ilike(like),
            ),
        )
        .order_by(Procedimento.nome)
        .limit(50)
        .all()
    )

    return jsonify({
        "procedimentos": [
            procedimento_para_dict(procedimento)
            for procedimento in resultados
        ]
    }), 200
