from datetime import date, datetime, time

import pytest
from flask import request

from src import create_app
from src.models.auditoria_model import AcaoAuditoria, Auditoria
from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
from src.modules.lgpd.service import listar_auditorias
from src.settings.config import Config
from src.settings.extensions import db


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(Config, "TESTING", True, raising=False)
    app = create_app()

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _spdata_atendimento(**kwargs):
    defaults = {
        "spdata_atendimento_id": 100,
        "data_hora_entrada": datetime.combine(date(2026, 10, 7), time(8, 0)),
        "data_atendimento": date(2026, 10, 7),
        "paciente": "Paciente Clinico",
        "paciente_nome_social": "Nome Social",
        "id_paciente_spdata": 456,
    }
    defaults.update(kwargs)
    return MedSpdataAtendimento(**defaults)


def test_listar_auditorias_enriquece_paciente_do_atendimento_medico(app):
    with app.app_context():
        spdata = _spdata_atendimento()
        db.session.add(spdata)
        db.session.flush()

        db.session.add_all([
            Auditoria(
                acao=AcaoAuditoria.LOGIN_SUCESSO.value,
                entidade="login",
                created_at=datetime(2026, 10, 7, 11, 0, 0),
            ),
            Auditoria(
                acao=AcaoAuditoria.INICIOU_ATENDIMENTO.value,
                entidade="agenda_medica",
                entidade_id=spdata.id,
                descricao="Status de atendimento atualizado. status=em-atendimento",
                created_at=datetime(2026, 10, 7, 12, 0, 0),
            ),
        ])
        db.session.commit()

        with app.test_request_context("/auditorias/?limit=10"):
            resultado = listar_auditorias(request.args)

    evento = resultado["items"][0]
    assert evento["acao"] == AcaoAuditoria.INICIOU_ATENDIMENTO.value
    assert evento["paciente"] == {
        "id": 456,
        "nome": "Paciente Clinico",
        "nome_social": "Nome Social",
        "label": "Nome Social",
    }
    assert evento["descricao_direta"] == "Médico iniciou o atendimento do paciente."
    assert set(evento["paciente"].keys()) == {"id", "nome", "nome_social", "label"}
    assert resultado["items"][1]["paciente"] is None


def test_listar_auditorias_enriquece_abertura_direta_de_paciente(app):
    with app.app_context():
        db.session.add(_spdata_atendimento(
            spdata_atendimento_id=101,
            paciente="Paciente Direto",
            paciente_nome_social=None,
            id_paciente_spdata=987,
        ))
        db.session.add(Auditoria(
            acao=AcaoAuditoria.ABRIU_PACIENTE.value,
            entidade="paciente",
            entidade_id=987,
            descricao="Abertura do historico do paciente. atendimento_id=10",
            created_at=datetime(2026, 10, 7, 12, 0, 0),
        ))
        db.session.commit()

        with app.test_request_context("/auditorias/?limit=10"):
            resultado = listar_auditorias(request.args)

    assert resultado["items"][0]["paciente"]["id"] == 987
    assert resultado["items"][0]["paciente"]["label"] == "Paciente Direto"
    assert resultado["items"][0]["descricao_direta"] == "Médico abriu os dados do paciente."


@pytest.mark.parametrize(
    ("acao", "descricao", "esperado"),
    [
        (
            AcaoAuditoria.FINALIZOU_ATENDIMENTO.value,
            "Status de atendimento atualizado. status=atendido",
            "Médico finalizou o atendimento do paciente.",
        ),
        (
            AcaoAuditoria.ALTEROU_STATUS_AGENDA.value,
            "Status de atendimento atualizado. status=em-atendimento",
            "Médico atualizou o status do atendimento para em atendimento.",
        ),
        (
            AcaoAuditoria.VISUALIZOU_PRONTUARIO.value,
            "Acesso ao histórico local do paciente. total=2",
            "Médico visualizou o histórico local do paciente.",
        ),
        (
            AcaoAuditoria.VISUALIZOU_HISTORICO_BIODATA.value,
            "Acesso ao histórico BioData do paciente. limit=10 offset=0",
            "Médico consultou o histórico BioData do paciente.",
        ),
        (
            AcaoAuditoria.VISUALIZOU_HISTORICO_SPDATA.value,
            "Acesso ao histórico SPDATA do paciente. limit=10 offset=0",
            "Médico consultou o histórico SPDATA do paciente.",
        ),
        (
            AcaoAuditoria.VISUALIZOU_EXAMES_PACS.value,
            "paciente_id=456; total=3",
            "Médico visualizou exames PACS do paciente.",
        ),
        (
            AcaoAuditoria.VISUALIZOU_LAUDO_EXAME.value,
            "paciente_id=456; silanexa_id=10",
            "Médico abriu laudo de exame do paciente.",
        ),
        (
            AcaoAuditoria.VISUALIZOU_IMAGEM_EXAME.value,
            "paciente_id=456; silanexa_id=10",
            "Médico abriu imagem de exame do paciente.",
        ),
        (
            AcaoAuditoria.VISUALIZOU_DOCUMENTOS_MEDICOS.value,
            "Listagem de documentos médicos do atendimento",
            "Médico visualizou documentos médicos do paciente.",
        ),
        (
            AcaoAuditoria.SALVOU_DOCUMENTO_MEDICO.value,
            "Documento médico salvo. tipo=ATESTADO",
            "Médico salvou documento médico do paciente.",
        ),
    ],
)
def test_listar_auditorias_descreve_interacao_medico_paciente(
    app,
    acao,
    descricao,
    esperado,
):
    with app.app_context():
        db.session.add(_spdata_atendimento())
        db.session.add(Auditoria(
            acao=acao,
            entidade="paciente",
            entidade_id=456,
            descricao=descricao,
            created_at=datetime(2026, 10, 7, 12, 0, 0),
        ))
        db.session.commit()

        with app.test_request_context("/auditorias/?limit=10"):
            resultado = listar_auditorias(request.args)

    assert resultado["items"][0]["descricao_direta"] == esperado
    assert resultado["items"][0]["descricao"] == descricao
