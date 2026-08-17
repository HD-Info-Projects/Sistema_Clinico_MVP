from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.security.decorators import roles_required

from src.settings.extensions import db
from src.models.auditoria_model import AcaoAuditoria
from src.models.model_padroes_solicitacoes.modelo_receita_model import ModeloReceita
from src.models.model_padroes_solicitacoes.medicamentos_para_modelo_receita_model import Medicamentos
from src.services.auditoria_service import registrar_auditoria

padrao_medico_receita_bp = Blueprint(
    "padrao_medico_receita",
    __name__,
    url_prefix="/padrao_medico_receita",
)


def _padrao_medico_receita_to_dict(padrao):
    return {
        **padrao._to_dict(),
        "medicamentos": [
            medicamento._to_dict()
            for medicamento in padrao.medicamentos
        ]
    }


def _get_medico_id():
    return int(get_jwt_identity())


def _get_padrao_do_medico(id_padrao, medico_id):
    return (
        db.session.query(ModeloReceita)
        .filter(
            ModeloReceita.id == id_padrao,
            ModeloReceita.medico_id == medico_id
        )
        .first()
    )


def _get_medicamento_do_medico(id_medicamento, medico_id):
    return (
        db.session.query(Medicamentos)
        .join(
            ModeloReceita,
            Medicamentos.id_modelo_solicitacao_receita == ModeloReceita.id
        )
        .filter(
            Medicamentos.id == id_medicamento,
            ModeloReceita.medico_id == medico_id
        )
        .first()
    )


def _auditar_modelo_receita(acao, modelo_id, medico_id, detalhe):
    registrar_auditoria(
        acao,
        entidade="padrao_medico_receita",
        entidade_id=modelo_id,
        usuario_id=medico_id,
        descricao=f"Modelo médico de receita {detalhe}.",
    )


