from datetime import date, datetime, time, timedelta

import pytest

from src import create_app
from src.models.auditoria_model import AcaoAuditoria, Auditoria
from src.models.model_mydsystem.med_atendimentos_model import (
    MedAtendimentos,
    StatusAtendimentoMedSystem,
)
from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
from src.modules.atendimentos import encerramento as servico
from src.settings.config import Config
from src.settings.extensions import db


HOJE = date(2026, 9, 29)
ONTEM = HOJE - timedelta(days=1)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(Config, "TESTING", True, raising=False)
    monkeypatch.setattr(servico, "apagar_cache_por_padrao", lambda _padrao: 0)
    app = create_app()

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


_seq = iter(range(1, 10_000))


def _atendimento(data_agenda, status=StatusAtendimentoMedSystem.EM_ATENDIMENTO, crm="123"):
    n = next(_seq)
    spdata = MedSpdataAtendimento(
        spdata_atendimento_id=n,
        data_hora_entrada=datetime.combine(data_agenda, time(8, 0)),
        data_atendimento=data_agenda,
        paciente=f"Paciente {n}",
        crm_medico=crm,
    )
    db.session.add(spdata)
    db.session.flush()
    atendimento = MedAtendimentos(
        med_spdata_atendimento_id=spdata.id,
        spdata_atendimento_id=n,
        data_agenda=data_agenda,
        paciente=spdata.paciente,
        status=status.value,
    )
    db.session.add(atendimento)
    db.session.commit()
    return atendimento


def _status(atendimento):
    return db.session.get(MedAtendimentos, atendimento.id).status


def test_encerra_apenas_em_atendimento_de_dias_anteriores(app):
    antigo = _atendimento(ONTEM)
    de_hoje = _atendimento(HOJE)
    atendido = _atendimento(ONTEM, StatusAtendimentoMedSystem.ATENDIDO)
    faltou = _atendimento(ONTEM, StatusAtendimentoMedSystem.FALTOU)

    resultado = servico.encerrar_atendimentos_pendentes(hoje=HOJE)

    assert [item["id"] for item in resultado["encerrados"]] == [antigo.id]
    assert _status(antigo) == StatusAtendimentoMedSystem.ATENDIDO.value
    assert db.session.get(MedAtendimentos, antigo.id).finished_at is not None
    assert _status(de_hoje) == StatusAtendimentoMedSystem.EM_ATENDIMENTO.value
    assert _status(atendido) == StatusAtendimentoMedSystem.ATENDIDO.value
    assert _status(faltou) == StatusAtendimentoMedSystem.FALTOU.value

    auditorias = Auditoria.query.filter_by(
        acao=AcaoAuditoria.ENCERROU_ATENDIMENTO_AUTOMATICAMENTE.value
    ).all()
    assert len(auditorias) == 1
    assert auditorias[0].entidade_id == antigo.med_spdata_atendimento_id


def test_dry_run_nao_altera_nada(app):
    antigo = _atendimento(ONTEM)

    resultado = servico.encerrar_atendimentos_pendentes(hoje=HOJE, dry_run=True)

    assert resultado["dry_run"] is True
    assert [item["id"] for item in resultado["encerrados"]] == [antigo.id]
    assert _status(antigo) == StatusAtendimentoMedSystem.EM_ATENDIMENTO.value
    assert Auditoria.query.count() == 0


def test_filtra_por_crm_do_medico(app):
    do_medico = _atendimento(ONTEM, crm="123")
    de_outro = _atendimento(ONTEM, crm="999")

    servico.encerrar_atendimentos_pendentes(hoje=HOJE, crm_medico="123")

    assert _status(do_medico) == StatusAtendimentoMedSystem.ATENDIDO.value
    assert _status(de_outro) == StatusAtendimentoMedSystem.EM_ATENDIMENTO.value
