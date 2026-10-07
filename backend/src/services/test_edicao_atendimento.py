from datetime import date, datetime, time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.models.evolucao_medica_versao_model import EvolucaoMedicaVersao  # noqa: F401
from src.models.documento_medico_model import DocumentoMedico  # noqa: F401
from src.models.documento_personalizado_model import DocumentoPersonalizado  # noqa: F401
from src.models.model_padroes_solicitacoes.exames_para_modelo_exame_model import ExamesDoModelo  # noqa: F401
from src.models.model_padroes_solicitacoes.modelo_exame_model import ModeloExame  # noqa: F401
from src.models.model_mydsystem.med_atendimentos_model import MedAtendimentos
from src.services import spdata_atendimentos_service as service


def atendimento_concluido():
    return MedAtendimentos(
        med_spdata_atendimento_id=12,
        spdata_atendimento_id=34,
        data_agenda=date(2026, 10, 7),
        paciente="Paciente teste",
        status="ATENDIDO",
        started_at=datetime(2026, 10, 7, 9),
        finished_at=datetime(2026, 10, 7, 9, 30),
    )


def preparar_transicao(monkeypatch, atendimento):
    spdata = SimpleNamespace(id_convenio_spdata=None, spdata_atendimento_id=34)
    salvar = Mock()
    excluir = Mock()
    preventivos = Mock()
    monkeypatch.setattr(service, "buscar_agenda_id_para_spdata_atendimento", lambda *_: None)
    monkeypatch.setattr(service, "buscar_atendimento_medsystem_para_spdata", lambda *_: atendimento)
    monkeypatch.setattr(service, "buscar_convenios_locais", lambda *_: {})
    monkeypatch.setattr(service, "buscar_prioridades_locais", lambda *_: {})
    monkeypatch.setattr(service, "agenda_para_frontend", lambda _sp, atual, *_args, **_kwargs: {
        "status": service.normalizar_status(atual.status) if atual else "em-espera",
        "emEdicao": bool(atual.em_edicao) if atual else False,
    })
    monkeypatch.setattr(service, "salvar_conteudo_clinico", salvar)
    monkeypatch.setattr(service, "marcar_preventivos_atendidos", preventivos)
    monkeypatch.setattr(service.db.session, "delete", excluir)
    monkeypatch.setattr(service.db.session, "commit", Mock())
    return spdata, salvar, excluir, preventivos


@pytest.mark.parametrize("operacao", ["cancelado", "atendido"])
def test_encerrar_edicao_preserva_conclusao_e_nao_exclui_registro(monkeypatch, operacao):
    atendimento = atendimento_concluido()
    inicio, fim = atendimento.started_at, atendimento.finished_at
    spdata, salvar, excluir, preventivos = preparar_transicao(monkeypatch, atendimento)
    unidade = SimpleNamespace(id=7)

    aberto = service._aplicar_status_spdata(spdata, "em-atendimento", 10, None, unidade)
    assert aberto["emEdicao"] is True
    assert atendimento.finished_at == fim
    # Retomar/repetir a abertura não pode perder o contexto persistente.
    service._aplicar_status_spdata(spdata, "em-atendimento", 10, None, unidade)
    consulta = {"anamnese": "Alteração não confirmada", "medicamentos": "Nova receita"}
    resultado = service._aplicar_status_spdata(spdata, operacao, 10, consulta, unidade)

    assert resultado["status"] == "atendido"
    assert resultado["emEdicao"] is False
    assert resultado["operacaoEdicao"] == operacao
    assert atendimento.started_at == inicio
    assert atendimento.finished_at == fim
    excluir.assert_not_called()
    preventivos.assert_not_called()
    if operacao == "cancelado":
        salvar.assert_not_called()
    else:
        salvar.assert_called_once_with(spdata, atendimento, 10, consulta, unidade=unidade, em_edicao=True)


def test_finalizar_edicao_permite_limpar_anamnese(monkeypatch):
    anamnese = SimpleNamespace(observacoes="Texto original")
    evolucao = SimpleNamespace(texto_evolucao="Texto original", status="finalizado")
    clinico = SimpleNamespace(hora_fim=time(9, 30), anamnese=anamnese, evolucoes_medicas=[evolucao])
    monkeypatch.setattr(service.db.session, "execute", lambda *_: SimpleNamespace(
        scalars=lambda: SimpleNamespace(first=lambda: clinico)))
    monkeypatch.setattr(service, "spdata_agenda_id_do_atendimento", lambda *_: None)
    service.salvar_conteudo_clinico(SimpleNamespace(spdata_atendimento_id=34), atendimento_concluido(),
                                   10, {"anamnese": ""}, em_edicao=True)
    assert anamnese.observacoes == ""
    assert evolucao.texto_evolucao == ""
    assert clinico.hora_fim == time(9, 30)


def test_cancelar_consulta_nova_continua_devolvendo_a_fila(monkeypatch):
    atendimento = atendimento_concluido()
    atendimento.status = "EM_ATENDIMENTO"
    atendimento.finished_at = None
    spdata, salvar, excluir, _ = preparar_transicao(monkeypatch, atendimento)

    resultado = service._aplicar_status_spdata(spdata, "cancelado", 10, None, SimpleNamespace(id=7))

    assert resultado["status"] == "em-espera"
    excluir.assert_called_once_with(atendimento)
    salvar.assert_not_called()


def test_cancelamento_direto_de_concluido_e_rejeitado(monkeypatch):
    atendimento = atendimento_concluido()
    spdata, salvar, excluir, _ = preparar_transicao(monkeypatch, atendimento)
    with pytest.raises(ValueError):
        service._aplicar_status_spdata(spdata, "cancelado", 10, None, SimpleNamespace(id=7))
    excluir.assert_not_called()
    salvar.assert_not_called()


@pytest.mark.parametrize("status", ["faltou", "em-espera"])
def test_edicao_nao_pode_ser_convertida_em_falta_ou_fila(monkeypatch, status):
    atendimento = atendimento_concluido()
    atendimento.marcar_em_atendimento()
    spdata, salvar, excluir, _ = preparar_transicao(monkeypatch, atendimento)
    with pytest.raises(ValueError):
        service._aplicar_status_spdata(spdata, status, 10, None, SimpleNamespace(id=7))
    assert atendimento.em_edicao is True
    assert atendimento.status == "EM_ATENDIMENTO"
    excluir.assert_not_called()
    salvar.assert_not_called()


@pytest.mark.parametrize("em_edicao", [True, False])
def test_gravacao_clinica_preserva_hora_fim_e_documentos_na_edicao(monkeypatch, em_edicao):
    fim = time(9, 30)
    documento = object()
    clinico = SimpleNamespace(hora_fim=fim, documentos=[documento], cid_personalizado=None)
    monkeypatch.setattr(service.db.session, "execute", lambda *_: SimpleNamespace(
        scalars=lambda: SimpleNamespace(first=lambda: clinico)))
    excluir = Mock()
    monkeypatch.setattr(service.db.session, "delete", excluir)
    monkeypatch.setattr(service, "spdata_agenda_id_do_atendimento", lambda *_: None)
    service.salvar_conteudo_clinico(
        SimpleNamespace(spdata_atendimento_id=34), atendimento_concluido(), 10,
        {"cid_personalizado": None}, em_edicao=em_edicao,
    )
    assert (clinico.hora_fim == fim) is em_edicao
    assert clinico.documentos == [documento]
    excluir.assert_not_called()
