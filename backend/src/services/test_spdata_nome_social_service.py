from datetime import date, datetime, time
from types import SimpleNamespace

import pytest
from sqlalchemy import column

from src.services import spdata_atendimentos_service as service
from src.services.spdata_atendimentos_service import (
    agenda_para_frontend,
    agenda_spdata_para_frontend,
    chave_preventivo,
    consulta_tem_preventivo,
    filtrar_agenda_frontend,
    filtro_visivel_medico_spdata,
    sexo_para_frontend,
    tipo_procedimento_frontend,
)
from src.utils.tuss import codigo_tuss_visivel_medico


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
    assert item["paciente"]["dataNascimento"] is None
    assert item["preventivo"] is False


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
        data_nascimento=date(1899, 12, 30),
        celular=None,
        telefone=None,
        email=None,
        cpf=None,
        atendido_spdata="S",
    )
    spdata_ref = SimpleNamespace(
        id=11,
        spdata_atendimento_id=2002,
        id_medico_spdata=8,
        unidade_id=1,
        data_nascimento=date(1975, 2, 9),
        hora_entrada=time(10, 26),
        sexo="F",
    )

    item = agenda_spdata_para_frontend(agenda, spdata_ref)

    assert item["paciente"]["nome"] == "JOAO NOME CIVIL"
    assert item["paciente"]["nomeSocial"] == "JOAO NOME SOCIAL"
    assert item["paciente"]["dataNascimento"] == "1975-02-09"
    assert item["paciente"]["sexo"] == "feminino"
    assert item["horario"] == "10:26"
    assert item["horarioAgendado"] == "10:00"
    assert item["horarioEntrada"] == "10:26"


def test_agenda_spdata_placeholder_mantem_horario_agendado():
    agenda = SimpleNamespace(
        id=3,
        spdata_agenda_id=2002,
        registro=None,
        id_paciente_spdata=66,
        unidade_id=1,
        id_convenio_spdata=None,
        convenio=None,
        data_agenda=date(2026, 8, 5),
        hora_agenda=time(10, 0),
        obs=None,
        paciente="PACIENTE",
        paciente_nome_social=None,
        data_nascimento=None,
        celular=None,
        telefone=None,
        email=None,
        cpf=None,
        atendido_spdata="N",
    )
    spdata_ref = SimpleNamespace(
        id=11,
        spdata_atendimento_id=-2002,
        id_medico_spdata=8,
        unidade_id=1,
        hora_entrada=time(10, 0),
    )

    item = agenda_spdata_para_frontend(agenda, spdata_ref)

    assert item["status"] == "agendado"
    assert item["horario"] == "10:00"
    assert item["horarioAgendado"] == "10:00"
    assert item["horarioEntrada"] is None
    assert item["paciente"]["sexo"] is None


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("F", "feminino"),
        ("feminino", "feminino"),
        ("M", "masculino"),
        ("masculino", "masculino"),
        (None, None),
        ("", None),
        ("desconhecido", None),
    ],
)
def test_sexo_para_frontend_nao_inventa_valor(valor, esperado):
    assert sexo_para_frontend(valor) == esperado


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


def test_visibilidade_medica_inclui_consultas_e_codigos_liberados():
    assert codigo_tuss_visivel_medico("10101012") is True
    assert codigo_tuss_visivel_medico("5001") is True
    assert codigo_tuss_visivel_medico("41301307") is True
    assert codigo_tuss_visivel_medico("41301471") is True
    assert codigo_tuss_visivel_medico("41301099") is False
    assert codigo_tuss_visivel_medico("41301102") is False
    assert codigo_tuss_visivel_medico("40901300") is False
    assert codigo_tuss_visivel_medico("41500000") is False


def test_filtro_visibilidade_medica_sql_inclui_apenas_regra_permitida():
    model = SimpleNamespace(cod_procedimento_spdata=column("cod_procedimento_spdata"))
    filtro = filtro_visivel_medico_spdata(model)
    sql = str(filtro.compile(compile_kwargs={"literal_binds": True}))

    assert "5001" in sql
    assert "10000000" in sql
    assert "19999999" in sql
    assert "41301307" in sql
    assert "41301471" in sql
    assert "40901300" not in sql
    assert "41500000" not in sql


