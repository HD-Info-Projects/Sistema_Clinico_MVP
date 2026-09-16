"""Compatibility wrapper for the atendimentos dashboard routes."""

from src.modules.atendimentos.routes import (
    _data_hora_entrada,
    _item_dashboard,
    dashboard_bp,
    parse_data,
)

__all__ = ["_data_hora_entrada", "_item_dashboard", "dashboard_bp", "parse_data"]
