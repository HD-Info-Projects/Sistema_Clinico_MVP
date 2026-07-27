from flask import (
    Blueprint,
    current_app,
    request,
    jsonify
)

from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.orm import joinedload
from src.security.decorators import roles_required

from src.controllers.login_controller import LoginController
from src.models.usuario_model import Usuario

from src.settings.extensions import db, limiter
from src.services.medicos_spdata_service import (
    buscar_medicos_spdata,
    normalizar_texto,
    criar_usuario_medico_spdata
)

login_bp = Blueprint('login', __name__, url_prefix="/login")
controller = LoginController()


def _login_email_rate_limit_key():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip().lower()

    if email:
        return f"login-email:{email[:255]}"

    return f"login-email-ip:{request.remote_addr or 'unknown'}"


def _login_ip_rate_limit():
    return current_app.config.get("LOGIN_RATE_LIMIT_IP", "10 per minute")


def _login_email_rate_limit():
    return current_app.config.get("LOGIN_RATE_LIMIT_EMAIL", "5 per minute")


@login_bp.route("/auth", methods=["POST"])
@limiter.limit(_login_ip_rate_limit)
@limiter.limit(_login_email_rate_limit, key_func=_login_email_rate_limit_key)
def login():
    try:
        data = request.get_json(silent=True) or {}
        email = data.get("email")
        senha = data.get("senha")

        if not email or not senha:
            return jsonify({"error": "Campos obrigatórios: email, senha"}), 400

        token = controller.generate_JWT_usuario(email, senha)

        if not token:
            return jsonify({"error": "Credenciais inválidas"}), 401

        return jsonify(access_token=token), 200

    except Exception:
        current_app.logger.exception("Erro inesperado no login")
        return jsonify({"error": "Erro interno ao realizar login"}), 500


@login_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    try:
        usuario_id = int(get_jwt_identity())
        usuario = (
            db.session.query(Usuario)
            .options(joinedload(Usuario.medico))
            .filter(Usuario.id == usuario_id)
            .first()
        )

        if not usuario:
            return jsonify({"error": "Não autorizado"}), 401

        return jsonify({
            "id": usuario.id,
            "email": usuario.email,
            "nome_completo": usuario.nome_completo,
            "role": usuario.role,
            "crm": usuario.medico.crm_atendimento_spdata if usuario.medico else None,
            "especialidade": usuario.medico.especialidade if usuario.medico else None,
        }), 200

    except Exception:
        current_app.logger.exception("Erro ao carregar usuário autenticado")
        return jsonify({"error": "Erro interno ao carregar sessão"}), 500


@login_bp.route("/register", methods=["POST"])
@jwt_required()
@roles_required("admin")
def register_medic():
    try:
        data = request.get_json(silent=True) or {}

        campos_obrigatorios = [
            "email_medico",
            "senha_medico",
            "nome_completo_medico",
            "CNPJ_CPF",
        ]
        campos_faltando = [
            campo for campo in campos_obrigatorios
            if not data.get(campo)
        ]

        if campos_faltando:
            return jsonify({
                "error": "Campos obrigatórios ausentes",
                "fields": campos_faltando,
            }), 400
        
        email = data["email_medico"]
        senha = data["senha_medico"]
        nome_completo = data["nome_completo_medico"]
        cpf_cnpj = data["CNPJ_CPF"]
        crm_atendimento_spdata = data.get("crm_atendimento_spdata")

        medicos_spdata = buscar_medicos_spdata(cpf=cpf_cnpj)
        if not medicos_spdata:
            medicos_spdata = buscar_medicos_spdata(nome=nome_completo)

        if not medicos_spdata:
            return jsonify({"error": "Médico não foi encontrado no SPDATA"}), 404

        if len(medicos_spdata) > 1:
            nome_normalizado = normalizar_texto(nome_completo)
            medicos_mesmo_nome = [
                medico
                for medico in medicos_spdata
                if normalizar_texto(medico.get("NOME")) == nome_normalizado
            ]
            if medicos_mesmo_nome:
                medicos_spdata = medicos_mesmo_nome

        if len(medicos_spdata) > 1:
            return jsonify({
                "error": "Mais de um médico encontrado no SPDATA",
                "medicos": [
                    {
                        "id": medico.get("ID"),
                        "nome": medico.get("NOME"),
                        "cpf": medico.get("CPF") or medico.get("CNPJ_CPF"),
                        "crm": medico.get("OLD_CRM"),
                        "crm_atendimento_spdata": medico.get("CRM_ATENDIMENTO_SPDATA"),
                    }
                    for medico in medicos_spdata
                ]
            }), 409

        resultado = criar_usuario_medico_spdata(
            medicos_spdata[0],
            email=email,
            senha=senha,
            crm_atendimento_spdata=crm_atendimento_spdata,
        )

        return jsonify({
            "msg": "Médico cadastrado com sucesso!",
            "usuario": resultado["usuario"]._to_dict(),
            "medico": resultado["medico"]._to_dict(),
        }), 201
        
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
