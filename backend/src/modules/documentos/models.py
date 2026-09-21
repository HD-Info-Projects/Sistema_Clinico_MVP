"""Medical document models exposed through the documentos module.

The SQLAlchemy class remains in the legacy model file to avoid Alembic metadata
changes during the modular migration.
"""

from src.models.documento_medico_model import (
    DocumentoMedico,
    TIPO_ATESTADO,
    TIPO_ENCAMINHAMENTO,
    TIPO_SOLICITACAO_OPME,
    TIPO_SOLICITACAO_PROCEDIMENTO,
    TIPOS_DOCUMENTO_VALIDOS,
)

__all__ = [
    "DocumentoMedico",
    "TIPO_ATESTADO",
    "TIPO_ENCAMINHAMENTO",
    "TIPO_SOLICITACAO_OPME",
    "TIPO_SOLICITACAO_PROCEDIMENTO",
    "TIPOS_DOCUMENTO_VALIDOS",
]
