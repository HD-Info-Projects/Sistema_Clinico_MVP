"""Agenda module: agenda média, check-in e no-show.

Reúne os blueprints de agenda médica (médico), check-in (recepção) e
no-show (recepção) que antes viviam em src.routes. O check-in é
auto-contido em modules/agenda/check_in.py por ler diretamente o
Firebird do SPDATA.
"""

from src.modules.agenda.check_in import check_in_bp
from src.modules.agenda.routes import agenda_medica_bp, no_show_bp

__all__ = ["agenda_medica_bp", "check_in_bp", "no_show_bp"]