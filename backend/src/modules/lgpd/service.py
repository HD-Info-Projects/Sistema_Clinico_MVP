from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.models.auditoria_model import Auditoria
from src.services.auditoria_service import registrar_auditoria
from src.services.retencao_exames_service import listar_retencao_exames
from src.settings.extensions import db


def parse_data(valor, default=None):
    if not valor:
        return default

    return datetime.fromisoformat(str(valor)[:10]).date()


def listar_auditorias(params):
    data_ini = parse_data(params.get("dataIni"))
    data_fim = parse_data(params.get("dataFim"))
    acao = (params.get("acao") or "").strip() or None
    entidade = (params.get("entidade") or "").strip() or None
    usuario_id = params.get("usuarioId", type=int)
    limit = min(max(params.get("limit", default=50, type=int) or 50, 1), 200)
    offset = max(params.get("offset", default=0, type=int) or 0, 0)

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

    return {
        "items": [evento.to_dict() for evento in eventos[:limit]],
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }


__all__ = ["listar_auditorias", "listar_retencao_exames", "parse_data", "registrar_auditoria"]
