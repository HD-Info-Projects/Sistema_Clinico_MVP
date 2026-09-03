from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from src.models.auditoria_model import AcaoAuditoria
from src.models.medico_model import Medico
from src.models.usuario_model import Usuario
from src.models.usuario_unidade_model import UsuarioUnidade
from src.security.decorators import roles_required
from src.security.unidades import unidade_id_request
from src.services.auditoria_service import registrar_auditoria
from src.services.spdata_recepcao_service import (
    buscar_pacientes_spdata,
    listar_convenios_recepcao,
    listar_procedimentos_recepcao,
    salvar_atendimento_spdata,
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


def medico_para_dict(usuario, medico):
    return {
        "id": medico.id,
        "usuarioId": usuario.id,
        "nome": usuario.nome_completo,
        "spdataId": medico.spdata_id,
        "crm": medico.crm,
        "crmAtendimento": medico.crm_atendimento_spdata,
        "especialidade": medico.especialidade,
    }


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
        usuario_id = int(get_jwt_identity())
        registrar_auditoria(
            AcaoAuditoria.SINCRONIZOU_SPDATA,
            entidade="paciente_spdata",
            entidade_id=paciente.get("idPacienteSpdata"),
            usuario_id=usuario_id,
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
        usuario_id = int(get_jwt_identity())
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
    unidade_id = unidade_id_request()
    query = (
        select(Usuario, Medico)
        .join(Medico, Medico.usuario_id == Usuario.id)
        .where(
            Usuario.role == "medico",
            Usuario.ativo.is_(True),
            Medico.ativo.is_(True),
        )
        .order_by(Usuario.nome_completo)
    )

    if unidade_id:
        query = query.join(
            UsuarioUnidade,
            UsuarioUnidade.usuario_id == Usuario.id,
        ).where(
            UsuarioUnidade.unidade_id == unidade_id,
            UsuarioUnidade.ativo.is_(True),
        )

    medicos = [
        medico_para_dict(usuario, medico)
        for usuario, medico in db.session.execute(query).all()
    ]
    return jsonify({"medicos": medicos}), 200
