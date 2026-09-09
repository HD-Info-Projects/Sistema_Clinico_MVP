from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from src.models.medico_model import Medico
from src.models.usuario_model import Usuario
from src.security.decorators import roles_required
from src.security.passwords import validate_password_strength
from src.services.medicos_spdata_service import (
    buscar_medicos_spdata,
    normalizar_int,
    normalizar_texto,
    upsert_usuario_medico_spdata,
)
from src.services.unidades_service import (
    listar_unidades_usuario_frontend,
    normalizar_unidade_ids,
    sincronizar_unidades_usuario,
)
from src.settings.extensions import db


usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

ROLES_VALIDAS = {"medico", "recepcao", "admin"}
ROLES_EXIGEM_UNIDADE = {"medico", "recepcao"}


def _bool_payload(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in {"1", "true", "sim", "s", "yes"}
    return bool(valor)


def _usuario_por_id(usuario_id):
    return (
        db.session.query(Usuario)
        .options(joinedload(Usuario.medico))
        .filter(Usuario.id == usuario_id)
        .first()
    )


def _normalizar_email(valor):
    email = normalizar_texto(valor, 255)
    return email.lower() if email else None


def _email_existente(email, usuario_id=None):
    query = select(Usuario).where(Usuario.email == email)
    if usuario_id is not None:
        query = query.where(Usuario.id != usuario_id)
    return db.session.execute(query).scalars().first()


def _medico_spdata_to_dict(medico):
    return {
        "spdata_id": normalizar_int(medico.get("ID")),
        "nome": normalizar_texto(medico.get("NOME"), 255),
        "documento": normalizar_texto(
            medico.get("CNPJ_CPF") or medico.get("CPF"),
            255,
        ),
        "email": normalizar_texto(
            medico.get("EMAIL_CONSULTORIO") or medico.get("EMAIL"),
            255,
        ),
        "crm": normalizar_texto(medico.get("OLD_CRM"), 20),
        "crm_uf": normalizar_texto(medico.get("OLD_UFCRM") or medico.get("UF"), 2),
        "crm_atendimento_spdata": normalizar_texto(
            medico.get("CRM_ATENDIMENTO_SPDATA") or medico.get("OLD_CRM"),
            50,
        ),
        "especialidade": normalizar_texto(
            medico.get("ESPECIALIDADE_PRINCIPAL"),
            255,
        ),
    }


def _medico_payload(data):
    medico = data.get("medico")
    return medico if isinstance(medico, dict) else {}


def _validar_role(role):
    if role not in ROLES_VALIDAS:
        return jsonify({"error": "Perfil de usuário inválido."}), 400
    return None


def _status_value_error(error):
    mensagem = str(error).lower()
    if "cadastrado" in mensagem or "vinculado" in mensagem or "pertencem" in mensagem:
        return 409
    return 400


def _senha_minima():
    return current_app.config.get("PASSWORD_MIN_LENGTH", 6)


def _payload_unidade_ids(data):
    if "unidade_ids" in data:
        return normalizar_unidade_ids(data.get("unidade_ids"))
    if "unidadeIds" in data:
        return normalizar_unidade_ids(data.get("unidadeIds"))
    return None


def _validar_unidades_role(role, unidade_ids):
    if role in ROLES_EXIGEM_UNIDADE and not unidade_ids:
        raise ValueError("Selecione ao menos uma unidade")


def _usuario_admin_dict(usuario):
    dados = usuario._to_dict()
    unidades = listar_unidades_usuario_frontend(usuario.id) if usuario.id else []
    dados["unidades"] = unidades
    dados["unidade_ids"] = [unidade["id"] for unidade in unidades]
    return dados


def _aplicar_campos_medico(medico, payload):
    campos = {
        "crm": 20,
        "crm_atendimento_spdata": 50,
        "crm_uf": 2,
        "rqe": 30,
        "especialidade": 255,
    }

    for campo, limite in campos.items():
        if campo in payload:
            setattr(medico, campo, normalizar_texto(payload.get(campo), limite))

    if "ativo" in payload:
        medico.ativo = _bool_payload(payload["ativo"])


@usuarios_bp.route("", methods=["GET"])
@jwt_required()
@roles_required("admin")
def listar_usuarios():
    role = request.args.get("role")
    if role and role not in ROLES_VALIDAS:
        return jsonify({"error": "Perfil de usuário inválido."}), 400

    query = (
        db.session.query(Usuario)
        .options(joinedload(Usuario.medico))
        .order_by(Usuario.nome_completo.asc())
    )
    if role:
        query = query.filter(Usuario.role == role)

    return jsonify([_usuario_admin_dict(usuario) for usuario in query.all()]), 200


@usuarios_bp.route("/medicos-spdata", methods=["GET"])
@jwt_required()
@roles_required("admin")
def buscar_medicos_spdata_admin():
    spdata_id = request.args.get("spdata_id", type=int)
    cpf = normalizar_texto(request.args.get("cpf"), 255)
    nome = normalizar_texto(request.args.get("nome"), 255)

    filtros = [spdata_id is not None, bool(cpf), bool(nome)]
    if sum(filtros) != 1:
        return jsonify({"error": "Informe apenas um filtro: spdata_id, cpf ou nome."}), 400

    medicos = buscar_medicos_spdata(spdata_id=spdata_id, cpf=cpf, nome=nome)
    return jsonify([_medico_spdata_to_dict(medico) for medico in medicos]), 200


@usuarios_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("admin")
def criar_usuario():
    data = request.get_json(silent=True) or {}
    role = data.get("role") or "medico"
    erro_role = _validar_role(role)
    if erro_role:
        return erro_role

    try:
        email = _normalizar_email(data.get("email"))
        senha = data.get("senha")
        unidade_ids = _payload_unidade_ids(data) or []

        if not email or not senha:
            return jsonify({"error": "Campos obrigatórios ausentes.", "fields": ["email", "senha"]}), 400

        validate_password_strength(senha, _senha_minima())
        _validar_unidades_role(role, unidade_ids)

        if role == "medico":
            return _criar_medico_spdata(data, email, senha, unidade_ids)

        nome_completo = normalizar_texto(data.get("nome_completo"), 255)
        documento = normalizar_texto(data.get("cnpj_cpf"), 255)
        if not nome_completo or not documento:
            return jsonify({"error": "Campos obrigatórios ausentes.", "fields": ["nome_completo", "cnpj_cpf"]}), 400

        if _email_existente(email):
            return jsonify({"error": "E-mail já cadastrado."}), 409

        usuario = Usuario(
            nome_completo=nome_completo,
            cnpj_cpf=documento,
            email=email,
            senha=senha,
            role=role,
        )
        usuario.ativo = _bool_payload(data.get("ativo", True))

        db.session.add(usuario)
        db.session.flush()
        if unidade_ids:
            sincronizar_unidades_usuario(usuario.id, unidade_ids)
        db.session.commit()

        return jsonify({
            "message": "Usuário cadastrado com sucesso.",
            "usuario": _usuario_admin_dict(usuario),
        }), 201

    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), _status_value_error(error)
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Dados duplicados ou inválidos."}), 409


