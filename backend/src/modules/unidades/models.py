"""Unit models exposed through the unidades module.

The SQLAlchemy classes remain in their legacy files for now to avoid Alembic
metadata churn during the migration.
"""

from src.models.unidade_model import Unidade
from src.models.usuario_unidade_model import UsuarioUnidade

__all__ = ["Unidade", "UsuarioUnidade"]
