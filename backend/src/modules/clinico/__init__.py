"""Clinical module.

Centraliza prontuário, modelos médicos e facades do domínio clínico sem
alterar os contratos públicos das rotas legadas.
"""

from src.modules.clinico.routes import (
    padrao_medico_anamnese_bp,
    padrao_medico_documento_bp,
    padrao_medico_exame_bp,
    padrao_medico_orientacao_exame_bp,
    padrao_medico_receita_bp,
    prontuario_bp,
)

__all__ = [
    "padrao_medico_anamnese_bp",
    "padrao_medico_documento_bp",
    "padrao_medico_exame_bp",
    "padrao_medico_orientacao_exame_bp",
    "padrao_medico_receita_bp",
    "prontuario_bp",
]