def _criar_medico_spdata(data, email, senha, unidade_ids):
    payload_medico = _medico_payload(data)
    spdata_id = normalizar_int(payload_medico.get("spdata_id") or data.get("spdata_id"))

    if spdata_id is None:
        return jsonify({"error": "Informe o médico do SPDATA."}), 400

    medicos_spdata = buscar_medicos_spdata(spdata_id=spdata_id)
    if not medicos_spdata:
        return jsonify({"error": "Médico não encontrado no SPDATA."}), 404

    medico_local = db.session.execute(
        select(Medico).where(Medico.spdata_id == spdata_id)
    ).scalars().first()
    medico_spdata = medicos_spdata[0]
    documento = normalizar_texto(medico_spdata.get("CNPJ_CPF") or medico_spdata.get("CPF"), 255)
    usuario_email = _email_existente(email)
    usuario_documento = (
        db.session.execute(select(Usuario).where(Usuario.cnpj_cpf == documento)).scalars().first()
        if documento
        else None
    )

    if usuario_email and (not medico_local or usuario_email.id != medico_local.usuario_id):
        return jsonify({"error": "E-mail já cadastrado."}), 409
    if usuario_documento and (not medico_local or usuario_documento.id != medico_local.usuario_id):
        return jsonify({"error": "CPF/CNPJ já cadastrado para outro usuário."}), 409

    resultado = upsert_usuario_medico_spdata(
        medico_spdata,
        email=email,
        senha=senha,
        crm_atendimento_spdata=payload_medico.get("crm_atendimento_spdata"),
    )
    usuario = resultado["usuario"]
    medico = resultado["medico"]

    usuario.ativo = _bool_payload(data.get("ativo", True))
    medico.ativo = usuario.ativo
    _aplicar_campos_medico(medico, payload_medico)
    medico.ativo = usuario.ativo
    sincronizar_unidades_usuario(usuario.id, unidade_ids)
    db.session.commit()

    criado = resultado["usuario_criado"] or resultado["medico_criado"]
    return jsonify({
        "message": "Médico cadastrado com sucesso." if criado else "Médico atualizado com sucesso.",
        "usuario": _usuario_admin_dict(usuario),
    }), 201 if criado else 200


