from datetime import date
from types import SimpleNamespace

import pytest

from src.routes.check_in_route import buscar_agendamentos_firebird
from src.services.spdata_agenda_service import buscar_agenda_spdata


def test_check_in_nao_busca_agenda_sem_codigo_spdata_agenda():
    unidade = SimpleNamespace(id=1, codigo_spdata_agenda=None)

    with pytest.raises(ValueError, match="Unidade sem código SPDATA de agenda configurado"):
        buscar_agendamentos_firebird(date(2026, 8, 20), unidade)


def test_sync_agenda_nao_busca_agenda_sem_codigo_spdata_agenda():
    unidade = SimpleNamespace(id=1, codigo_spdata_agenda="")

    with pytest.raises(ValueError, match="Unidade sem código SPDATA de agenda configurado"):
        buscar_agenda_spdata(date(2026, 8, 20), date(2026, 8, 20), unidade=unidade)
