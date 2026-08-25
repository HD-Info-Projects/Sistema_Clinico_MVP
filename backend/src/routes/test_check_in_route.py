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
    casos = [
        ("5001", "consulta"),
        ("10101012", "consulta"),
        ("20000000", "procedimento-ambulatorial"),
        ("30000000", "cirurgia"),
        ("40100000", "metodos-eletrofisiologicos"),
        ("40200000", "endoscopia"),
        ("40300000", "medicina-laboratorial"),
        ("40400000", "medicina-transfusional"),
        ("40500000", "genetica"),
        ("40600000", "anatomia-patologica-citopatologia"),
        ("40700000", "medicina-nuclear"),
        ("40800000", "radiologia-rx"),
        ("40901300", "ultrassonografia-us"),
        ("41000000", "tomografia-computadorizada"),
        ("41100000", "ressonancia-magnetica"),
        ("41200000", "radioterapia"),
        ("41300000", "exames-procedimentos-especificos"),
        ("41400000", "testes-diagnostico"),
        ("41500000", "outros-diagnosticos-terapeuticos"),
        ("41600000", "outros"),
    ]

    for codigo, tipo in casos:
        assert tipo_procedimento_row({"COD_PROCEDIMENTO_SPDATA": codigo}) == tipo

    assert tipo_procedimento_row({"COD_PROCEDIMENTO_SPDATA": "0"}) == "nao-informado"
    assert tipo_procedimento_row({"COD_PROCEDIMENTO_SPDATA": None}) == "nao-informado"


def test_filtra_rows_por_tipo_procedimento():
    rows = [
        {"COD_PROCEDIMENTO_SPDATA": "10101012"},
        {"COD_PROCEDIMENTO_SPDATA": "5001"},
        {"COD_PROCEDIMENTO_SPDATA": "40901300"},
        {"COD_PROCEDIMENTO_SPDATA": "0"},
        {"COD_PROCEDIMENTO_SPDATA": "99999999"},
    ]

    assert filtrar_rows_por_tipo(rows, "consulta") == [rows[0], rows[1]]
    assert filtrar_rows_por_tipo(rows, "ultrassonografia-us") == [rows[2]]
    assert filtrar_rows_por_tipo(rows, "nao-informado") == [rows[3]]
    assert filtrar_rows_por_tipo(rows, "outros") == [rows[4]]


def test_item_check_in_expoe_tipo_procedimento():
    item = item_para_frontend(
        {"REGISTRO": "123", "COD_PROCEDIMENTO_SPDATA": "40901300"},
        {},
        {},
        {},
        SimpleNamespace(id=1),
    )

    assert item["codigoProcedimentoSpdata"] == "40901300"
    assert item["tipoProcedimento"] == "ultrassonografia-us"
    assert item["tipoProcedimentoLabel"] == "Ultrassonografia (US)"
