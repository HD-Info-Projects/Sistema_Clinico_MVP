"""Exam models exposed through the exames module.

The SQLAlchemy class remains in the legacy model file to avoid Alembic metadata
changes during the modular migration.
"""

from src.models.model_mydsystem.med_exames_model import Exame

__all__ = ["Exame"]
