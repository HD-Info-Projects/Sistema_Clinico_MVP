from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.auditoria_model import AcaoAuditoria
from src.security.decorators import roles_required
from src.services.auditoria_service import registrar_auditoria
from src.services.spdata_atendimentos_service import (
    atualizar_status_agenda,
    listar_agenda_medica,
)
from src.settings.extensions import db


agenda_medica_bp = Blueprint("agenda_medica", __name__, url_prefix="/agenda-medica")


def _parse_data(valor, default=None):
    if not valor:
        return default or date.today()

    return datetime.fromisoformat(str(valor)[:10]).date()


@agenda_medica_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("medico")
def listar_agenda():
    try:
        usuario_id = int(get_jwt_identity())
        data = request.args.get("data")
        search = (request.args.get("search") or request.args.get("q") or "").strip() or None
        status = request.args.get("status")
        tem_filtro_data = any(request.args.get(nome) for nome in ("data", "dataIni", "dataFim"))

        if search and not tem_filtro_data:
            data_ini = None
            data_fim = None
        else:
            data_ini = _parse_data(request.args.get("dataIni") or data)
            data_fim = _parse_data(request.args.get("dataFim") or data, data_ini)

        resultado = listar_agenda_medica(usuario_id, data_ini, data_fim, status=status, search=search)
        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_AGENDA,
            entidade="agenda_medica",
            usuario_id=usuario_id,
            descricao=f"Listagem de agenda médica. data_ini={data_ini} data_fim={data_fim} status={status or ''}",
        )
        return jsonify(resultado), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao listar agenda médica")
        return jsonify({"error": "Erro interno ao listar agenda médica"}), 500


@agenda_medica_bp.route("/<int:med_spdata_atendimento_id>/status", methods=["PATCH"])
@jwt_required()
@roles_required("medico")
def atualizar_status(med_spdata_atendimento_id):
    try:
        usuario_id = int(get_jwt_identity())
        body = request.get_json() or {}
        status = body.get("status")
        consulta = body.get("consulta")

        return jsonify(
            atualizar_status_agenda(
                med_spdata_atendimento_id,
                status,
                usuario_id=usuario_id,
                consulta=consulta,
            )
        ), 200

    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao atualizar status da agenda médica")
        return jsonify({"error": "Erro interno ao atualizar agenda médica"}), 500
