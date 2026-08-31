from datetime import date, datetime, time
from types import SimpleNamespace

from src.services.spdata_atendimentos_service import (
    agenda_para_frontend,
    agenda_spdata_para_frontend,
    filtrar_agenda_frontend,
    tipo_procedimento_frontend,
)


def test_agenda_para_frontend_expoe_nome_social_sem_substituir_nome_civil():
    spdata = SimpleNamespace(
        id=10,
        spdata_atendimento_id=1001,
        cod_atendimento="A1001",
        id_paciente_spdata=55,
        id_medico_spdata=7,
        unidade_id=1,
        id_convenio_spdata=None,
        id_centro_custo_spdata=203,
        data_atendimento=date(2026, 8, 5),
        hora_entrada=time(9, 30),
        data_hora_entrada=datetime(2026, 8, 5, 9, 30),
        obs_atendimento=None,
        paciente="MARIA NOME CIVIL",
        paciente_nome_social="MARIA NOME SOCIAL",
        sexo="F",
        data_nascimento=None,
        celular=None,
        email=None,
        cpf=None,
        endereco=None,
        dados_spdata={},
    )

    item = agenda_para_frontend(spdata)

    assert item["paciente"]["nome"] == "MARIA NOME CIVIL"
    assert item["paciente"]["nomeSocial"] == "MARIA NOME SOCIAL"


def test_agenda_spdata_para_frontend_expoe_nome_social_sem_substituir_nome_civil():
    agenda = SimpleNamespace(
        id=3,
        spdata_agenda_id=2002,
        registro="R2002",
        id_paciente_spdata=66,
        unidade_id=1,
        id_convenio_spdata=None,
        convenio=None,
        data_agenda=date(2026, 8, 5),
        hora_agenda=time(10, 0),
        obs=None,
        paciente="JOAO NOME CIVIL",
        paciente_nome_social="JOAO NOME SOCIAL",
        data_nascimento=None,
        celular=None,
        telefone=None,
        email=None,
        cpf=None,
        atendido_spdata="S",
    )
    spdata_ref = SimpleNamespace(
        id=11,
        spdata_atendimento_id=-2002,
        id_medico_spdata=8,
        unidade_id=1,
    )

    item = agenda_spdata_para_frontend(agenda, spdata_ref)

    assert item["paciente"]["nome"] == "JOAO NOME CIVIL"
    assert item["paciente"]["nomeSocial"] == "JOAO NOME SOCIAL"


def test_filtro_consultas_medico_inclui_faixa_consulta_e_codigo_5001():
    def item(codigo):
        tipo, label = tipo_procedimento_frontend(codigo)
        return {
            "codigoProcedimentoSpdata": codigo,
            "tipoProcedimento": tipo,
            "tipoProcedimentoLabel": label,
            "paciente": {"nome": "Paciente"},
        }

    filtrados = filtrar_agenda_frontend(
        [
            item("10101012"),
            item("5001"),
            item("40901300"),
            item("40100000"),
            item("41500000"),
        ],
        tipo="consulta",
    )

    assert [item["codigoProcedimentoSpdata"] for item in filtrados] == ["10101012", "5001"]


def test_filtro_agenda_sem_tipo_mantem_todos_codigos_tuss():
    def item(codigo):
        tipo, label = tipo_procedimento_frontend(codigo)
        return {
            "codigoProcedimentoSpdata": codigo,
            "tipoProcedimento": tipo,
            "tipoProcedimentoLabel": label,
            "paciente": {"nome": "Paciente"},
        }

    items = [
        item("10101012"),
        item("41301307"),
        item("41301471"),
        item("40901300"),
        item("41500000"),
    ]

    filtrados = filtrar_agenda_frontend(items)

    assert [item["codigoProcedimentoSpdata"] for item in filtrados] == [
        "10101012",
        "41301307",
        "41301471",
        "40901300",
        "41500000",
    ]
