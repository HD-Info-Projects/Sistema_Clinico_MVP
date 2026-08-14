import json
from datetime import datetime, time, timedelta

import pytest

from src import create_app
from src.models.anamnese_model import Anamnese
from src.models.atendimentos_model import Atendimento
from src.models.auditoria_model import AcaoAuditoria, Auditoria
from src.models.diagnostico_model import Diagnostico
from src.models.documento_medico_model import DocumentoMedico
from src.models.evolucoes_medicas_model import EvolucaoMedica
from src.models.evolucao_medica_versao_model import EvolucaoMedicaVersao
from src.models.fila_sincronizacao_model import (
    FilaSincronizacao,
    StatusSincronizacao,
    TipoEventoSincronizacao,
)
from src.models.log_integracao_model import LogIntegracao
from src.models.model_mydsystem.med_atendimentos_model import MedAtendimentos
from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
from src.models.model_mydsystem.med_spdata_atendimentos_model import (
    MedSpdataAtendimento,
)
from src.models.prescricao_model import Prescricao
from src.models.solicitacao_exame_model import SolicitacaoExame
from src.models.usuario_model import Usuario
from src.services.lgpd_retencao_service import (
    REGRAS_RETENCAO,
    TABELAS_CLINICAS_PROTEGIDAS,
    executar_retencao_lgpd,
)
from src.settings.config import Config
from src.settings.extensions import db


