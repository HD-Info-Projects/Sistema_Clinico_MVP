"""Compatibility wrapper for LGPD audit routes."""

from src.modules.lgpd.routes import auditoria_bp, listar_eventos_auditoria

__all__ = ["auditoria_bp", "listar_eventos_auditoria"]
