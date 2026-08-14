from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.auditoria_model import AcaoAuditoria
from src.security.decorators import roles_required
from src.security.unidades import unidade_id_request
from src.services.auditoria_service import registrar_auditoria
from src.services.documentos_medicos_service import (
    listar_documentos_atendimento,
    listar_documentos_por_ids,
    salvar_documento,
)
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
@roles_required("medico")
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
@roles_required("medico")
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


@documentos_medicos_bp.route("/<int:med_spdata_atendimento_id>/<tipo>", methods=["PUT"])
@jwt_required()
@roles_required("medico")
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
