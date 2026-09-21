from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import decode_token, get_jwt, get_jwt_identity, jwt_required
from sqlalchemy.orm import joinedload, selectinload

from src.models.auditoria_model import AcaoAuditoria
from src.models.usuario_model import Usuario
from src.modules.auth.service import AccountLockedError, LoginController
from src.modules.unidades.service import (
    listar_unidades_ativas_frontend,
    listar_unidades_usuario_frontend,
    vincular_usuario_unidade,
)
from src.security.decorators import active_user_required, roles_required
from src.security.jwt_blocklist import revoke_jti
from src.security.passwords import validate_password_strength
from src.services.auditoria_service import registrar_auditoria
from src.services.medicos_spdata_service import (
    buscar_medicos_spdata,
    criar_usuario_medico_spdata,
    normalizar_texto,
)
from src.settings.extensions import db, limiter


login_bp = Blueprint("login", __name__, url_prefix="/login")
controller = LoginController()


def _login_username_rate_limit_key():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username") or data.get("email") or "").strip().lower()

    if username:
        usuario = (
            db.session.query(Usuario.id, Usuario.login_rate_limit_version)
            .filter(
                (db.func.lower(Usuario.username) == username[:30])
                | (db.func.lower(Usuario.email) == username[:255])
            )
            .first()
        )
        version = usuario.login_rate_limit_version if usuario else 0
        return f"login-username:{username[:255]}:v{version}"

    return f"login-username-ip:{request.remote_addr or 'unknown'}"


def _login_ip_rate_limit():
    return current_app.config.get("LOGIN_RATE_LIMIT_IP", "10 per minute")


def _login_username_rate_limit():
    return current_app.config.get("LOGIN_RATE_LIMIT_EMAIL", "5 per minute")


def _deduct_failed_login(response):
    return response.status_code == 401


@login_bp.route("/auth", methods=["POST"])
@limiter.limit(_login_ip_rate_limit, deduct_when=_deduct_failed_login)
@limiter.limit(
    _login_username_rate_limit,
    key_func=_login_username_rate_limit_key,
    deduct_when=_deduct_failed_login,
)
def login():
    try:
        data = request.get_json(silent=True) or {}
        username = data.get("username") or data.get("email")
        senha = data.get("senha")

        if not username or not senha:
            return jsonify({"error": "Campos obrigatórios: usuário, senha"}), 400

        token = controller.generate_JWT_usuario(username, senha)

        if not token:
            registrar_auditoria(
                AcaoAuditoria.LOGIN_FALHA,
                entidade="usuarios",
                descricao=f"Falha de login para usuario={str(username).strip().lower()[:30]}",
            )
            return jsonify({"error": "Credenciais inválidas"}), 401

        decoded_token = decode_token(token)
        registrar_auditoria(
            AcaoAuditoria.LOGIN_SUCESSO,
            entidade="usuarios",
            entidade_id=int(decoded_token["sub"]),
            usuario_id=int(decoded_token["sub"]),
            descricao="Login realizado com sucesso",
        )

        return jsonify(access_token=token), 200

    except AccountLockedError:
        return jsonify({
            "error": "Conta bloqueada. Solicite o desbloqueio ao administrador."
        }), 423

    except Exception:
        current_app.logger.exception("Erro inesperado no login")
        return jsonify({"error": "Erro interno ao realizar login"}), 500


@login_bp.route("/me", methods=["GET"])
@jwt_required()
@active_user_required()
def me():
    try:
        usuario_id = int(get_jwt_identity())
        usuario = (
            db.session.query(Usuario)
            .options(
                joinedload(Usuario.medico),
                selectinload(Usuario.unidades),
            )
            .filter(Usuario.id == usuario_id)
            .first()
        )

        if not usuario:
            return jsonify({"error": "Não autorizado"}), 401

        if not usuario.ativo or usuario.bloqueado_em:
            return jsonify({"error": "Não autorizado"}), 401

        return jsonify({
            "id": usuario.id,
            "username": usuario.username,
            "email": usuario.email,
            "nome_completo": usuario.nome_completo,
            "role": usuario.role,
            "crm": usuario.medico.crm_atendimento_spdata if usuario.medico else None,
            "especialidade": usuario.medico.especialidade if usuario.medico else None,
            "unidades": (
                listar_unidades_ativas_frontend()
                if usuario.role == "admin"
                else listar_unidades_usuario_frontend(usuario.id)
            ),
        }), 200

    except Exception:
        current_app.logger.exception("Erro ao carregar usuário autenticado")
        return jsonify({"error": "Erro interno ao carregar sessão"}), 500


@login_bp.route("/logout", methods=["POST"])
@jwt_required()
@active_user_required()
def logout():
    usuario_id = int(get_jwt_identity())
    claims = get_jwt()
    revoke_jti(claims.get("jti"), claims.get("exp"))
    registrar_auditoria(
        AcaoAuditoria.LOGOUT,
        entidade="usuarios",
        entidade_id=usuario_id,
        usuario_id=usuario_id,
        descricao="Logout realizado",
    )
    return jsonify({"ok": True}), 200


@login_bp.route("/register", methods=["POST"])
@jwt_required()
@roles_required("admin")
def register_medic():
    try:
        data = request.get_json(silent=True) or {}

        campos_obrigatorios = [
            "senha_medico",
            "nome_completo_medico",
            "CNPJ_CPF",
        ]
        campos_faltando = [
            campo for campo in campos_obrigatorios
            if not data.get(campo)
        ]

        if not data.get("username_medico") and not data.get("email_medico"):
            campos_faltando.append("username_medico")

        if campos_faltando:
            return jsonify({
                "error": "Campos obrigatórios ausentes",
                "fields": campos_faltando,
            }), 400

        username = data.get("username_medico") or data.get("email_medico")
        email = data.get("email_medico")
        senha = data["senha_medico"]
        nome_completo = data["nome_completo_medico"]
        cpf_cnpj = data["CNPJ_CPF"]
        crm_atendimento_spdata = data.get("crm_atendimento_spdata")
        unidade_ids = data.get("unidade_ids") or data.get("unidadeIds") or []
        if isinstance(unidade_ids, (str, int)):
            unidade_ids = [unidade_ids]

        validate_password_strength(senha, current_app.config.get("PASSWORD_MIN_LENGTH", 6))

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
            username=username,
            email=email,
            senha=senha,
            crm_atendimento_spdata=crm_atendimento_spdata,
        )

        for indice, unidade_id in enumerate(unidade_ids):
            vincular_usuario_unidade(
                resultado["usuario"].id,
                int(unidade_id),
                principal=indice == 0,
            )
        db.session.commit()

        return jsonify({
            "msg": "Médico cadastrado com sucesso!",
            "usuario": resultado["usuario"]._to_dict(),
            "medico": resultado["medico"]._to_dict(),
            "unidades": listar_unidades_usuario_frontend(resultado["usuario"].id),
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao cadastrar médico")
        return jsonify({"error": "Erro interno ao cadastrar médico"}), 500
