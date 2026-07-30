from datetime import date, datetime, time
from types import SimpleNamespace

from src.services import spdata_atendimentos_service as service


def test_formatar_alergia_spdata_prioriza_agente_e_preserva_observacao():
    assert service.formatar_alergia_spdata("Dipirona", "Urticaria") == "Dipirona (Urticaria)"
    assert service.formatar_alergia_spdata("Dipirona", "dipirona") == "Dipirona"
    assert service.formatar_alergia_spdata(None, "Quinolonas em geral") == "Quinolonas em geral"
    assert service.formatar_alergia_spdata(None, None) == "Alergia informada"


def test_buscar_alergias_pacientes_spdata_filtra_deduplica_e_agrupa(monkeypatch):
    class FakeCursor:
        description = [
            ("ID_PACIENTE_SPDATA",),
            ("AGENTE",),
            ("OBSERVACAO",),
        ]

        def __init__(self):
            self.params = None
            self.closed = False

        def execute(self, _sql, params):
            self.params = list(params)

        def fetchall(self):
            return [
                (1, "Dipirona", None),
                (1, "dipirona", None),
                (1, None, "Quinolonas em geral"),
                (2, None, None),
            ]

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self):
            self.cursor_instance = FakeCursor()

        def cursor(self):
            return self.cursor_instance

        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc_val, _exc_tb):
            return None

    fake_connection = FakeConnection()
    monkeypatch.setattr(service, "ConnectionDBFireBird", lambda: fake_connection)

    alergias = service.buscar_alergias_pacientes_spdata([1, 2, 1, None, ""])

    assert fake_connection.cursor_instance.params == [1, 2]
    assert fake_connection.cursor_instance.closed is True
    assert alergias == {
        1: ["Dipirona", "Quinolonas em geral"],
        2: ["Alergia informada"],
    }


def test_agenda_para_frontend_envia_alergias_do_paciente():
    spdata = SimpleNamespace(
        id=10,
        spdata_atendimento_id=99,
        cod_atendimento="A123",
        data_atendimento=date(2026, 7, 30),
        hora_entrada=time(8, 30),
        id_paciente_spdata=123,
        id_medico_spdata=7,
        obs_atendimento="",
        data_hora_entrada=datetime(2026, 7, 30, 8, 30),
        paciente="Paciente Teste",
        data_nascimento=date(1990, 1, 1),
        sexo="F",
        id_convenio_spdata=1,
        celular="",
        email="",
        cpf="",
        endereco="",
        dados_spdata={},
    )

    item = service.agenda_para_frontend(
        spdata,
        convenios_por_codigo={1: "Convenio"},
        alergias_por_paciente={123: ["Dipirona"]},
    )

    assert item["paciente"]["alergias"] == ["Dipirona"]
