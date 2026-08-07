from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from src.security.decorators import roles_required
from src.security.unidades import unidade_atual_required
from src.services.no_show_service import listar_no_show, registrar_motivo_no_show
from src.settings.extensions import db


no_show_bp = Blueprint("no_show", __name__, url_prefix="/no_show")


def parse_data(valor, default=None):
    if not valor:
        return default or date.today()
    return datetime.fromisoformat(str(valor)[:10]).date()


def parse_int(nome, default, minimo=1, maximo=None):
    valor = request.args.get(nome, default=default, type=int)
    valor = max(valor or default, minimo)
    if maximo is not None:
        valor = min(valor, maximo)
    return valor


@no_show_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("recepcao")
def index():
    try:
        hoje = date.today()
        data_ini = parse_data(request.args.get("dataIni"), hoje.replace(day=1))
        data_fim = parse_data(request.args.get("dataFim"), hoje)
        page = parse_int("page", 1)
        page_size = parse_int("pageSize", 20, maximo=500)
        unidade = unidade_atual_required()

        return jsonify(listar_no_show(
            data_ini,
            data_fim,
            unidade=unidade,
            medico=request.args.get("medico"),
            especialidade=request.args.get("especialidade"),
            convenio=request.args.get("convenio"),
            status=request.args.get("status"),
            q=request.args.get("q"),
            page=page,
            page_size=page_size,
        )), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erro ao listar no-show")
        return jsonify({"error": str(e)}), 500


@no_show_bp.route("/<int:agenda_id>/motivo", methods=["PATCH"])
@jwt_required()
@roles_required("recepcao")
def atualizar_motivo(agenda_id):
    try:
        body = request.get_json() or {}
        return jsonify(registrar_motivo_no_show(agenda_id, body.get("motivo"))), 200

    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erro ao registrar motivo do no-show")
        return jsonify({"error": str(e)}), 500
