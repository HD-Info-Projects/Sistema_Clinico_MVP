import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from src.models.auditoria_model import AcaoAuditoria
from src.models.model_padroes_solicitacoes.modelo_documento_medico_model import ModeloDocumentoMedico
from src.services.auditoria_service import registrar_auditoria
from src.services.padroes_medico_service import resolver_medico_alvo
from src.security.decorators import roles_required
from src.settings.extensions import db


padrao_medico_documento_bp = Blueprint(
    "padrao_medico_documento",
    __name__,
    url_prefix="/padrao_medico_documento",
)


def _get_padrao_do_medico(id_padrao, medico_id):
    return db.session.query(ModeloDocumentoMedico).filter(
        ModeloDocumentoMedico.id == id_padrao,
        ModeloDocumentoMedico.medico_id == medico_id,
    ).first()


def _conteudo_tem_texto(conteudo):
    if not isinstance(conteudo, str):
        return False
    texto = re.sub(r"<[^>]*>", " ", conteudo)
    texto = re.sub(r"&(?:nbsp|#160|#xA0);", " ", texto, flags=re.IGNORECASE)
    return bool(texto.strip())


def _dados_documento(data, parcial=False):
    if not isinstance(data, dict):
        return None, "Dados inválidos"

    valores = {}
    for campo in ("nome_modelo", "titulo_documento"):
        if campo in data or not parcial:
            valor = data.get(campo)
            if not isinstance(valor, str) or not valor.strip():
                return None, f"Campo {campo} é obrigatório"
            if len(valor.strip()) > 255:
                return None, f"Campo {campo} excede 255 caracteres"
            valores[campo] = valor.strip()

    if "conteudo" in data or not parcial:
        conteudo = data.get("conteudo")
        if not _conteudo_tem_texto(conteudo):
            return None, "Campo conteudo é obrigatório"
        valores["conteudo"] = conteudo.strip()

    return valores, None


def _auditar(acao, modelo_id, medico_id, detalhe):
    registrar_auditoria(
        acao,
        entidade="padrao_medico_documento",
        entidade_id=modelo_id,
        usuario_id=medico_id,
        descricao=f"Modelo médico de documento {detalhe}.",
    )


@padrao_medico_documento_bp.route("/criar", methods=["POST"])
@jwt_required()
@roles_required("medico", "admin")
def criar_padrao_documento():
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        dados, erro_validacao = _dados_documento(request.get_json() or {})
        if erro_validacao:
            return jsonify({"error": erro_validacao}), 400

        padrao = ModeloDocumentoMedico(
            dados["nome_modelo"],
            dados["titulo_documento"],
            medico_id,
            dados["conteudo"],
        )
        db.session.add(padrao)
        db.session.commit()
        _auditar(AcaoAuditoria.CRIOU_MODELO_MEDICO, padrao.id, medico_id, "criado")
        return jsonify(padrao._to_dict()), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_documento_bp.route("/lista", methods=["GET"])
@jwt_required()
@roles_required("medico", "admin")
def listar_padroes_documentos():
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        lista = db.session.query(ModeloDocumentoMedico).filter(
            ModeloDocumentoMedico.medico_id == medico_id
        ).order_by(ModeloDocumentoMedico.nome_modelo.asc(), ModeloDocumentoMedico.id.asc()).all()
        return jsonify({"padroes_documentos": [padrao._to_dict() for padrao in lista]}), 200
    except Exception:
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_documento_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("medico", "admin")
def obter_padrao_documento(id):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id, medico_id)
        if not padrao:
            return jsonify({"error": "Padrão médico de documento não encontrado"}), 404
        return jsonify(padrao._to_dict()), 200
    except Exception:
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_documento_bp.route("/editar/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
@roles_required("medico", "admin")
def editar_padrao_documento(id):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id, medico_id)
        if not padrao:
            return jsonify({"error": "Padrão médico de documento não encontrado"}), 404
        dados, erro_validacao = _dados_documento(request.get_json() or {}, parcial=True)
        if erro_validacao:
            return jsonify({"error": erro_validacao}), 400
        if not dados:
            return jsonify({"error": "Nenhum campo para atualizar"}), 400
        for campo, valor in dados.items():
            setattr(padrao, campo, valor)
        db.session.commit()
        _auditar(AcaoAuditoria.EDITOU_MODELO_MEDICO, padrao.id, medico_id, "editado")
        return jsonify(padrao._to_dict()), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500


@padrao_medico_documento_bp.route("/deletar/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("medico", "admin")
def deletar_padrao_documento(id):
    try:
        medico_id, erro = resolver_medico_alvo()
        if erro:
            return erro
        padrao = _get_padrao_do_medico(id, medico_id)
        if not padrao:
            return jsonify({"error": "Padrão médico de documento não encontrado"}), 404
        db.session.delete(padrao)
        db.session.commit()
        _auditar(AcaoAuditoria.EXCLUIU_MODELO_MEDICO, id, medico_id, "excluído")
        return jsonify({"message": "Padrão médico de documento deletado com sucesso"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno"}), 500
