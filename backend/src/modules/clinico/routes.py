"""Clinical route facade.

The large prontuario and modelo_medico blueprints remain in their legacy
modules during this migration step, but the application registry imports
them through this clinical domain module.
"""

from src.routes.modelo_orientacao_exame_route import padrao_medico_orientacao_exame_bp
from src.routes.modelo_solicitacao_anamnese_route import padrao_medico_anamnese_bp
from src.routes.modelo_solicitacao_exames_route import padrao_medico_exame_bp
from src.routes.modelo_solicitacao_medicos_route import padrao_medico_receita_bp
from src.routes.prontuario_route import prontuario_bp

__all__ = [
    "padrao_medico_anamnese_bp",
    "padrao_medico_exame_bp",
    "padrao_medico_orientacao_exame_bp",
    "padrao_medico_receita_bp",
    "prontuario_bp",
]
