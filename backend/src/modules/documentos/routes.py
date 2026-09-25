from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.auditoria_model import AcaoAuditoria
from src.modules.documentos.service import (
    listar_documentos_atendimento,
    listar_documentos_personalizados_atendimento,
    listar_documentos_por_ids,
    salvar_documento,
    salvar_documento_personalizado,
    excluir_documento_personalizado,
)
from src.security.decorators import roles_required
from src.security.roles import MEDICO_ROLES
from src.security.unidades import unidade_id_request
from src.services.auditoria_service import registrar_auditoria
from src.settings.extensions import db


documentos_medicos_bp = Blueprint("documentos_medicos", __name__, url_prefix="/documentos-medicos")


def parse_ids(valor):
    ids = []
    for item in str(valor or "").split(","):
        item = item.strip()
        if not item:
            continue
        ids.append(int(item))
    return ids


@documentos_medicos_bp.route("", methods=["GET"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def listar_documentos():
    try:
        usuario_id = int(get_jwt_identity())
        ids = parse_ids(request.args.get("ids"))
        if not ids:
            return jsonify([]), 200

        resultado = listar_documentos_por_ids(
            usuario_id,
            ids,
            unidade_id=unidade_id_request(),
        )
        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_DOCUMENTOS_MEDICOS,
            entidade="documentos_medicos",
            usuario_id=usuario_id,
            descricao=f"Listagem de documentos médicos por ids. total_ids={len(ids)}",
        )
        return jsonify(resultado), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:
        current_app.logger.exception("Erro ao listar documentos médicos")
        return jsonify({"error": "Erro interno ao listar documentos médicos"}), 500


@documentos_medicos_bp.route("/<int:med_spdata_atendimento_id>", methods=["GET"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def listar_documentos_do_atendimento(med_spdata_atendimento_id):
    try:
        usuario_id = int(get_jwt_identity())
        resultado = listar_documentos_atendimento(
            usuario_id,
            med_spdata_atendimento_id,
            unidade_id=unidade_id_request(),
        )
        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_DOCUMENTOS_MEDICOS,
            entidade="med_spdata_atendimentos",
            entidade_id=med_spdata_atendimento_id,
            usuario_id=usuario_id,
            descricao="Listagem de documentos médicos do atendimento",
        )
        return jsonify(resultado), 200

    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:
        current_app.logger.exception("Erro ao listar documentos médicos do atendimento")
        return jsonify({"error": "Erro interno ao listar documentos médicos"}), 500


@documentos_medicos_bp.route("/<int:med_spdata_atendimento_id>/personalizados", methods=["GET"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def listar_documentos_personalizados(med_spdata_atendimento_id):
    try:
        usuario_id = int(get_jwt_identity())
        resultado = listar_documentos_personalizados_atendimento(
            usuario_id,
            med_spdata_atendimento_id,
            unidade_id=unidade_id_request(),
        )
        return jsonify(resultado), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:
        current_app.logger.exception("Erro ao listar documentos personalizados")
        return jsonify({"error": "Erro interno ao listar documentos personalizados"}), 500


@documentos_medicos_bp.route("/<int:med_spdata_atendimento_id>/personalizados", methods=["POST"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def criar_documento_personalizado(med_spdata_atendimento_id):
    return _salvar_documento_personalizado(med_spdata_atendimento_id)


@documentos_medicos_bp.route("/<int:med_spdata_atendimento_id>/personalizados/<int:documento_id>", methods=["PUT"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def editar_documento_personalizado(med_spdata_atendimento_id, documento_id):
    return _salvar_documento_personalizado(med_spdata_atendimento_id, documento_id)


@documentos_medicos_bp.route("/<int:med_spdata_atendimento_id>/personalizados/<int:documento_id>", methods=["DELETE"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def excluir_documento_personalizado_route(med_spdata_atendimento_id, documento_id):
    try:
        excluir_documento_personalizado(
            int(get_jwt_identity()),
            med_spdata_atendimento_id,
            documento_id,
            unidade_id=unidade_id_request(),
        )
        return jsonify({"ok": True}), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except PermissionError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 403
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao excluir documento personalizado")
        return jsonify({"error": "Erro interno ao excluir documento personalizado"}), 500


def _salvar_documento_personalizado(med_spdata_atendimento_id, documento_id=None):
    try:
        usuario_id = int(get_jwt_identity())
        body = request.get_json() or {}
        dados = body.get("dados") if isinstance(body, dict) and "dados" in body else body
        resultado = salvar_documento_personalizado(
            usuario_id,
            med_spdata_atendimento_id,
            dados,
            unidade_id=unidade_id_request(),
            documento_id=documento_id,
        )
        registrar_auditoria(
            AcaoAuditoria.SALVOU_DOCUMENTO_MEDICO,
            entidade="documentos_medicos_personalizados",
            entidade_id=resultado["id"],
            usuario_id=usuario_id,
            descricao="Documento médico personalizado salvo",
        )
        return jsonify(resultado), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except PermissionError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao salvar documento personalizado")
        return jsonify({"error": "Erro interno ao salvar documento personalizado"}), 500


@documentos_medicos_bp.route("/<int:med_spdata_atendimento_id>/<tipo>", methods=["PUT"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def salvar_documento_medico(med_spdata_atendimento_id, tipo):
    try:
        usuario_id = int(get_jwt_identity())
        body = request.get_json() or {}
        dados = body.get("dados") if isinstance(body, dict) and "dados" in body else body

        resultado = salvar_documento(
            usuario_id,
            med_spdata_atendimento_id,
            tipo,
            dados,
            unidade_id=unidade_id_request(),
        )
        registrar_auditoria(
            AcaoAuditoria.SALVOU_DOCUMENTO_MEDICO,
            entidade="med_spdata_atendimentos",
            entidade_id=med_spdata_atendimento_id,
            usuario_id=usuario_id,
            descricao=f"Documento médico salvo. tipo={tipo}",
        )
        return jsonify(resultado), 200

    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except PermissionError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao salvar documento médico")
        return jsonify({"error": "Erro interno ao salvar documento médico"}), 500
