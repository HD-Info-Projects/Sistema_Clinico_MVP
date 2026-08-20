from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.model_padroes_solicitacoes.modelo_orientacao_exame_model import (
    ModeloOrientacaoExame,
)
from src.security.decorators import roles_required
from src.settings.extensions import db


padrao_medico_orientacao_exame_bp = Blueprint(
    "padrao_medico_orientacao_exame",
    __name__,
    url_prefix="/padrao_medico_orientacao_exame",
)


def _get_medico_id():
    return int(get_jwt_identity())


def _get_padrao_do_medico(id_padrao, medico_id):
    return (
        db.session.query(ModeloOrientacaoExame)
        .filter(
            ModeloOrientacaoExame.id == id_padrao,
            ModeloOrientacaoExame.medico_id == medico_id,
        )
        .first()
    )


@padrao_medico_orientacao_exame_bp.route("/criar", methods=["POST"])
@jwt_required()
@roles_required("medico")
def create_padrao_medico_orientacao_exame():
    try:
        medico_id = _get_medico_id()
        data = request.get_json() or {}
        nome_modelo = (data.get("nome_modelo") or "").strip()
        conteudo = (data.get("conteudo") or "").strip()

        if not nome_modelo:
            return jsonify({"error": "Campo nome_modelo é obrigatório"}), 400

        if not conteudo:
            return jsonify({"error": "Campo conteudo é obrigatório"}), 400

        novo_padrao = ModeloOrientacaoExame(nome_modelo, medico_id, conteudo)
        db.session.add(novo_padrao)
        db.session.commit()

        return jsonify(novo_padrao._to_dict()), 201

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_orientacao_exame_bp.route("/lista", methods=["GET"])
@jwt_required()
@roles_required("medico")
def lista_padroes_medicos_orientacao_exame():
    try:
        medico_id = _get_medico_id()
        lista_padroes = (
            db.session.query(ModeloOrientacaoExame)
            .filter(ModeloOrientacaoExame.medico_id == medico_id)
            .all()
        )

        return jsonify({
            "padroes_orientacoes_exames": [
                padrao._to_dict()
                for padrao in lista_padroes
            ]
        }), 200

    except Exception:
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_orientacao_exame_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("medico")
def detalhes_padrao_medico_orientacao_exame(id: int):
    try:
        medico_id = _get_medico_id()
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão médico de orientação não encontrado"}), 404

        return jsonify(padrao._to_dict()), 200

    except Exception:
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_orientacao_exame_bp.route("/editar/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
@roles_required("medico")
def editar_padrao_medico_orientacao_exame(id: int):
    try:
        medico_id = _get_medico_id()
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão médico de orientação não encontrado"}), 404

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


@padrao_medico_orientacao_exame_bp.route("/deletar/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("medico")
def deletar_padrao_medico_orientacao_exame(id: int):
    try:
        medico_id = _get_medico_id()
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão médico de orientação não encontrado"}), 404

        db.session.delete(padrao)
        db.session.commit()

        return jsonify({"message": "Padrão médico de orientação deletado com sucesso"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500
