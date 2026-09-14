"""Compatibility wrapper for the exames module."""

from src.modules.exames.routes import exames_bp
from src.modules.exames.service import (
    exame_para_dict,
    filtro_busca_exames,
)

__all__ = ["exames_bp", "exame_para_dict", "filtro_busca_exames"]
