from datetime import date
from types import SimpleNamespace

from src.services import spdata_atendimentos_service as service


class QueryFake:
    def __init__(self, row):
        self.row = row

    def join(self, *_args, **_kwargs):
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.row


def test_buscar_atendimento_em_andamento_local_retorna_false_quando_nao_encontra(monkeypatch):
    monkeypatch.setattr(service, "get_crm_medico_usuario", lambda _usuario_id: "CRM123")
    monkeypatch.setattr(service, "resolver_unidade_usuario", lambda *_args, **_kwargs: SimpleNamespace(id=7))
    monkeypatch.setattr(service.db.session, "query", lambda *_args: QueryFake(None))

    resultado = service.buscar_atendimento_em_andamento_local(10, unidade_id=7, data_ref=date(2026, 9, 29))

    assert resultado == {
        "emAtendimento": False,
        "data": "2026-09-29",
        "unidadeId": 7,
    }


def test_buscar_atendimento_em_andamento_local_retorna_paciente_quando_encontra(monkeypatch):
    atendimento = SimpleNamespace(id=99, data_agenda=date(2026, 9, 28), em_edicao=True)
    spdata = SimpleNamespace(
        id=123,
        id_paciente_spdata=456,
        paciente="Paciente Teste",
        paciente_nome_social="Nome Social",
    )

    monkeypatch.setattr(service, "get_crm_medico_usuario", lambda _usuario_id: "CRM123")
    monkeypatch.setattr(service, "resolver_unidade_usuario", lambda *_args, **_kwargs: SimpleNamespace(id=7))
    monkeypatch.setattr(service.db.session, "query", lambda *_args: QueryFake((atendimento, spdata)))

    resultado = service.buscar_atendimento_em_andamento_local(10, unidade_id=7, data_ref=date(2026, 9, 29))

    assert resultado["emAtendimento"] is True
    assert resultado["emEdicao"] is True
    assert resultado["data"] == "2026-09-28"
    assert resultado["id"] == 123
    assert resultado["medsystemAtendimentoId"] == 99
    assert resultado["paciente"] == {
        "id": 456,
        "nome": "Paciente Teste",
        "nomeSocial": "Nome Social",
    }


def test_buscar_atendimento_em_andamento_local_sem_data_consulta_qualquer_data(monkeypatch):
    monkeypatch.setattr(service, "get_crm_medico_usuario", lambda _usuario_id: "CRM123")
    monkeypatch.setattr(service, "resolver_unidade_usuario", lambda *_args, **_kwargs: SimpleNamespace(id=7))
    monkeypatch.setattr(service.db.session, "query", lambda *_args: QueryFake(None))

    resultado = service.buscar_atendimento_em_andamento_local(10, unidade_id=7)

    assert resultado["emAtendimento"] is False
    assert resultado["data"] is None
