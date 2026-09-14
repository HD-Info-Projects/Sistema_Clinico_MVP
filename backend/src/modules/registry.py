"""Blueprint registry used while legacy routes are migrated into modules.

This keeps the existing URL contracts unchanged during the modular monolith
transition. Each blueprint still points to its current legacy route module.
"""


def register_modules(app):
    from src.routes.agenda_medica_route import agenda_medica_bp
    from src.routes.auditoria_route import auditoria_bp
    from src.routes.check_in_route import check_in_bp
    from src.routes.dashboard_route import dashboard_bp
    from src.routes.documentos_medicos_route import documentos_medicos_bp
    from src.modules.exames.routes import exames_bp
    from src.routes.login_route import login_bp
    from src.routes.modelo_orientacao_exame_route import padrao_medico_orientacao_exame_bp
    from src.routes.modelo_solicitacao_anamnese_route import padrao_medico_anamnese_bp
    from src.routes.modelo_solicitacao_exames_route import padrao_medico_exame_bp
    from src.routes.modelo_solicitacao_medicos_route import padrao_medico_receita_bp
    from src.routes.no_show_route import no_show_bp
    from src.modules.procedimentos.routes import procedimentos_bp
    from src.routes.prontuario_route import prontuario_bp
    from src.routes.recepcao_route import recepcao_bp
    from src.routes.retencao_exames_route import retencao_exames_bp
    from src.routes.spdata_exames_pacs_route import exames_pacs_bp
    from src.routes.tts_route import tts_bp
    from src.modules.unidades.routes import unidades_bp
    from src.routes.usuarios_route import usuarios_bp

    blueprints = (
        login_bp,
        dashboard_bp,
        check_in_bp,
        prontuario_bp,
        padrao_medico_receita_bp,
        padrao_medico_exame_bp,
        padrao_medico_anamnese_bp,
        padrao_medico_orientacao_exame_bp,
        agenda_medica_bp,
        exames_bp,
        procedimentos_bp,
        no_show_bp,
        retencao_exames_bp,
        tts_bp,
        documentos_medicos_bp,
        usuarios_bp,
        auditoria_bp,
        unidades_bp,
        exames_pacs_bp,
        recepcao_bp,
    )

    for blueprint in blueprints:
        app.register_blueprint(blueprint)
