from flask import Flask, jsonify
from flask_limiter.errors import RateLimitExceeded
from .settings.config import Config
from .settings.extensions import db, migrate, jwt, cors, limiter

from src.commands.exames_commands import importar_exames_spdata_command
from src.commands.convenios_commands import (
    exportar_logos_tiss_command,
    importar_convenios_spdata_command,
)
from src.commands.especialidades_commands import importar_especialidades_spdata_command
from src.commands.medicos_commands import registrar_medico_spdata_command
from src.commands.usuarios_commands import registrar_admin_command, registrar_recepcao_command
from src.commands.unidades_commands import (
    criar_unidade_command,
    listar_unidades_command,
    vincular_unidade_usuario_command,
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(_error):
        return jsonify({
            "error": "Muitas tentativas de login. Aguarde alguns minutos e tente novamente."
        }), 429

    app.cli.add_command(importar_exames_spdata_command)
    app.cli.add_command(importar_convenios_spdata_command)
    app.cli.add_command(exportar_logos_tiss_command)
    app.cli.add_command(importar_especialidades_spdata_command)
    app.cli.add_command(registrar_medico_spdata_command)
    app.cli.add_command(registrar_admin_command)
    app.cli.add_command(registrar_recepcao_command)
    app.cli.add_command(criar_unidade_command)
    app.cli.add_command(listar_unidades_command)
    app.cli.add_command(vincular_unidade_usuario_command)

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
    from src.routes.no_show_route import no_show_bp
    from src.routes.retencao_exames_route import retencao_exames_bp
    from src.routes.tts_route import tts_bp
    from src.routes.documentos_medicos_route import documentos_medicos_bp
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
    app.register_blueprint(no_show_bp)
    app.register_blueprint(retencao_exames_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(documentos_medicos_bp)
    app.register_blueprint(unidades_bp)

    return app
