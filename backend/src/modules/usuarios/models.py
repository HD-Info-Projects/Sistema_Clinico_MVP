"""User models exposed through the usuarios module.

The SQLAlchemy classes remain in their legacy model files to avoid Alembic
metadata changes during the modular migration.
"""

from src.models.medico_model import Medico
from src.models.usuario_model import Usuario

__all__ = ["Usuario", "Medico"]