def test_consulta_tem_preventivo_exige_mesmo_paciente_data_e_unidade():
    chave = chave_preventivo(55, date(2026, 8, 5), 1)
    chaves_preventivos = {chave}

    assert consulta_tem_preventivo("10101012", chave, chaves_preventivos) is True
    assert consulta_tem_preventivo("5001", chave, chaves_preventivos) is True
    assert consulta_tem_preventivo(
        "10101012",
        chave_preventivo(56, date(2026, 8, 5), 1),
        chaves_preventivos,
    ) is False
    assert consulta_tem_preventivo(
        "10101012",
        chave_preventivo(55, date(2026, 8, 6), 1),
        chaves_preventivos,
    ) is False
    assert consulta_tem_preventivo(
        "10101012",
        chave_preventivo(55, date(2026, 8, 5), 2),
        chaves_preventivos,
    ) is False


@pytest.mark.parametrize("codigo", ["41301099", "41301102", "41301307"])
def test_procedimento_nao_recebe_badge_preventivo(codigo):
    chave = chave_preventivo(55, date(2026, 8, 5), 1)

    assert consulta_tem_preventivo(codigo, chave, {chave}) is False


def test_agenda_para_frontend_expoe_badge_preventivo():
    spdata = SimpleNamespace(
        id=10,
        spdata_atendimento_id=1001,
        cod_atendimento="A1001",
        id_paciente_spdata=55,
        id_medico_spdata=7,
        unidade_id=1,
        id_convenio_spdata=None,
        data_atendimento=date(2026, 8, 5),
        hora_entrada=time(9, 30),
        data_hora_entrada=datetime(2026, 8, 5, 9, 30),
        obs_atendimento=None,
        cod_procedimento_spdata="10101012",
        procedimento_spdata="Consulta",
        paciente="PACIENTE",
        paciente_nome_social=None,
        sexo="F",
        data_nascimento=None,
        celular=None,
        email=None,
        cpf=None,
        endereco=None,
        dados_spdata={},
    )

    item = agenda_para_frontend(spdata, preventivo=True)

    assert item["preventivo"] is True


def test_marcar_preventivos_atendidos_atualiza_todos_e_preserva_idempotencia(monkeypatch):
    consulta = SimpleNamespace(
        id=1,
        id_paciente_spdata=55,
        data_atendimento=date(2026, 8, 5),
        cod_procedimento_spdata="10101012",
    )
    preventivos = [
        SimpleNamespace(
            id=2,
            spdata_atendimento_id=1002,
            cod_atendimento="A1002",
            data_atendimento=date(2026, 8, 5),
            hora_entrada=time(9, 31),
            id_medico_spdata=7,
            medico="MEDICA",
            id_paciente_spdata=55,
            paciente="PACIENTE",
            cpf=None,
            prontuario="P55",
        ),
        SimpleNamespace(
            id=3,
            spdata_atendimento_id=1003,
            cod_atendimento="A1003",
            data_atendimento=date(2026, 8, 5),
            hora_entrada=time(9, 32),
            id_medico_spdata=7,
            medico="MEDICA",
            id_paciente_spdata=55,
            paciente="PACIENTE",
            cpf=None,
            prontuario="P55",
        ),
    ]

    class AtendimentoExistente:
        med_spdata_atendimento_id = 2
        status = "ATENDIDO"

        def marcar_atendido(self):
            raise AssertionError("Atendimento já concluído não deve ter a data alterada")

    class Resultado:
        def scalars(self):
            return self

        def all(self):
            return [AtendimentoExistente()]

    parametros_busca = {}
    adicionados = []

    def buscar(*args, **kwargs):
        parametros_busca.update(kwargs)
        return preventivos

    def criar(preventivo, unidade_id):
        class NovoAtendimento:
            med_spdata_atendimento_id = preventivo.id
            status = "EM_ATENDIMENTO"

            def marcar_atendido(self):
                self.status = "ATENDIDO"

        assert unidade_id == 1
        return NovoAtendimento()

    monkeypatch.setattr(service, "buscar_preventivos_spdata", buscar)
    monkeypatch.setattr(service, "criar_atendimento_medsystem", criar)
    monkeypatch.setattr(service.db.session, "execute", lambda _query: Resultado())
    monkeypatch.setattr(service.db.session, "add", adicionados.append)

    atualizados = service.marcar_preventivos_atendidos(consulta, SimpleNamespace(id=1))

    assert len(atualizados) == 2
    assert parametros_busca == {
        "id_paciente_spdata": 55,
        "excluir_id": 1,
        "bloquear": True,
    }
    assert len(adicionados) == 1
    assert adicionados[0].med_spdata_atendimento_id == 3
    assert adicionados[0].status == "ATENDIDO"