@usuarios_bp.route("/<int:usuario_id>", methods=["PUT"])
@jwt_required()
@roles_required("admin")
def atualizar_usuario(usuario_id):
    usuario = _usuario_por_id(usuario_id)
    if not usuario:
        return jsonify({"error": "Usuário não encontrado."}), 404

    try:
        data = request.get_json(silent=True) or {}
        role = data.get("role") or usuario.role
        erro_role = _validar_role(role)
        if erro_role:
            return erro_role

        unidade_ids = _payload_unidade_ids(data)
        if unidade_ids is None and role in ROLES_EXIGEM_UNIDADE:
            unidade_ids = [unidade["id"] for unidade in listar_unidades_usuario_frontend(usuario.id)]
        _validar_unidades_role(role, unidade_ids or [])

        email = _normalizar_email(data.get("email")) if "email" in data else usuario.email
        if not email:
            return jsonify({"error": "Informe o e-mail."}), 400
        if _email_existente(email, usuario_id=usuario.id):
            return jsonify({"error": "E-mail já cadastrado."}), 409

        if "nome_completo" in data:
            usuario.nome_completo = normalizar_texto(data.get("nome_completo"), 255) or usuario.nome_completo
        if "cnpj_cpf" in data:
            usuario.cnpj_cpf = normalizar_texto(data.get("cnpj_cpf"), 255) or usuario.cnpj_cpf
        if "senha" in data and data.get("senha"):
            validate_password_strength(data["senha"], _senha_minima())
            usuario.set_senha(data["senha"])
        if "ativo" in data:
            usuario.ativo = _bool_payload(data["ativo"])

        usuario.email = email
        usuario.role = role

        if role == "medico":
            payload_medico = _medico_payload(data)
            if not usuario.medico:
                return jsonify({"error": "Médico sem vínculo SPDATA. Cadastre novamente pelo SPDATA."}), 400

            spdata_id = normalizar_int(payload_medico.get("spdata_id"))
            if spdata_id is not None and spdata_id != usuario.medico.spdata_id:
                return jsonify({"error": "Não é permitido alterar o vínculo SPDATA do médico."}), 400

            _aplicar_campos_medico(usuario.medico, payload_medico)
            usuario.medico.ativo = usuario.ativo
        elif usuario.medico:
            usuario.medico.ativo = False

        if unidade_ids is not None:
            sincronizar_unidades_usuario(usuario.id, unidade_ids)

        db.session.commit()

        return jsonify({
            "message": "Médico atualizado com sucesso." if role == "medico" else "Usuário atualizado com sucesso.",
            "usuario": _usuario_admin_dict(usuario),
        }), 200

    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), _status_value_error(error)
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Dados duplicados ou inválidos."}), 409


@usuarios_bp.route("/<int:usuario_id>", methods=["DELETE"])
@jwt_required()
@roles_required("admin")
def inativar_usuario(usuario_id):
    usuario = _usuario_por_id(usuario_id)
    if not usuario:
        return jsonify({"error": "Usuário não encontrado."}), 404

    usuario.ativo = False
    if usuario.medico:
        usuario.medico.ativo = False

    db.session.commit()

    return jsonify({
        "message": "Médico inativado com sucesso." if usuario.role == "medico" else "Usuário inativado com sucesso.",
        "usuario": _usuario_admin_dict(usuario),
    }), 200
