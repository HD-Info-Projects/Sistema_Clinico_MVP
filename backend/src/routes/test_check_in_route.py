from datetime import date
from types import SimpleNamespace

import pytest

from src.routes.check_in_route import (
    buscar_agendamentos_firebird,
    filtrar_rows_por_tipo,
    item_para_frontend,
    tipo_procedimento_row,
)
from src.services.spdata_agenda_service import buscar_agenda_spdata


def test_check_in_nao_busca_agenda_sem_codigo_spdata_agenda():
    unidade = SimpleNamespace(id=1, codigo_spdata_agenda=None)

    with pytest.raises(ValueError, match="Unidade sem código SPDATA de agenda configurado"):
        buscar_agendamentos_firebird(date(2026, 8, 20), unidade)


def test_sync_agenda_nao_busca_agenda_sem_codigo_spdata_agenda():
    unidade = SimpleNamespace(id=1, codigo_spdata_agenda="")

    with pytest.raises(ValueError, match="Unidade sem código SPDATA de agenda configurado"):
        buscar_agenda_spdata(date(2026, 8, 20), date(2026, 8, 20), unidade=unidade)


def test_classifica_tipo_procedimento_por_codigo_tuss():
    assert tipo_procedimento_row({"COD_PROCEDIMENTO_SPDATA": "10101012"}) == "consulta"
    assert tipo_procedimento_row({"COD_PROCEDIMENTO_SPDATA": "40901300"}) == "exame"
    assert tipo_procedimento_row({"COD_PROCEDIMENTO_SPDATA": "0"}) == "nao-informado"
    assert tipo_procedimento_row({"COD_PROCEDIMENTO_SPDATA": None}) == "nao-informado"


def test_filtra_rows_por_tipo_procedimento():
    rows = [
        {"COD_PROCEDIMENTO_SPDATA": "10101012"},
        {"COD_PROCEDIMENTO_SPDATA": "40901300"},
        {"COD_PROCEDIMENTO_SPDATA": "0"},
    ]

    assert filtrar_rows_por_tipo(rows, "consulta") == [rows[0]]
    assert filtrar_rows_por_tipo(rows, "exame") == [rows[1]]
    assert filtrar_rows_por_tipo(rows, "nao-informado") == [rows[2]]


def test_item_check_in_expoe_tipo_procedimento():
    item = item_para_frontend(
        {"REGISTRO": "123", "COD_PROCEDIMENTO_SPDATA": "40901300"},
        {},
        {},
        {},
        SimpleNamespace(id=1),
    )

    assert item["codigoProcedimentoSpdata"] == "40901300"
    assert item["tipoProcedimento"] == "exame"
    assert item["tipoProcedimentoLabel"] == "Exame"
