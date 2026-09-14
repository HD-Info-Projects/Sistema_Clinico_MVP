"""Procedure models exposed through the procedimentos module.

The SQLAlchemy class remains in the legacy model file to avoid Alembic metadata
changes during the modular migration.
"""

from src.models.model_mydsystem.med_procedimentos_model import Procedimento

__all__ = ["Procedimento"]
