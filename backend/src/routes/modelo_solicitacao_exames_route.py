from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.security.decorators import roles_required

from src.settings.extensions import db
from src.models.auditoria_model import AcaoAuditoria
from src.models.model_mydsystem.med_exames_model import Exame
from src.models.model_padroes_solicitacoes.modelo_exame_model import ModeloExame
from src.models.model_padroes_solicitacoes.exames_para_modelo_exame_model import (
    ExamesDoModelo,
)
from src.services.auditoria_service import registrar_auditoria
from src.services.padroes_medico_service import resolver_medico_alvo

padrao_medico_exame_bp = Blueprint(
    "padrao_medico_exame",
    __name__,
    url_prefix="/padrao_medico_exame",
)


def _padrao_medico_exame_to_dict(padrao):
    return {
        **padrao._to_dict(),
        "exames": [exame._to_dict() for exame in padrao.exames],
    }


def _get_padrao_do_medico(id_padrao, medico_id):
    return (
        db.session.query(ModeloExame)
        .filter(
            ModeloExame.id == id_padrao,
            ModeloExame.medico_id == medico_id,
        )
        .first()
    )


def _get_exame_do_medico(id_exame, medico_id):
    return (
        db.session.query(ExamesDoModelo)
        .join(
            ModeloExame,
            ExamesDoModelo.id_modelo_solicitacao_exame == ModeloExame.id,
        )
        .filter(
            ExamesDoModelo.id == id_exame,
            ModeloExame.medico_id == medico_id,
        )
        .first()
    )


def _get_exame_catalogo(data):
    valor = data.get("exame_id") if "exame_id" in data else data.get("exameId")
    if valor is None or valor == "":
        return None, None

    try:
        exame_id = int(valor)
    except (TypeError, ValueError):
        raise ValueError("exame_id inválido")

    if exame_id <= 0:
        raise ValueError("exame_id inválido")

    exame = db.session.get(Exame, exame_id)
    if not exame:
        raise ValueError("exame_id não encontrado")

    return exame_id, exame


def _auditar_modelo_exame(acao, modelo_id, medico_id, detalhe):
    registrar_auditoria(
        acao,
        entidade="padrao_medico_exame",
        entidade_id=modelo_id,
        usuario_id=medico_id,
        descricao=f"Modelo médico de exame {detalhe}.",
    )


@padrao_medico_exame_bp.route("/criar", methods=["POST"])
@jwt_required()
@roles_required("medico", "admin")
def create_padrao_medico_exame():
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        data = request.get_json() or {}
        nome_modelo = (data.get("nome_modelo") or "").strip()

        if not nome_modelo:
            return jsonify({"error": "Campo nome_modelo é obrigatório"}), 400

        new_padrao = ModeloExame(nome_modelo, medico_id)
        db.session.add(new_padrao)
        db.session.commit()
        _auditar_modelo_exame(
            AcaoAuditoria.CRIOU_MODELO_MEDICO,
            new_padrao.id,
            medico_id,
            "criado",
        )

        return jsonify(new_padrao._to_dict()), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_exame_bp.route(
    "/add_exame/<int:id_padrao_medico_exame>", methods=["POST"]
)
@jwt_required()
@roles_required("medico", "admin")
def add_exame_padrao_medico_exame(id_padrao_medico_exame):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id_padrao_medico_exame, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão de exames não encontrado"}), 404

        data = request.get_json() or {}
        exame_id, exame_catalogo = _get_exame_catalogo(data)
        nome_exame = (data.get("nome_exame") or "").strip()
        if not nome_exame and exame_catalogo:
            nome_exame = exame_catalogo.nome

        if not nome_exame:
            return jsonify({"error": "Campo nome_exame é obrigatório"}), 400

        new_exame = ExamesDoModelo(nome_exame, id_padrao_medico_exame, exame_id=exame_id)
        db.session.add(new_exame)
        db.session.commit()
        _auditar_modelo_exame(
            AcaoAuditoria.EDITOU_MODELO_MEDICO,
            id_padrao_medico_exame,
            medico_id,
            "editado: exame adicionado",
        )

        return jsonify(new_exame._to_dict()), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_exame_bp.route("/lista", methods=["GET"])
