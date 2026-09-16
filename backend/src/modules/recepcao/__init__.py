"""Recepcao module.

Orquestra busca/criação de pacientes e atendimentos da recepção, mantendo os
contratos SPDATA existentes durante a migração modular.
"""

from src.modules.recepcao.routes import recepcao_bp

__all__ = ["recepcao_bp"]
