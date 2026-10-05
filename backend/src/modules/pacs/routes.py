from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
import requests

from src.integrations.pacs import (
    buscar_exames_paciente_firebird,
    buscar_laudo_firebird,
    buscar_paciente_do_lancamento,
    chamar_viewer_exame,
    exame_para_frontend,
    normalizar_int,
)
from src.models.auditoria_model import AcaoAuditoria
from src.modules.clinico.prontuario import _referencia_autorizada_paciente
from src.security.decorators import roles_required
from src.security.roles import MEDICO_ROLES
from src.security.unidades import unidade_id_request
from src.services.auditoria_service import registrar_auditoria


exames_pacs_bp = Blueprint("exames_pacs", __name__, url_prefix="/exames-pacs")


def _registrar_auditoria_pacs(acao, usuario_id, referencia=None, id_lancamento=None, total=None):
    paciente_id = normalizar_int((referencia or {}).get("ID_PACIENTE_SPDATA"))
    if paciente_id is None:
        paciente_id = normalizar_int((referencia or {}).get("paciente_id"))

    detalhes = []
    if paciente_id is not None:
        detalhes.append(f"paciente_id={paciente_id}")
    if id_lancamento is not None:
        detalhes.append(f"silanexa_id={id_lancamento}")
    if total is not None:
        detalhes.append(f"total={total}")

    registrar_auditoria(
        acao,
        entidade="exame_pacs",
        entidade_id=id_lancamento or paciente_id,
        usuario_id=usuario_id,
        descricao="; ".join(detalhes) or None,
    )


def _json_no_store(payload, status_code=200):
    response = jsonify(payload)
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response, status_code


def _garantir_acesso_paciente(usuario_id: int, paciente_id: int):
    return _referencia_autorizada_paciente(
        usuario_id,
        paciente_id=paciente_id,
        unidade_id=unidade_id_request(),
    )


def _garantir_acesso_lancamento(usuario_id: int, id_lancamento: int):
    referencia = buscar_paciente_do_lancamento(id_lancamento)
    if not referencia:
        raise LookupError("Exame não encontrado")

    paciente_id = normalizar_int(referencia.get("ID_PACIENTE_SPDATA"))
    if paciente_id is None:
        raise LookupError("Paciente do exame não encontrado")

    _garantir_acesso_paciente(usuario_id, paciente_id)
    return referencia


@exames_pacs_bp.route("/paciente/<int:paciente_id>", methods=["GET"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def listar_exames_paciente(paciente_id: int):
    usuario_id = None
    try:
        usuario_id = int(get_jwt_identity())
        referencia = _garantir_acesso_paciente(usuario_id, paciente_id)
        paciente_id_autorizado = normalizar_int(referencia.get("paciente_id")) or paciente_id
        rows = buscar_exames_paciente_firebird(paciente_id_autorizado)
        items = [exame_para_frontend(row) for row in rows]
        _registrar_auditoria_pacs(
            AcaoAuditoria.VISUALIZOU_EXAMES_PACS,
            usuario_id,
            referencia={**referencia, "paciente_id": paciente_id_autorizado},
            total=len(items),
        )
        return jsonify({
            "pacienteId": paciente_id_autorizado,
            "items": items,
        }), 200

    except PermissionError:
        if usuario_id is not None:
            _registrar_auditoria_pacs(
                AcaoAuditoria.ACESSO_NEGADO,
                usuario_id,
                referencia={"paciente_id": paciente_id},
            )
        return jsonify({"error": "Paciente não encontrado"}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Erro ao listar exames PACS do paciente")
        return jsonify({"error": "Erro interno ao listar exames do paciente"}), 500


@exames_pacs_bp.route("/<int:id>/laudo", methods=["GET"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def busca_laudo_exame_pacs(id: int):
    usuario_id = None
    try:
        usuario_id = int(get_jwt_identity())
        referencia = _garantir_acesso_lancamento(usuario_id, id)
        laudo_base64 = buscar_laudo_firebird(id)
        if not laudo_base64:
            return jsonify({"error": "Laudo não encontrado"}), 404

        _registrar_auditoria_pacs(
            AcaoAuditoria.VISUALIZOU_LAUDO_EXAME,
            usuario_id,
            referencia=referencia,
            id_lancamento=id,
        )

        return _json_no_store({
            "idTokenLancamentoExame": id,
            "contentType": "application/pdf",
            "filename": f"laudo-exame-{id}.pdf",
            "base64": laudo_base64,
        })

    except (LookupError, PermissionError):
        if usuario_id is not None:
            _registrar_auditoria_pacs(
                AcaoAuditoria.ACESSO_NEGADO,
                usuario_id,
                id_lancamento=id,
            )
        return jsonify({"error": "Exame não encontrado"}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Erro ao buscar laudo PACS do exame")
        return jsonify({"error": "Erro interno ao buscar laudo do exame"}), 500


@exames_pacs_bp.route("/<int:id>", methods=["POST"])
@jwt_required()
@roles_required(*MEDICO_ROLES)
def busca_exames_pacs(id: int):
    usuario_id = None
    try:
        usuario_id = int(get_jwt_identity())
        referencia = _garantir_acesso_lancamento(usuario_id, id)
        payload, status_code = chamar_viewer_exame(id)
        _registrar_auditoria_pacs(
            AcaoAuditoria.VISUALIZOU_IMAGEM_EXAME,
            usuario_id,
            referencia=referencia,
            id_lancamento=id,
        )
        return _json_no_store(payload, status_code)

    except (LookupError, PermissionError):
        if usuario_id is not None:
            _registrar_auditoria_pacs(
                AcaoAuditoria.ACESSO_NEGADO,
                usuario_id,
                id_lancamento=id,
            )
        return jsonify({"error": "Exame não encontrado"}), 404
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502
    except Exception:
        current_app.logger.exception("Erro ao buscar viewer PACS do exame")
        return jsonify({"error": "Erro interno ao buscar viewer do exame"}), 500


__all__ = [
    "busca_exames_pacs",
    "busca_laudo_exame_pacs",
    "exames_pacs_bp",
    "listar_exames_paciente",
]