@padrao_medico_receita_bp.route("/criar", methods=["POST"])
@jwt_required()
@roles_required("medico")
def create_padrao_medico_receita():
    try:
        medico_id = _get_medico_id()
        data = request.get_json() or {}
        nome_modelo = (data.get("nome_modelo") or "").strip()

        if not nome_modelo:
            return jsonify({"error": "Campo nome_modelo é obrigatório"}), 400

        new_padrao_medico_receita = ModeloReceita(nome_modelo, medico_id)
        db.session.add(new_padrao_medico_receita)
        db.session.commit()
        _auditar_modelo_receita(
            AcaoAuditoria.CRIOU_MODELO_MEDICO,
            new_padrao_medico_receita.id,
            medico_id,
            "criado",
        )

        return jsonify(new_padrao_medico_receita._to_dict()), 201

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_receita_bp.route("/add_medicamento/<int:id_padrao_medico_receita>", methods=["POST"])
@jwt_required()
@roles_required("medico")
def add_medicamento_padrao_medico_receita(id_padrao_medico_receita: int):
    try:
        medico_id = _get_medico_id()
        padrao = _get_padrao_do_medico(id_padrao_medico_receita, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão médico de receita não encontrado"}), 404

        data = request.get_json() or {}

        nome_medicamento = (data.get("nome_medicamento") or "").strip()
        dosagem = (data.get("dosagem") or "").strip()
        detalhes = data.get("detalhes")

        if not nome_medicamento:
            return jsonify({"error": "Campo nome_medicamento é obrigatório"}), 400

        if not dosagem:
            return jsonify({"error": "Campo dosagem é obrigatório"}), 400

        new_medicamento = Medicamentos(nome_medicamento, dosagem, detalhes, id_padrao_medico_receita)

        db.session.add(new_medicamento)
        db.session.commit()
        _auditar_modelo_receita(
            AcaoAuditoria.EDITOU_MODELO_MEDICO,
            id_padrao_medico_receita,
            medico_id,
            "editado: medicamento adicionado",
        )

        return jsonify(new_medicamento._to_dict()), 201

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


### ROTAS DE GET

@padrao_medico_receita_bp.route("/lista", methods=["GET"])
@jwt_required()
@roles_required("medico")
def lista_padroes_medicos_receita():
    try:
        medico_id = _get_medico_id()
        lista_padroes_receitas = (
            db.session.query(ModeloReceita)
            .filter(ModeloReceita.medico_id == medico_id)
            .all()
        )

        return jsonify({
            "padroes_receitas": [
                _padrao_medico_receita_to_dict(padrao)
                for padrao in lista_padroes_receitas
            ]
        }), 200

    except Exception:
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_receita_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("medico")
def detalhes_padrao_medico_receita(id: int):
    try:
        medico_id = _get_medico_id()
        detalhe_padrao_receita_select = _get_padrao_do_medico(id, medico_id)

        if not detalhe_padrao_receita_select:
            return jsonify({"error": "Padrão médico de receita não encontrado"}), 404

        return jsonify(_padrao_medico_receita_to_dict(detalhe_padrao_receita_select)), 200

    except Exception:
        return jsonify({"error": "Erro interno"}), 500


### ROTAS DE UPDATE

@padrao_medico_receita_bp.route("/editar/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
@roles_required("medico")
def editar_padrao_medico_receita(id: int):
    try:
        medico_id = _get_medico_id()
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão médico de receita não encontrado"}), 404

        data = request.get_json() or {}
        nome_modelo = (data.get("nome_modelo") or "").strip()

        if not nome_modelo:
            return jsonify({"error": "Campo nome_modelo é obrigatório"}), 400

        padrao.nome_modelo = nome_modelo

        db.session.commit()
        _auditar_modelo_receita(
            AcaoAuditoria.EDITOU_MODELO_MEDICO,
            padrao.id,
            medico_id,
            "editado",
        )

        return jsonify(_padrao_medico_receita_to_dict(padrao)), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_receita_bp.route("/editar_medicamento/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
@roles_required("medico")
def editar_medicamento_padrao_medico_receita(id: int):
    try:
        medico_id = _get_medico_id()
        medicamento = _get_medicamento_do_medico(id, medico_id)

        if not medicamento:
            return jsonify({"error": "Medicamento não encontrado"}), 404

        data = request.get_json() or {}
        campos_atualizados = False

        if "nome_medicamento" in data:
            nome_medicamento = (data.get("nome_medicamento") or "").strip()

            if not nome_medicamento:
                return jsonify({"error": "Campo nome_medicamento não pode ser vazio"}), 400

            medicamento.nome_medicamento = nome_medicamento
            campos_atualizados = True

        if "dosagem" in data:
            dosagem = (data.get("dosagem") or "").strip()

            if not dosagem:
                return jsonify({"error": "Campo dosagem não pode ser vazio"}), 400

            medicamento.dosagem = dosagem
            campos_atualizados = True

        if "detalhes" in data:
            medicamento.detalhes = data.get("detalhes")
            campos_atualizados = True

        if not campos_atualizados:
            return jsonify({"error": "Nenhum campo válido informado para atualização"}), 400

        db.session.commit()
        _auditar_modelo_receita(
            AcaoAuditoria.EDITOU_MODELO_MEDICO,
            medicamento.id_modelo_solicitacao_receita,
            medico_id,
            "editado: medicamento atualizado",
        )

        return jsonify(medicamento._to_dict()), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


### ROTAS DE DELETE

@padrao_medico_receita_bp.route("/deletar/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("medico")
def deletar_padrao_medico_receita(id: int):
    try:
        medico_id = _get_medico_id()
        padrao = _get_padrao_do_medico(id, medico_id)

        if not padrao:
            return jsonify({"error": "Padrão médico de receita não encontrado"}), 404

        db.session.delete(padrao)
        db.session.commit()
        _auditar_modelo_receita(
            AcaoAuditoria.EXCLUIU_MODELO_MEDICO,
            id,
            medico_id,
            "excluído",
        )

        return jsonify({"message": "Padrão médico de receita deletado com sucesso"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_receita_bp.route("/deletar_medicamento/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("medico")
def deletar_medicamento_padrao_medico_receita(id: int):
    try:
        medico_id = _get_medico_id()
        medicamento = _get_medicamento_do_medico(id, medico_id)

        if not medicamento:
            return jsonify({"error": "Medicamento não encontrado"}), 404

        modelo_id = medicamento.id_modelo_solicitacao_receita
        db.session.delete(medicamento)
        db.session.commit()
        _auditar_modelo_receita(
            AcaoAuditoria.EDITOU_MODELO_MEDICO,
            modelo_id,
            medico_id,
            "editado: medicamento excluído",
        )

        return jsonify({"message": "Medicamento deletado com sucesso"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500
