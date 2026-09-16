"""Compatibility wrapper for the usuarios module routes."""

from src.modules.usuarios.routes import (
    _medico_spdata_to_dict,
    _usuario_admin_dict,
    usuarios_bp,
)

__all__ = ["usuarios_bp", "_medico_spdata_to_dict", "_usuario_admin_dict"]
