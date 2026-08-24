"""Regras de acesso para operações sobre padrões médicos (modelos).

Por padrão toda operação usa o médico autenticado como alvo. Administradores
podem atuar em nome de outro médico informando ``medico_id`` na query string
ou no corpo JSON da requisição.
"""

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity


def resolver_medico_alvo():
    """Resolve o médico alvo da operação atual.

    Sem ``medico_id`` informado, retorna o próprio usuário autenticado
    (comportamento histórico das rotas). Com ``medico_id``, apenas
    administradores podem indicar outro médico, que precisa existir e ter
    papel ``medico``.

    Retorna ``(medico_id, erro)``. ``erro`` é ``None`` quando resolvido com
    sucesso; caso contrário contém uma resposta Flask pronta para retorno.
    """
    try:
        identidade = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None, (jsonify({"error": "Não autorizado"}), 401)

    from src.models.usuario_model import Usuario
    from src.settings.extensions import db

    solicitado = request.args.get("medico_id", type=int)
    if solicitado is None:
        corpo = request.get_json(silent=True) or {}
        bruto = corpo.get("medico_id")

        if bruto is not None:
            try:
                solicitado = int(bruto)
            except (TypeError, ValueError):
                return None, (jsonify({"error": "Campo medico_id inválido"}), 400)

    if not solicitado or solicitado == identidade:
        return identidade, None

    chamador = db.session.get(Usuario, identidade)
    if not chamador or (chamador.role or "") != "admin":
        return (
            None,
            (jsonify({"error": "Sem permissão para gerenciar padrões de outro médico"}), 403),
        )

    alvo = db.session.get(Usuario, solicitado)
    if not alvo or (alvo.role or "") != "medico":
        return None, (jsonify({"error": "Médico não encontrado"}), 404)

    return solicitado, None
