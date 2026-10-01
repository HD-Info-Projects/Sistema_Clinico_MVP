from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.modules.spdata_sync.service import (
    ActiveJobError,
    InvalidTargetError,
    QueueUnavailableError,
    buscar_job,
    criar_e_enfileirar_job,
    listar_jobs,
)
from src.security.decorators import roles_required
from src.settings.extensions import limiter


spdata_sync_bp = Blueprint(
    "spdata_sync",
    __name__,
    url_prefix="/admin/spdata-sync/jobs",
)


def _rate_limit():
    return current_app.config["SPDATA_IMPORT_RATE_LIMIT"]


def _admin_rate_key():
    return f"spdata-sync:{get_jwt_identity()}"


@spdata_sync_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin")
@limiter.limit(_rate_limit, key_func=_admin_rate_key)
def criar():
    payload = request.get_json(silent=True) or {}
    try:
        usuario_id = int(get_jwt_identity())
        job = criar_e_enfileirar_job(payload.get("target", "TODOS"), usuario_id)
    except InvalidTargetError as error:
        return jsonify({"error": str(error)}), 400
    except ActiveJobError as error:
        return jsonify({
            "error": str(error),
            "job": error.job.to_dict(),
        }), 409
    except QueueUnavailableError as error:
        return jsonify({
            "error": str(error),
            "job": error.job.to_dict(),
        }), 503

    response = jsonify({
        "message": "Sincronização SPDATA adicionada à fila.",
        "job": job.to_dict(),
    })
    response.status_code = 202
    response.headers["Location"] = f"/admin/spdata-sync/jobs/{job.id}"
    response.headers["Cache-Control"] = "no-store"
    return response


@spdata_sync_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("admin")
def listar():
    try:
        limit = min(max(int(request.args.get("limit", 20)), 1), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Paginação inválida."}), 400

    response = jsonify(listar_jobs(limit=limit, offset=offset))
    response.headers["Cache-Control"] = "no-store"
    return response, 200


@spdata_sync_bp.route("/<int:job_id>", methods=["GET"])
@jwt_required()
@roles_required("admin")
def detalhe(job_id):
    job = buscar_job(job_id)
    if not job:
        return jsonify({"error": "Sincronização não encontrada."}), 404

    response = jsonify({"job": job.to_dict()})
    response.headers["Cache-Control"] = "no-store"
    return response, 200
