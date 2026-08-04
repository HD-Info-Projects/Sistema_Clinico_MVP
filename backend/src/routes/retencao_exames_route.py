from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from src.security.decorators import roles_required
from src.security.unidades import unidade_atual_required
from src.services.retencao_exames_service import listar_retencao_exames
from src.settings.extensions import db


retencao_exames_bp = Blueprint("retencao_exames", __name__, url_prefix="/retencao-exames")


def parse_data(valor, default=None):
    if not valor:
        return default or date.today()
    return datetime.fromisoformat(str(valor)[:10]).date()


@retencao_exames_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("recepcao")
def index():
    try:
        hoje = date.today()
        data_ini = parse_data(request.args.get("dataIni"), hoje.replace(day=1))
        data_fim = parse_data(request.args.get("dataFim"), hoje)

        if data_fim < data_ini:
            return jsonify({"error": "dataFim não pode ser menor que dataIni."}), 400

        return jsonify(listar_retencao_exames(data_ini, data_fim, unidade=unidade_atual_required())), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erro ao listar retenção de exames")
        return jsonify({"error": str(e)}), 500
