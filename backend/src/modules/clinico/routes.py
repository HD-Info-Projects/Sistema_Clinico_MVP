"""Clinical route exports.

The prontuario blueprint now lives in this module package. The modelo_medico
blueprints remain as compatibility imports until they are split further.
"""

from src.routes.modelo_orientacao_exame_route import padrao_medico_orientacao_exame_bp
from src.routes.modelo_solicitacao_anamnese_route import padrao_medico_anamnese_bp
from src.routes.modelo_solicitacao_exames_route import padrao_medico_exame_bp
from src.routes.modelo_solicitacao_medicos_route import padrao_medico_receita_bp
from src.modules.clinico.prontuario import prontuario_bp

__all__ = [
    "padrao_medico_anamnese_bp",
    "padrao_medico_exame_bp",
    "padrao_medico_orientacao_exame_bp",
    "padrao_medico_receita_bp",
    "prontuario_bp",
]
