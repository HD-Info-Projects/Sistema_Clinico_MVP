"""Compatibility wrapper for the documentos module routes."""

from src.modules.documentos.routes import documentos_medicos_bp, parse_ids

__all__ = ["documentos_medicos_bp", "parse_ids"]
