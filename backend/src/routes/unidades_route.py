import re
import unicodedata

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select

from src.models.unidade_model import Unidade
from src.security.decorators import roles_required
from src.settings.extensions import db


unidades_bp = Blueprint("unidades", __name__, url_prefix="/unidades")


def _normalizar_texto(valor, limite=None):
    if valor is None:
        return None

    valor = str(valor).strip()
    if limite:
        valor = valor[:limite]

    return valor or None


def _normalizar_int(valor):
    if valor is None or valor == "":
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _bool_payload(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in {"1", "true", "sim", "s", "yes"}
    return bool(valor)


def _slug_base(nome):
    texto = unicodedata.normalize("NFKD", nome)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto or "unidade"


def _slug_unico(nome, unidade_id=None):
    base = _slug_base(nome)
    slug = base
    contador = 2

    while True:
        query = select(Unidade).where(Unidade.slug == slug)
        if unidade_id is not None:
            query = query.where(Unidade.id != unidade_id)
        existente = db.session.execute(query).scalars().first()
        if not existente:
            return slug

        slug = f"{base}-{contador}"
        contador += 1


def _aplicar_payload(unidade, data):
    nome = _normalizar_texto(data.get("nome"), 255)
    if not nome:
        return jsonify({"error": "Campos obrigatórios ausentes.", "fields": ["nome"]}), 400

    unidade.nome = nome
    unidade.slug = _slug_unico(nome, unidade_id=unidade.id)
    unidade.codigo_spdata_centro_custo = _normalizar_int(data.get("codigo_spdata_centro_custo"))
    unidade.codigo_spdata_agenda = _normalizar_texto(data.get("codigo_spdata_agenda"), 50)
    unidade.endereco = _normalizar_texto(data.get("endereco"), 500)
    unidade.telefone = _normalizar_texto(data.get("telefone"), 50)
    unidade.ativa = _bool_payload(data.get("ativa", True))
    return None


@unidades_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("admin")
def listar_unidades():
    unidades = db.session.execute(
        select(Unidade).order_by(Unidade.nome.asc())
    ).scalars().all()
    return jsonify([unidade._to_dict() for unidade in unidades]), 200


@unidades_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin")
def criar_unidade():
    data = request.get_json(silent=True) or {}
    unidade = Unidade()
    erro = _aplicar_payload(unidade, data)
    if erro:
        return erro

    db.session.add(unidade)
    db.session.commit()

    return jsonify({
        "message": "Unidade cadastrada com sucesso.",
        "unidade": unidade._to_dict(),
    }), 201


@unidades_bp.route("/<int:unidade_id>", methods=["PUT"])
@jwt_required()
@roles_required("admin")
def atualizar_unidade(unidade_id):
    unidade = db.session.get(Unidade, unidade_id)
    if not unidade:
        return jsonify({"error": "Unidade não encontrada."}), 404

    data = request.get_json(silent=True) or {}
    erro = _aplicar_payload(unidade, data)
    if erro:
        return erro

    db.session.commit()

    return jsonify({
        "message": "Unidade atualizada com sucesso.",
        "unidade": unidade._to_dict(),
    }), 200


@unidades_bp.route("/<int:unidade_id>", methods=["DELETE"])
@jwt_required()
@roles_required("admin")
def inativar_unidade(unidade_id):
    unidade = db.session.get(Unidade, unidade_id)
    if not unidade:
        return jsonify({"error": "Unidade não encontrada."}), 404

    unidade.ativa = False
    db.session.commit()

    return jsonify({
        "message": "Unidade inativada com sucesso.",
        "unidade": unidade._to_dict(),
    }), 200
