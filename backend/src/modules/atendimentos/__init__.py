"""Atendimentos module.

Concentra o dashboard do médico e os facades de modelos/serviços do
domínio de atendimento, mantendo os contratos HTTP legados durante a
migração modular.
"""

from src.modules.atendimentos.routes import dashboard_bp

__all__ = ["dashboard_bp"]
