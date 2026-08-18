import logging
import time

from flask import Flask, g, jsonify, request
from flask_limiter.errors import RateLimitExceeded
from .settings.config import Config
from .settings.extensions import db, migrate, jwt, cors, limiter
from .settings.logging_config import REQUEST_ID_HEADER, configure_logging, make_request_id
from .security.jwt_blocklist import is_jti_revoked

from src.commands.exames_commands import importar_exames_spdata_command
from src.commands.procedimentos_commands import importar_procedimentos_spdata_command
from src.commands.convenios_commands import (
    exportar_logos_tiss_command,
    importar_convenios_spdata_command,
)
from src.commands.especialidades_commands import importar_especialidades_spdata_command
from src.commands.medicos_commands import registrar_medico_spdata_command
from src.commands.usuarios_commands import (
    registrar_admin_command,
    registrar_dpo_command,
    registrar_recepcao_command,
)
from src.commands.unidades_commands import (
    criar_unidade_command,
    listar_unidades_command,
    vincular_unidade_usuario_command,
)
from src.commands.lgpd_commands import lgpd_retencao_command

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    configure_logging(app)
    request_logger = logging.getLogger("src.requests")

    if app.config.get("IS_PRODUCTION"):
        missing = [
            key
            for key in ("SECRET_KEY", "JWT_SECRET_KEY", "SQLALCHEMY_DATABASE_URI")
            if not app.config.get(key)
        ]
        if missing:
            raise RuntimeError(
                "Configuração de produção incompleta: " + ", ".join(missing)
            )

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    if app.config.get("CORS_ORIGINS"):
        cors.init_app(app, supports_credentials=True, origins=app.config["CORS_ORIGINS"])
    limiter.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload):
        return is_jti_revoked(jwt_payload.get("jti"))

    @jwt.revoked_token_loader
    def revoked_token_response(_jwt_header, _jwt_payload):
        return jsonify({"error": "Sessão encerrada"}), 401

    @app.before_request
    def prepare_request_logging():
        g.request_started_at = time.perf_counter()
        g.request_id = make_request_id(request.headers.get(REQUEST_ID_HEADER))

    def _should_log_request():
        if not app.config.get("LOG_REQUESTS", True):
            return False

        if request.path == "/" and not app.config.get("LOG_HEALTHCHECKS", False):
            return False

        return True

    def _log_request(response):
        if not _should_log_request():
            return

        started_at = getattr(g, "request_started_at", None)
        duration_ms = None
        if started_at is not None:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        status_code = response.status_code
        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING

        request_logger.log(
            level,
            "request completed",
            extra={
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault(
            REQUEST_ID_HEADER,
            getattr(g, "request_id", None) or make_request_id(),
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
            "img-src 'self' data: blob:; media-src 'self' data: blob:; connect-src 'self'; "
            "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; form-action 'self'",
        )

        if app.config.get("SECURITY_HSTS_ENABLED"):
            max_age = app.config.get("SECURITY_HSTS_MAX_AGE", 31536000)
            response.headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={max_age}; includeSubDomains",
            )

        _log_request(response)
        return response

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(_error):
        return jsonify({
            "error": "Muitas tentativas de login. Aguarde alguns minutos e tente novamente."
        }), 429

    app.cli.add_command(importar_exames_spdata_command)
    app.cli.add_command(importar_procedimentos_spdata_command)
    app.cli.add_command(importar_convenios_spdata_command)
    app.cli.add_command(exportar_logos_tiss_command)
    app.cli.add_command(importar_especialidades_spdata_command)
    app.cli.add_command(registrar_medico_spdata_command)
    app.cli.add_command(registrar_admin_command)
    app.cli.add_command(registrar_dpo_command)
    app.cli.add_command(registrar_recepcao_command)
    app.cli.add_command(criar_unidade_command)
    app.cli.add_command(listar_unidades_command)
    app.cli.add_command(vincular_unidade_usuario_command)
    app.cli.add_command(lgpd_retencao_command)

    # Importações de Models:
    from src.models.atendimentos_model import Atendimento
    from src.models.anamnese_model import Anamnese
    from src.models.evolucoes_medicas_model import EvolucaoMedica
    from src.models.evolucao_medica_versao_model import EvolucaoMedicaVersao
    from src.models.diagnostico_model import Diagnostico
    from src.models.prescricao_model import Prescricao
    from src.models.solicitacao_exame_model import SolicitacaoExame
    from src.models.documento_medico_model import DocumentoMedico
    from src.models.fila_sincronizacao_model import FilaSincronizacao
    from src.models.log_integracao_model import LogIntegracao
    from src.models.auditoria_model import Auditoria
    from src.models.usuario_model import Usuario
    from src.models.medico_model import Medico
    from src.models.unidade_model import Unidade
    from src.models.usuario_unidade_model import UsuarioUnidade

    # Cruzamento:
    from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
    from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
    from src.models.model_mydsystem.med_atendimentos_model import MedAtendimentos
    from src.models.model_mydsystem.med_spdata_convenios_model import MedSpdataConvenio
    from src.models.model_mydsystem.med_spdata_especialidades_model import MedSpdataEspecialidade
    from src.models.model_mydsystem.med_procedimentos_model import Procedimento

    # Modelos Médicos:
    from src.models.model_padroes_solicitacoes.modelo_receita_model import ModeloReceita
    from src.models.model_padroes_solicitacoes.medicamentos_para_modelo_receita_model import Medicamentos
    from src.models.model_padroes_solicitacoes.modelo_exame_model import ModeloExame
    from src.models.model_padroes_solicitacoes.exames_para_modelo_exame_model import ExamesDoModelo
    from src.models.model_padroes_solicitacoes.modelo_anamnese_model import ModeloAnamnese
    from src.models.model_padroes_solicitacoes.modelo_orientacao_exame_model import ModeloOrientacaoExame

    from src.models.model_mydsystem.med_exames_model import Exame

    # Importações de Routes/Rotas:
    from .routes import register_routes
    register_routes(app)

    from src.routes.login_route import login_bp
    from src.routes.dashboard_route import dashboard_bp
    from src.routes.check_in_route import check_in_bp
    from src.routes.prontuario_route import prontuario_bp
    from src.routes.modelo_solicitacao_medicos_route import padrao_medico_receita_bp
    from src.routes.modelo_solicitacao_exames_route import padrao_medico_exame_bp
    from src.routes.modelo_solicitacao_anamnese_route import padrao_medico_anamnese_bp
    from src.routes.modelo_orientacao_exame_route import padrao_medico_orientacao_exame_bp
    from src.routes.agenda_medica_route import agenda_medica_bp
    from src.routes.exames_route import exames_bp
    from src.routes.procedimentos_route import procedimentos_bp
    from src.routes.no_show_route import no_show_bp
    from src.routes.retencao_exames_route import retencao_exames_bp
    from src.routes.tts_route import tts_bp
    from src.routes.documentos_medicos_route import documentos_medicos_bp
    from src.routes.auditoria_route import auditoria_bp
    from src.routes.unidades_route import unidades_bp

    app.register_blueprint(login_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(check_in_bp)
    app.register_blueprint(prontuario_bp)
    app.register_blueprint(padrao_medico_receita_bp)
    app.register_blueprint(padrao_medico_exame_bp)
    app.register_blueprint(padrao_medico_anamnese_bp)
    app.register_blueprint(padrao_medico_orientacao_exame_bp)
    app.register_blueprint(agenda_medica_bp)
    app.register_blueprint(exames_bp)
    app.register_blueprint(procedimentos_bp)
    app.register_blueprint(no_show_bp)
    app.register_blueprint(retencao_exames_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(documentos_medicos_bp)
    app.register_blueprint(auditoria_bp)
    app.register_blueprint(unidades_bp)

    return app
