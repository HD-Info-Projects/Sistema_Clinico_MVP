from flask import current_app, has_request_context, request
from flask_jwt_extended import get_jwt_identity

from src.models.auditoria_model import Auditoria
from src.settings.extensions import db


MAX_DESCRICAO_LENGTH = 1000


def _request_ip():
    if not has_request_context():
        return None

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    return request.remote_addr


def _request_user_agent():
    if not has_request_context():
        return None

    return request.headers.get("User-Agent")


def _usuario_id_atual():
    try:
        identity = get_jwt_identity()
    except Exception:
        return None

    try:
        return int(identity) if identity is not None else None
    except (TypeError, ValueError):
        return None


def _normalizar_acao(acao):
    return acao.value if hasattr(acao, "value") else str(acao)


def _normalizar_descricao(descricao):
    if descricao is None:
        return None


    texto = str(descricao)
    if len(texto) <= MAX_DESCRICAO_LENGTH:
        return texto

    return texto[:MAX_DESCRICAO_LENGTH - 3] + "..."


def registrar_auditoria(
    acao,
    *,
    entidade=None,
    entidade_id=None,
    usuario_id=None,
    medico_id=None,
    descricao=None,
    commit=True,
):
    try:
        evento = Auditoria(
            usuario_id=usuario_id if usuario_id is not None else _usuario_id_atual(),
            medico_id=medico_id,
            acao=_normalizar_acao(acao),
            entidade=entidade,
            entidade_id=entidade_id,
            descricao=_normalizar_descricao(descricao),
            ip=_request_ip(),
            user_agent=_request_user_agent(),
        )
        db.session.add(evento)

        if commit:
            db.session.commit()

        return evento

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Falha ao registrar auditoria LGPD")
        return None
