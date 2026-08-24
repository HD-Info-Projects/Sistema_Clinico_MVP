from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.security.decorators import roles_required

from src.services.padroes_medico_service import resolver_medico_alvo

from src.settings.extensions import db
from src.models.model_padroes_solicitacoes.modelo_anamnese_model import ModeloAnamnese

padrao_medico_anamnese_bp = Blueprint(
    "padrao_medico_anamnese",
    __name__,
    url_prefix="/padrao_medico_anamnese",
)


def _get_padrao_do_medico(id_padrao, medico_id):
    return (
        db.session.query(ModeloAnamnese)
        .filter(
            ModeloAnamnese.id == id_padrao,
            ModeloAnamnese.medico_id == medico_id
        )
        .first()
    )


@padrao_medico_anamnese_bp.route("/criar", methods=["POST"])
@jwt_required()
@roles_required("medico", "admin")
def create_padrao_medico_anamnese():
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        data = request.get_json() or {}
        nome_modelo = (data.get("nome_modelo") or "").strip()
        conteudo = (data.get("conteudo") or "").strip()

        if not nome_modelo:
            return jsonify({"error": "Campo nome_modelo é obrigatório"}), 400

        if not conteudo:
            return jsonify({"error": "Campo conteudo é obrigatório"}), 400

        new_padrao = ModeloAnamnese(nome_modelo, medico_id, conteudo)
        db.session.add(new_padrao)
        db.session.commit()

        return jsonify(new_padrao._to_dict()), 201

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_anamnese_bp.route("/lista", methods=["GET"])
@jwt_required()
@roles_required("medico", "admin")
def lista_padroes_medicos_anamnese():
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        lista_padroes = (
            db.session.query(ModeloAnamnese)
            .filter(ModeloAnamnese.medico_id == medico_id)
            .all()
        )

        return jsonify({
            "padroes_anamnese": [
                padrao._to_dict()
                for padrao in lista_padroes
            ]
        }), 200

    except Exception:
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_anamnese_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("medico", "admin")
def detalhes_padrao_medico_anamnese(id: int):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão médico de anamnese não encontrado"}), 404

        return jsonify(padrao._to_dict()), 200

    except Exception:
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_anamnese_bp.route("/editar/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
@roles_required("medico", "admin")
def editar_padrao_medico_anamnese(id: int):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão médico de anamnese não encontrado"}), 404

        data = request.get_json() or {}
        nome_modelo = (data.get("nome_modelo") or "").strip()

        if not nome_modelo:
            return jsonify({"error": "Campo nome_modelo é obrigatório"}), 400

        padrao.nome_modelo = nome_modelo

        if "conteudo" in data:
            conteudo = (data.get("conteudo") or "").strip()
            if not conteudo:
                return jsonify({"error": "Campo conteudo não pode ser vazio"}), 400
            padrao.conteudo = conteudo

        db.session.commit()

        return jsonify(padrao._to_dict()), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_anamnese_bp.route("/deletar/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("medico", "admin")
def deletar_padrao_medico_anamnese(id: int):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão médico de anamnese não encontrado"}), 404

        db.session.delete(padrao)
        db.session.commit()

        return jsonify({"message": "Padrão médico de anamnese deletado com sucesso"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500
