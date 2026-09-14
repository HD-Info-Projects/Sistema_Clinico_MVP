"""Compatibility wrapper for the procedimentos module."""

from src.modules.procedimentos.routes import procedimentos_bp
from src.modules.procedimentos.service import (
    filtro_busca_procedimentos,
    procedimento_para_dict,
)

__all__ = [
    "procedimentos_bp",
    "filtro_busca_procedimentos",
    "procedimento_para_dict",
]
