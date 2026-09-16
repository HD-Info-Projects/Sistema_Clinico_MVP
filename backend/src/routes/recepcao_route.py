"""Compatibility wrapper for the recepcao module routes."""

from src.modules.recepcao.routes import (
    _erro_response,
    _json_body,
    _usuario_id,
    recepcao_bp,
)

__all__ = ["_erro_response", "_json_body", "_usuario_id", "recepcao_bp"]
