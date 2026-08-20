from sqlalchemy import or_

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from src.models.model_mydsystem.med_exames_model import Exame
from src.security.decorators import roles_required
from src.settings.extensions import db


exames_bp = Blueprint("exames", __name__, url_prefix="/exames")


@exames_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("medico")
def listar_exames():
    resultados = (
        db.session.query(Exame)
        .order_by(Exame.nome)
        .all()
    )

    return jsonify({
        "exames": [
            {
                "id": e.id,
                "nome": e.nome,
                "codigo_alfanumerico": e.codigo_alfanumerico,
                "codigo_amb": e.codigo_amb,
            }
            for e in resultados
        ]
    }), 200


@exames_bp.route("/buscar", methods=["GET"])
@jwt_required()
@roles_required("medico")
def buscar_exames():
    q = (request.args.get("q") or "").strip()

    if len(q) < 2:
        return jsonify({"exames": []}), 200

    like = f"%{q}%"
    resultados = (
        db.session.query(Exame)
        .filter(
            or_(
                Exame.nome.ilike(like),
                Exame.codigo_alfanumerico.ilike(like),
                Exame.codigo_amb.ilike(like),
            )
        )
        .order_by(Exame.nome)
        .limit(50)
        .all()
    )

    return jsonify({
        "exames": [
            {
                "id": e.id,
                "nome": e.nome,
                "codigo_alfanumerico": e.codigo_alfanumerico,
                "codigo_amb": e.codigo_amb,
            }
            for e in resultados
        ]
    }), 200
