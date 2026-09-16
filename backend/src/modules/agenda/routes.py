from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.auditoria_model import AcaoAuditoria
from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
from src.security.decorators import roles_required
from src.security.unidades import unidade_atual_required, unidade_id_request
from src.services.auditoria_service import registrar_auditoria
from src.services.no_show_service import listar_no_show, registrar_motivo_no_show
from src.services.spdata_atendimentos_service import (
    atualizar_status_agenda,
    listar_agenda_medica,
    listar_marcadores_agenda_medica,
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

        resultado = listar_agenda_medica(
            usuario_id,
            data_ini,
            data_fim,
            status=status,
            search=search,
            unidade_id=unidade_id_request(),
            somente_visiveis_medico=True,
        )
        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_AGENDA,
            entidade="agenda_medica",
            usuario_id=usuario_id,
            descricao=f"Listagem de agenda médica. data_ini={data_ini} data_fim={data_fim} status={status or ''} visibilidade_medica=true",
        )
        return jsonify(resultado), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao listar agenda médica")
        return jsonify({"error": "Erro interno ao listar agenda médica"}), 500


@agenda_medica_bp.route("/marcadores", methods=["GET"])
@jwt_required()
@roles_required("medico")
def listar_marcadores_agenda():
    try:
        usuario_id = int(get_jwt_identity())
        data = request.args.get("data")
        data_ini = _parse_data(request.args.get("dataIni") or data)
        data_fim = _parse_data(request.args.get("dataFim") or data, data_ini)
        sincronizar = str(request.args.get("sincronizar") or "").lower() in {"1", "true", "sim", "s"}

        resultado = listar_marcadores_agenda_medica(
            usuario_id,
            data_ini,
            data_fim,
            unidade_id=unidade_id_request(),
            sincronizar=sincronizar,
            somente_visiveis_medico=True,
        )
        return jsonify(resultado), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao listar marcadores da agenda médica")
        return jsonify({"error": "Erro interno ao listar marcadores da agenda médica"}), 500


@agenda_medica_bp.route("/<int:med_spdata_atendimento_id>/status", methods=["PATCH"])
@jwt_required()
@roles_required("medico")
def atualizar_status(med_spdata_atendimento_id):
    try:
        usuario_id = int(get_jwt_identity())
        body = request.get_json() or {}
        status = body.get("status")
        consulta = body.get("consulta")

        resultado = atualizar_status_agenda(
            med_spdata_atendimento_id,
            status,
            usuario_id=usuario_id,
            consulta=consulta,
            unidade_id=unidade_id_request(),
        )
        status_final = resultado.get("status") or status
        acao = AcaoAuditoria.ALTEROU_STATUS_AGENDA
        if status_final == "em-atendimento":
            acao = AcaoAuditoria.INICIOU_ATENDIMENTO
        elif status_final == "atendido":
            acao = AcaoAuditoria.FINALIZOU_ATENDIMENTO

        registrar_auditoria(
            acao,
            entidade="agenda_medica",
            entidade_id=med_spdata_atendimento_id,
            usuario_id=usuario_id,
            descricao=f"Status de atendimento atualizado. status={status_final}",
        )

        return jsonify(resultado), 200

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


no_show_bp = Blueprint("no_show", __name__, url_prefix="/no_show")


def _parse_data_ns(valor, default=None):
    if not valor:
        return default or date.today()
    return datetime.fromisoformat(str(valor)[:10]).date()


def _parse_int_ns(nome, default, minimo=1, maximo=None):
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
        data_ini = _parse_data_ns(request.args.get("dataIni"), hoje.replace(day=1))
        data_fim = _parse_data_ns(request.args.get("dataFim"), hoje)
        page = _parse_int_ns("page", 1)
        page_size = _parse_int_ns("pageSize", 20, maximo=500)
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

        resultado = registrar_motivo_no_show(agenda_id, body.get("motivo"))
        registrar_auditoria(
            AcaoAuditoria.ALTEROU_MOTIVO_NO_SHOW,
            entidade="no_show",
            entidade_id=agenda_id,
            usuario_id=int(get_jwt_identity()),
            descricao=f"Motivo do no-show atualizado. motivo={resultado.get('motivo')}",
        )
        return jsonify(resultado), 200

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
