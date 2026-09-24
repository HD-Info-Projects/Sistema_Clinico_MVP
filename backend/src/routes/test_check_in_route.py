from datetime import date, datetime, time
from types import SimpleNamespace

import pytest

from src.modules.agenda import check_in as check_in_module
from src.modules.agenda.check_in import (
    buscar_agendamentos_firebird,
    calcular_idade,
    filtrar_rows_por_tipo,
    item_para_frontend,
    mesclar_agenda_atendimentos,
    tipo_procedimento_row,
)
from src.services import spdata_agenda_service
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
        ("41301307", "exames-procedimentos-especificos"),
        ("41301471", "exames-procedimentos-especificos"),
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


def test_calcular_idade_ignora_data_sentinela_spdata():
    assert calcular_idade(date(1899, 12, 30)) is None


def test_check_in_exibe_horario_de_entrada_sem_perder_horario_agendado():
    agenda = {
        "ID_AGENDAMENTO": 10,
        "REGISTRO": "123",
        "HORA": time(8, 0),
        "ATENDIDO": "N",
    }
    atendimento = {
        "ID_ATENDIMENTO": 20,
        "REGISTRO": "123",
        "HORA": time(8, 37),
        "HORA_ENTRADA": time(8, 37),
        "DATA_HORA_ENTRADA": datetime(2026, 9, 24, 8, 37),
    }

    [row] = mesclar_agenda_atendimentos([agenda], [atendimento])
    item = item_para_frontend(row, {}, {}, {}, SimpleNamespace(id=1))

    assert row["HORA"] == time(8, 0)
    assert row["HORA_ENTRADA"] == time(8, 37)
    assert item["status"] == "em-espera"
    assert item["horario"] == "08:37"
    assert item["horarioAgendado"] == "08:00"
    assert item["horarioEntrada"] == "08:37"


def test_check_in_agendado_sem_entrada_mantem_horario_agendado():
    item = item_para_frontend(
        {
            "ID_AGENDAMENTO": 10,
            "REGISTRO": "123",
            "HORA": time(8, 0),
            "ATENDIDO": "N",
        },
        {},
        {},
        {},
        SimpleNamespace(id=1),
    )

    assert item["status"] == "agendado"
    assert item["horario"] == "08:00"
    assert item["horarioAgendado"] == "08:00"
    assert item["horarioEntrada"] is None


@pytest.mark.parametrize(
    ("modulo", "buscar", "argumentos"),
    [
        (
            check_in_module,
            check_in_module.buscar_agendamentos_firebird,
            (date(2026, 9, 24), SimpleNamespace(codigo_spdata_agenda="16")),
        ),
        (
            spdata_agenda_service,
            spdata_agenda_service.buscar_agenda_spdata,
            (
                date(2026, 9, 24),
                date(2026, 9, 24),
                SimpleNamespace(codigo_spdata_agenda="16"),
            ),
        ),
    ],
)
def test_consultas_agenda_priorizam_nascimento_cadastro(
    monkeypatch,
    modulo,
    buscar,
    argumentos,
):
    class Cursor:
        description = []

        def execute(self, sql, params):
            self.sql = sql

        def fetchall(self):
            return []

    class Connection:
        def __init__(self, cursor):
            self.cursor_instance = cursor

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def cursor(self):
            return self.cursor_instance

    cursor = Cursor()
    monkeypatch.setattr(modulo, "ConnectionDBFireBird", lambda: Connection(cursor))

    buscar(*argumentos)

    assert "LEFT JOIN RICADPAC paciente" in cursor.sql
    assert "NULLIF(paciente.NASC, DATE '1899-12-30')" in cursor.sql
    assert "NULLIF(r.DATA_NASCIMENTO, DATE '1899-12-30')" in cursor.sql