@jwt_required()
@roles_required("medico", "admin")
def lista_padroes_medicos_exame():
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        lista = (
            db.session.query(ModeloExame)
            .filter(ModeloExame.medico_id == medico_id)
            .all()
        )

        return jsonify({"padroes_exames": [_padrao_medico_exame_to_dict(p) for p in lista]}), 200

    except Exception:
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_exame_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("medico", "admin")
def detalhes_padrao_medico_exame(id):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão de exames não encontrado"}), 404

        return jsonify(_padrao_medico_exame_to_dict(padrao)), 200

    except Exception:
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_exame_bp.route("/editar/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
@roles_required("medico", "admin")
def editar_padrao_medico_exame(id):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão de exames não encontrado"}), 404

        data = request.get_json() or {}
        nome_modelo = (data.get("nome_modelo") or "").strip()

        if not nome_modelo:
            return jsonify({"error": "Campo nome_modelo é obrigatório"}), 400

        padrao.nome_modelo = nome_modelo
        db.session.commit()
        _auditar_modelo_exame(
            AcaoAuditoria.EDITOU_MODELO_MEDICO,
            padrao.id,
            medico_id,
            "editado",
        )

        return jsonify(_padrao_medico_exame_to_dict(padrao)), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_exame_bp.route("/editar_exame/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
@roles_required("medico", "admin")
def editar_exame_padrao_medico_exame(id):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        exame = _get_exame_do_medico(id, medico_id)

        if not exame:
            return jsonify({"error": "Exame não encontrado"}), 404

        data = request.get_json() or {}
        campos_atualizados = False

        if "exame_id" in data or "exameId" in data:
            exame_id, exame_catalogo = _get_exame_catalogo(data)
            exame.exame_id = exame_id
            campos_atualizados = True

            if exame_catalogo and "nome_exame" not in data:
                exame.nome_exame = exame_catalogo.nome

        if "nome_exame" in data:
            nome_exame = (data.get("nome_exame") or "").strip()
            if not nome_exame:
                return jsonify({"error": "Campo nome_exame não pode ser vazio"}), 400
            exame.nome_exame = nome_exame
            campos_atualizados = True

        if not campos_atualizados:
            return jsonify({"error": "Nenhum campo válido informado"}), 400

        db.session.commit()
        _auditar_modelo_exame(
            AcaoAuditoria.EDITOU_MODELO_MEDICO,
            exame.id_modelo_solicitacao_exame,
            medico_id,
            "editado: exame atualizado",
        )
        return jsonify(exame._to_dict()), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_exame_bp.route("/deletar/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("medico", "admin")
def deletar_padrao_medico_exame(id):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão de exames não encontrado"}), 404

        db.session.delete(padrao)
        db.session.commit()
        _auditar_modelo_exame(
            AcaoAuditoria.EXCLUIU_MODELO_MEDICO,
            id,
            medico_id,
            "excluído",
        )

        return jsonify({"message": "Padrão de exames deletado com sucesso"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_exame_bp.route("/deletar_exame/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("medico", "admin")
def deletar_exame_padrao_medico_exame(id):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        exame = _get_exame_do_medico(id, medico_id)

        if not exame:
            return jsonify({"error": "Exame não encontrado"}), 404

        modelo_id = exame.id_modelo_solicitacao_exame
        db.session.delete(exame)
        db.session.commit()
        _auditar_modelo_exame(
            AcaoAuditoria.EDITOU_MODELO_MEDICO,
            modelo_id,
            medico_id,
            "editado: exame excluído",
        )

        return jsonify({"message": "Exame deletado com sucesso"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500
