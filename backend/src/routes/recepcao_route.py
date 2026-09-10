from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.auditoria_model import AcaoAuditoria
from src.security.decorators import roles_required
from src.security.unidades import unidade_id_request
from src.services.auditoria_service import registrar_auditoria
from src.services.spdata_recepcao_service import (
    buscar_pacientes_spdata,
    listar_convenios_recepcao,
    listar_medicos_recepcao,
    listar_procedimentos_recepcao,
    salvar_atendimento_spdata,
    salvar_novo_atendimento_spdata,
    salvar_paciente_spdata,
)
from src.settings.extensions import db


recepcao_bp = Blueprint("recepcao", __name__, url_prefix="/recepcao")


def _json_body():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        raise ValueError("Payload inválido")
    return data


def _erro_response(error):
    if isinstance(error, ValueError):
        return jsonify({"error": str(error)}), 400
    if isinstance(error, PermissionError):
        return jsonify({"error": str(error)}), 403
    if isinstance(error, LookupError):
        return jsonify({"error": str(error)}), 404
    return None


def _usuario_id():
    return int(get_jwt_identity())


@recepcao_bp.route("/pacientes/buscar", methods=["GET"])
@jwt_required()
@roles_required("recepcao", "admin")
def buscar_pacientes():
    try:
        pacientes = buscar_pacientes_spdata(
            cpf=request.args.get("cpf"),
            prontuario=request.args.get("prontuario"),
            paciente_id=request.args.get("id"),
            search=request.args.get("q") or request.args.get("search"),
        )
        return jsonify({"pacientes": pacientes}), 200
    except Exception as error:
        response = _erro_response(error)
        if response:
            return response
        current_app.logger.exception("Erro ao buscar pacientes no SPDATA")
        return jsonify({"error": "Erro interno ao buscar pacientes"}), 500


@recepcao_bp.route("/pacientes", methods=["POST"])
@jwt_required()
@roles_required("recepcao", "admin")
def salvar_paciente():
    try:
        resultado = salvar_paciente_spdata(_json_body())
        paciente = resultado.get("paciente") or {}
        registrar_auditoria(
            AcaoAuditoria.SINCRONIZOU_SPDATA,
            entidade="paciente_spdata",
            entidade_id=paciente.get("idPacienteSpdata"),
            usuario_id=_usuario_id(),
            descricao="Paciente criado/atualizado no SPDATA pela recepção.",
        )
        return jsonify(resultado), 201 if resultado.get("created") else 200
    except Exception as error:
        db.session.rollback()
        response = _erro_response(error)
        if response:
            return response
        current_app.logger.exception("Erro ao salvar paciente no SPDATA")
        return jsonify({"error": "Erro interno ao salvar paciente"}), 500


@recepcao_bp.route("/atendimentos", methods=["POST"])
@jwt_required()
@roles_required("recepcao", "admin")
def salvar_atendimento():
    try:
        usuario_id = _usuario_id()
        resultado = salvar_atendimento_spdata(
            _json_body(),
            usuario_id=usuario_id,
            unidade_id=unidade_id_request(),
        )
        atendimento = resultado.get("atendimento") or {}
        registrar_auditoria(
            AcaoAuditoria.SINCRONIZOU_SPDATA,
            entidade="atendimento_spdata",
            entidade_id=atendimento.get("spdataAtendimentoId") or atendimento.get("id"),
            usuario_id=usuario_id,
            descricao="Atendimento criado/sincronizado no SPDATA pela recepção.",
        )
        return jsonify(resultado), 201 if resultado.get("created") else 200
    except Exception as error:
        db.session.rollback()
        response = _erro_response(error)
        if response:
            return response
        current_app.logger.exception("Erro ao salvar atendimento no SPDATA")
        return jsonify({"error": "Erro interno ao salvar atendimento"}), 500


@recepcao_bp.route("/novo-atendimento", methods=["POST"])
@jwt_required()
@roles_required("recepcao", "admin")
def salvar_novo_atendimento():
    try:
        usuario_id = _usuario_id()
        resultado = salvar_novo_atendimento_spdata(
            _json_body(),
            usuario_id=usuario_id,
            unidade_id=unidade_id_request(),
        )
        atendimento = resultado.get("atendimento") or {}
        registrar_auditoria(
            AcaoAuditoria.SINCRONIZOU_SPDATA,
            entidade="novo_atendimento_spdata",
            entidade_id=atendimento.get("spdataAtendimentoId") or atendimento.get("id"),
            usuario_id=usuario_id,
            descricao="Paciente e atendimento criados/sincronizados no SPDATA pela recepção.",
        )
        return jsonify(resultado), 201 if resultado.get("atendimentoCreated") else 200
    except Exception as error:
        db.session.rollback()
        response = _erro_response(error)
        if response:
            return response
        current_app.logger.exception("Erro ao salvar novo atendimento no SPDATA")
        return jsonify({"error": "Erro interno ao salvar novo atendimento"}), 500


@recepcao_bp.route("/convenios", methods=["GET"])
@jwt_required()
@roles_required("recepcao", "admin")
def listar_convenios():
    return jsonify({"convenios": listar_convenios_recepcao(request.args.get("q"))}), 200


@recepcao_bp.route("/procedimentos", methods=["GET"])
@jwt_required()
@roles_required("recepcao", "admin")
def listar_procedimentos():
    return jsonify({"procedimentos": listar_procedimentos_recepcao(request.args.get("q"))}), 200


@recepcao_bp.route("/medicos", methods=["GET"])
@jwt_required()
@roles_required("recepcao", "admin")
def listar_medicos():
    return jsonify({"medicos": listar_medicos_recepcao(unidade_id_request())}), 200