AGORA = datetime(2026, 8, 13, 12, 0, 0)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(Config, "TESTING", True, raising=False)
    app = create_app()
    app.config.update(
        LGPD_RETENTION_LOGS_INTEGRACAO_DAYS=180,
        LGPD_RETENTION_FILA_SINCRONIZACAO_DAYS=90,
        LGPD_RETENTION_AUDITORIA_DAYS=1825,
        LGPD_RETENTION_SPDATA_ESPELHO_DAYS=730,
        LGPD_RETENTION_BATCH_SIZE=1,
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _log(created_at, acao="teste"):
    return LogIntegracao(
        acao=acao,
        sucesso=True,
        created_at=created_at,
    )


def _fila(status, updated_at, referencia_id):
    return FilaSincronizacao(
        tipo_evento=TipoEventoSincronizacao.ATENDIMENTO_FINALIZADO,
        referencia_id=referencia_id,
        payload={},
        status=status,
        created_at=updated_at,
        updated_at=updated_at,
    )


def _spdata_atendimento(spdata_id, data_atendimento):
    return MedSpdataAtendimento(
        spdata_atendimento_id=spdata_id,
        data_hora_entrada=datetime.combine(data_atendimento, time(8, 0)),
        data_atendimento=data_atendimento,
        paciente=f"Paciente {spdata_id}",
    )


def _executar_aprovado(agora=AGORA):
    plano = executar_retencao_lgpd(dry_run=True, agora=agora)
    return executar_retencao_lgpd(
        dry_run=False,
        agora=agora,
        plan_hash=plano["plan_hash"],
        contexto_execucao={
            "backup_reference": "sistema_clinico_mysql_teste.sql.gz.age",
            "approval_reference": "CHANGE-TESTE-001",
            "operator": "conta-tecnica-teste",
            "legal_hold_checked": True,
        },
    )


def test_dry_run_conta_e_mostra_cortes_sem_alterar_banco(app):
    corte_log = AGORA - timedelta(days=180)
    corte_spdata = (AGORA - timedelta(days=730)).date()
    db.session.add_all([
        _log(corte_log - timedelta(seconds=1), "antigo"),
        _log(corte_log, "no-limite"),
        MedSpdataAgenda(
            spdata_agenda_id=1,
            paciente="Paciente",
            data_agenda=corte_spdata - timedelta(days=1),
        ),
    ])
    db.session.commit()

    resultado = executar_retencao_lgpd(dry_run=True, agora=AGORA)

    assert resultado["modo"] == "dry-run"
    assert resultado["tabelas"]["logs_integracao"] == {
        "campo_data": "created_at",
        "retencao_dias": 180,
        "corte": corte_log.isoformat(),
        "candidatos": 1,
        "protegidos_por_vinculo": 0,
        "elegiveis": 1,
        "hash_ids_elegiveis": resultado["tabelas"]["logs_integracao"][
            "hash_ids_elegiveis"
        ],
        "exclusao_automatica": True,
        "excluidos": 0,
    }
    assert resultado["tabelas"]["MED_SPDATA_AGENDA"]["corte"] == (
        corte_spdata.isoformat()
    )
    assert resultado["tabelas"]["MED_SPDATA_AGENDA"]["elegiveis"] == 1
    assert db.session.query(LogIntegracao).count() == 2
    assert db.session.query(MedSpdataAgenda).count() == 1
    assert db.session.query(Auditoria).count() == 0


def test_configuracao_define_defaults_da_politica():
    assert Config.LGPD_RETENTION_LOGS_INTEGRACAO_DAYS == 180
    assert Config.LGPD_RETENTION_FILA_SINCRONIZACAO_DAYS == 90
    assert Config.LGPD_RETENTION_AUDITORIA_DAYS == 1825
    assert Config.LGPD_RETENTION_SPDATA_ESPELHO_DAYS == 730
    assert Config.LGPD_RETENTION_BATCH_SIZE == 500


def test_execute_aplica_status_limites_fk_lotes_e_auditoria(app):
    corte_log = AGORA - timedelta(days=180)
    corte_fila = AGORA - timedelta(days=90)
    corte_auditoria = AGORA - timedelta(days=1825)
    corte_spdata = (AGORA - timedelta(days=730)).date()

    db.session.add_all([
        _log(corte_log - timedelta(seconds=2), "antigo-1"),
        _log(corte_log - timedelta(seconds=1), "antigo-2"),
        _log(corte_log, "no-limite"),
        _fila(StatusSincronizacao.SINCRONIZADO, corte_fila - timedelta(seconds=1), 1),
        _fila(StatusSincronizacao.CANCELADO, corte_fila - timedelta(seconds=1), 2),
        _fila(StatusSincronizacao.PENDENTE, corte_fila - timedelta(days=1), 3),
        _fila(StatusSincronizacao.ERRO, corte_fila - timedelta(days=1), 4),
        _fila(StatusSincronizacao.SINCRONIZADO, corte_fila, 5),
        Auditoria(
            acao="EVENTO_ANTIGO",
            created_at=corte_auditoria - timedelta(seconds=1),
        ),
        Auditoria(
            acao=AcaoAuditoria.RETENCAO_DESCARTE_EXECUTADA.value,
            created_at=corte_auditoria - timedelta(seconds=1),
        ),
        Auditoria(acao="EVENTO_LIMITE", created_at=corte_auditoria),
        MedSpdataAgenda(
            spdata_agenda_id=10,
            paciente="Agenda antiga",
            data_agenda=corte_spdata - timedelta(days=1),
        ),
        MedSpdataAgenda(
            spdata_agenda_id=11,
            paciente="Agenda limite",
            data_agenda=corte_spdata,
        ),
    ])
    spdata_livre = _spdata_atendimento(20, corte_spdata - timedelta(days=1))
    spdata_limite = _spdata_atendimento(22, corte_spdata)
    db.session.add_all([spdata_livre, spdata_limite])
    db.session.commit()

    resultado = _executar_aprovado()

    assert resultado["total_excluidos"] == 6
    assert resultado["tabelas"]["logs_integracao"]["excluidos"] == 2
    assert resultado["tabelas"]["fila_sincronizacao"]["excluidos"] == 2
    assert resultado["tabelas"]["auditorias"]["excluidos"] == 2
    assert resultado["tabelas"]["MED_SPDATA_AGENDA"]["excluidos"] == 0
    assert resultado["tabelas"]["MED_SPDATA_ATENDIMENTOS"] == {
        "campo_data": "data_atendimento",
        "retencao_dias": 730,
        "corte": corte_spdata.isoformat(),
        "candidatos": 1,
        "protegidos_por_vinculo": 0,
        "elegiveis": 1,
        "hash_ids_elegiveis": resultado["tabelas"]["MED_SPDATA_ATENDIMENTOS"][
            "hash_ids_elegiveis"
        ],
        "exclusao_automatica": False,
        "excluidos": 0,
    }

    assert [log.acao for log in db.session.query(LogIntegracao).all()] == ["no-limite"]
    assert {
        fila.referencia_id for fila in db.session.query(FilaSincronizacao).all()
    } == {3, 4, 5}
    assert {
        item.spdata_atendimento_id
        for item in db.session.query(MedSpdataAtendimento).all()
    } == {20, 22}

    auditorias = db.session.query(Auditoria).order_by(Auditoria.id).all()
    assert [item.acao for item in auditorias] == [
        "EVENTO_LIMITE",
        AcaoAuditoria.RETENCAO_DESCARTE_EXECUTADA.value,
    ]
    evento_execucao = auditorias[-1]
    assert evento_execucao.created_at == AGORA
    assert evento_execucao.usuario_id is None
    assert evento_execucao.medico_id is None
    assert evento_execucao.ip is None
    assert evento_execucao.user_agent is None
    resumo = json.loads(evento_execucao.descricao)
    assert resumo["total_excluidos"] == 6
    assert resumo["backup_reference"] == "sistema_clinico_mysql_teste.sql.gz.age"
    assert resumo["approval_reference"] == "CHANGE-TESTE-001"
    assert resumo["operator"] == "conta-tecnica-teste"
    assert resumo["legal_hold_checked"] is True
    assert "paciente" not in evento_execucao.descricao.lower()


def test_tabelas_clinicas_sao_explicitamente_excluidas_da_politica(app):
    nomes_clinicos = {
        Atendimento.__tablename__,
        Anamnese.__tablename__,
        EvolucaoMedica.__tablename__,
        EvolucaoMedicaVersao.__tablename__,
        Diagnostico.__tablename__,
        Prescricao.__tablename__,
        SolicitacaoExame.__tablename__,
        DocumentoMedico.__tablename__,
    }
    assert TABELAS_CLINICAS_PROTEGIDAS == nomes_clinicos
    assert nomes_clinicos.isdisjoint(
        regra.modelo.__tablename__ for regra in REGRAS_RETENCAO
    )

    usuario = Usuario(
        nome_completo="Medico",
        cnpj_cpf="00000000000",
        email="medico@example.test",
        senha="senha-segura",
    )
    atendimento = Atendimento(
        spdata_paciente_id=1,
        spdata_agenda_id=1,
        spdata_medico_id=1,
        paciente_nome="Paciente clinico",
        paciente_cpf="00000000000",
        data_atendimento=AGORA - timedelta(days=4000),
        hora_inicio=time(8, 0),
        hora_fim=None,
    )
    db.session.add_all([usuario, atendimento])
    db.session.flush()
    evolucao = EvolucaoMedica(
        atendimento_id=atendimento.id,
        medico_id=usuario.id,
        texto_evolucao="Registro clinico",
    )
    db.session.add(evolucao)
    db.session.flush()
    db.session.add_all([
        Anamnese(atendimento_id=atendimento.id),
        EvolucaoMedicaVersao(
            evolucao_id=evolucao.id,
            texto_anterior="Registro anterior",
            texto_novo="Registro clinico",
            alterado_por=usuario.id,
        ),
        Diagnostico(atendimento_id=atendimento.id),
        Prescricao(
            atendimento_id=atendimento.id,
            medico_id=usuario.id,
            medicamento="Medicamento",
        ),
        SolicitacaoExame(atendimento_id=atendimento.id, tipo_exame="Exame"),
        DocumentoMedico(
            atendimento_id=atendimento.id,
            tipo_documento="ATESTADO",
            dados={},
        ),
    ])
    db.session.commit()

    _executar_aprovado()

    for modelo in (
        Atendimento,
        Anamnese,
        EvolucaoMedica,
        EvolucaoMedicaVersao,
        Diagnostico,
        Prescricao,
        SolicitacaoExame,
        DocumentoMedico,
    ):
        assert db.session.query(modelo).count() == 1


def test_execute_preserva_espelhos_monitorados_com_vinculo_clinico(app):
    corte_spdata = (AGORA - timedelta(days=730)).date()
    agenda = MedSpdataAgenda(
        spdata_agenda_id=901,
        paciente="Agenda vinculada",
        data_agenda=corte_spdata - timedelta(days=1),
    )
    spdata = _spdata_atendimento(902, corte_spdata - timedelta(days=1))
    atendimento = Atendimento(
        spdata_atendimento_id=902,
        spdata_paciente_id=1,
        spdata_agenda_id=901,
        spdata_medico_id=1,
        paciente_nome="Paciente clinico",
        paciente_cpf="00000000000",
        data_atendimento=AGORA - timedelta(days=800),
        hora_inicio=time(8, 0),
        hora_fim=None,
    )
    db.session.add_all([
        _log(AGORA - timedelta(days=181), "deve-permanecer"),
        agenda,
        spdata,
        atendimento,
    ])
    db.session.commit()

    dry_run = executar_retencao_lgpd(dry_run=True, agora=AGORA)

    assert dry_run["tabelas"]["MED_SPDATA_AGENDA"]["protegidos_por_vinculo"] == 1
    assert (
        dry_run["tabelas"]["MED_SPDATA_ATENDIMENTOS"]["protegidos_por_vinculo"]
        == 1
    )
    resultado = executar_retencao_lgpd(
        dry_run=False,
        agora=AGORA,
        plan_hash=dry_run["plan_hash"],
        contexto_execucao={
            "backup_reference": "backup-teste",
            "approval_reference": "CHANGE-TESTE-002",
            "operator": "conta-tecnica-teste",
            "legal_hold_checked": True,
        },
    )

    assert resultado["total_excluidos"] == 1
    assert db.session.query(LogIntegracao).count() == 0
    assert db.session.query(MedSpdataAgenda).count() == 1
    assert db.session.query(MedSpdataAtendimento).count() == 1
    assert db.session.query(Auditoria).count() == 1


def test_configuracao_rejeita_prazo_zero(app):
    app.config["LGPD_RETENTION_LOGS_INTEGRACAO_DAYS"] = 0

    with pytest.raises(ValueError, match="maior que zero"):
        executar_retencao_lgpd(dry_run=True, agora=AGORA)


def test_execute_aborta_quando_estado_diverge_do_plano(app):
    db.session.add(_log(AGORA - timedelta(days=181), "planejado"))
    db.session.commit()
    plano = executar_retencao_lgpd(dry_run=True, agora=AGORA)

    db.session.add(_log(AGORA - timedelta(days=182), "novo-elegivel"))
    db.session.commit()

    with pytest.raises(RuntimeError, match="diverge do dry-run aprovado"):
        executar_retencao_lgpd(
            dry_run=False,
            agora=AGORA,
            plan_hash=plano["plan_hash"],
            contexto_execucao={
                "backup_reference": "backup-teste",
                "approval_reference": "CHANGE-TESTE-003",
                "operator": "conta-tecnica-teste",
                "legal_hold_checked": True,
            },
        )

    assert db.session.query(LogIntegracao).count() == 2
    assert db.session.query(Auditoria).count() == 0


def test_execute_reverte_exclusoes_se_a_auditoria_falhar(app, monkeypatch):
    db.session.add(_log(AGORA - timedelta(days=181), "deve-permanecer"))
    db.session.commit()

    def falhar_ao_gerar_resumo(_resultado, _contexto):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(
        "src.services.lgpd_retencao_service._descricao_auditoria",
        falhar_ao_gerar_resumo,
    )

    with pytest.raises(RuntimeError, match="falha simulada"):
        _executar_aprovado()

    assert db.session.query(LogIntegracao).count() == 1
    assert db.session.query(Auditoria).count() == 0


def test_cli_exige_exatamente_um_modo(app):
    runner = app.test_cli_runner()

    sem_modo = runner.invoke(args=["lgpd-retencao"])
    dois_modos = runner.invoke(args=["lgpd-retencao", "--dry-run", "--execute"])
    dry_run = runner.invoke(args=["lgpd-retencao", "--dry-run"])
    execute_sem_aprovacao = runner.invoke(args=["lgpd-retencao", "--execute"])

    assert sem_modo.exit_code == 2
    assert "exatamente uma" in sem_modo.output
    assert dois_modos.exit_code == 2
    assert "exatamente uma" in dois_modos.output
    assert dry_run.exit_code == 0
    assert execute_sem_aprovacao.exit_code == 2
    assert "--plan-hash" in execute_sem_aprovacao.output
    assert "Modo: dry-run" in dry_run.output
    assert "Hash do plano:" in dry_run.output
    assert "corte=" in dry_run.output
