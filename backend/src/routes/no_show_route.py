from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.auditoria_model import AcaoAuditoria
from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
from src.security.decorators import roles_required
from src.security.unidades import unidade_atual_required
from src.services.auditoria_service import registrar_auditoria
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
@roles_required("recepcao", "admin")
def index():
    try:
        hoje = date.today()
        data_ini = parse_data(request.args.get("dataIni"), hoje.replace(day=1))
        data_fim = parse_data(request.args.get("dataFim"), hoje)
        page = parse_int("page", 1)
        page_size = parse_int("pageSize", 20, maximo=500)
        unidade = unidade_atual_required()

        resultado = listar_no_show(
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
        )
        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_NO_SHOW,
            entidade="no_show",
            usuario_id=int(get_jwt_identity()),
            descricao=f"Listagem de no-show. data_ini={data_ini} data_fim={data_fim} page={page} page_size={page_size}",
        )
        return jsonify(resultado), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao listar no-show")
        return jsonify({"error": "Erro interno ao listar no-show"}), 500


@no_show_bp.route("/<int:agenda_id>/motivo", methods=["PATCH"])
@jwt_required()
@roles_required("recepcao", "admin")
def atualizar_motivo(agenda_id):
    try:
        body = request.get_json() or {}
        unidade = unidade_atual_required()
        agenda = db.session.get(MedSpdataAgenda, agenda_id)
        if not agenda:
            raise LookupError("Agenda do no-show não encontrada")
        if agenda.unidade_id != unidade.id:
            raise PermissionError("Agenda não pertence à unidade selecionada")

        return jsonify(registrar_motivo_no_show(agenda_id, body.get("motivo"))), 200

    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao registrar motivo do no-show")
        return jsonify({"error": "Erro interno ao registrar motivo do no-show"}), 500
