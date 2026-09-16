"""Blueprint registry used while legacy routes are migrated into modules.

This keeps the existing URL contracts unchanged during the modular monolith
transition. Each blueprint still points to its current legacy route module.
"""


def register_modules(app):
    from src.modules.agenda import agenda_medica_bp, check_in_bp, no_show_bp
    from src.modules.atendimentos import dashboard_bp
    from src.modules.documentos.routes import documentos_medicos_bp
    from src.modules.exames.routes import exames_bp
    from src.modules.auth.routes import login_bp
    from src.modules.clinico import (
        padrao_medico_anamnese_bp,
        padrao_medico_exame_bp,
        padrao_medico_orientacao_exame_bp,
        padrao_medico_receita_bp,
        prontuario_bp,
    )
    from src.modules.procedimentos.routes import procedimentos_bp
    from src.modules.recepcao import recepcao_bp
    from src.modules.lgpd import auditoria_bp, retencao_exames_bp
    from src.integrations.pacs import exames_pacs_bp
    from src.modules.chamadas import tts_bp
    from src.modules.unidades.routes import unidades_bp
    from src.modules.usuarios.routes import usuarios_bp

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
