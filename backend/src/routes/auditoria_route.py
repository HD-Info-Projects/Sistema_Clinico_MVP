from datetime import datetime, time, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.models.auditoria_model import Auditoria
from src.security.decorators import roles_required
from src.settings.extensions import db


auditoria_bp = Blueprint("auditoria", __name__, url_prefix="/auditorias")


def _parse_date(value):
    if not value:
        return None

    return datetime.fromisoformat(str(value)[:10]).date()


@auditoria_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("admin", "dpo", "ti")
def listar_auditorias():
    data_ini = _parse_date(request.args.get("dataIni"))
    data_fim = _parse_date(request.args.get("dataFim"))
    acao = (request.args.get("acao") or "").strip() or None
    entidade = (request.args.get("entidade") or "").strip() or None
    usuario_id = request.args.get("usuarioId", type=int)
    limit = min(max(request.args.get("limit", default=50, type=int) or 50, 1), 200)
    offset = max(request.args.get("offset", default=0, type=int) or 0, 0)

    filtros = []
    if data_ini:
        filtros.append(Auditoria.created_at >= datetime.combine(data_ini, time.min))
    if data_fim:
        filtros.append(Auditoria.created_at < datetime.combine(data_fim + timedelta(days=1), time.min))
    if acao:
        filtros.append(Auditoria.acao == acao)
    if entidade:
        filtros.append(Auditoria.entidade == entidade)
    if usuario_id:
        filtros.append(Auditoria.usuario_id == usuario_id)

    query = (
        select(Auditoria)
        .options(joinedload(Auditoria.usuario))
        .where(*filtros)
        .order_by(Auditoria.created_at.desc())
        .limit(limit + 1)
        .offset(offset)
    )
    eventos = db.session.execute(query).scalars().all()
    has_more = len(eventos) > limit

    return jsonify({
        "items": [evento.to_dict() for evento in eventos[:limit]],
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }), 200
