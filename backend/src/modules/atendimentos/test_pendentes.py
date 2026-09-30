from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from src import create_app
from src.models.model_mydsystem.med_atendimentos_model import (
    MedAtendimentos,
    StatusAtendimentoMedSystem,
)
from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
from src.modules.atendimentos import pendentes
from src.settings.config import Config
from src.settings.extensions import db


HOJE = date(2026, 9, 29)
ONTEM = HOJE - timedelta(days=1)
UNIDADE = SimpleNamespace(id=1, codigo_spdata_centro_custo=10)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(Config, "TESTING", True, raising=False)
    monkeypatch.setattr(pendentes, "resolver_unidade_usuario", lambda _u, _id=None: UNIDADE)
    monkeypatch.setattr(pendentes, "get_crm_medico_usuario", lambda _u: "123")
    monkeypatch.setattr(pendentes, "buscar_convenios_locais", lambda _codigos: {})
    monkeypatch.setattr(
        pendentes,
        "agenda_para_frontend",
        lambda spdata, atendimento, _conv: {"id": spdata.id, "data": atendimento.data_agenda.isoformat()},
    )
    app = create_app()

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


_seq = iter(range(1, 10_000))


def _atendimento(
    data_agenda,
    status=StatusAtendimentoMedSystem.EM_ATENDIMENTO,
    crm="123",
    unidade_id=1,
    hora_agenda=time(8, 0),
):
    n = next(_seq)
    spdata = MedSpdataAtendimento(
        spdata_atendimento_id=n,
        unidade_id=unidade_id,
        data_hora_entrada=datetime.combine(data_agenda, hora_agenda),
        data_atendimento=data_agenda,
        paciente=f"Paciente {n}",
        crm_medico=crm,
    )
    db.session.add(spdata)
    db.session.flush()
    db.session.add(MedAtendimentos(
        med_spdata_atendimento_id=spdata.id,
        spdata_atendimento_id=n,
        unidade_id=unidade_id,
        data_agenda=data_agenda,
        hora_agenda=hora_agenda,
        paciente=spdata.paciente,
        status=status.value if hasattr(status, "value") else status,
    ))
    db.session.commit()
    return spdata


def test_lista_em_atendimento_do_medico_na_unidade(app):
    ontem = _atendimento(ONTEM)
    hoje = _atendimento(HOJE)
    _atendimento(ONTEM, StatusAtendimentoMedSystem.ATENDIDO)
    _atendimento(ONTEM, crm="999")
    _atendimento(ONTEM, unidade_id=2)

    itens = pendentes.listar_atendimentos_pendentes(1)

    assert [item["id"] for item in itens] == [hoje.id, ontem.id]


def test_anteriores_a_exclui_atendimentos_do_dia(app):
    ontem = _atendimento(ONTEM)
    _atendimento(HOJE)

    itens = pendentes.listar_atendimentos_pendentes(1, anteriores_a=HOJE)

    assert [item["id"] for item in itens] == [ontem.id]


def test_lista_status_normalizado_e_mais_recente_primeiro(app):
    anteontem = _atendimento(HOJE - timedelta(days=2), status="em-atendimento")
    ontem_cedo = _atendimento(ONTEM, hora_agenda=time(8, 0))
    ontem_tarde = _atendimento(ONTEM, hora_agenda=time(16, 0))

    itens = pendentes.listar_atendimentos_pendentes(1, anteriores_a=HOJE)

    assert [item["id"] for item in itens] == [ontem_tarde.id, ontem_cedo.id, anteontem.id]
