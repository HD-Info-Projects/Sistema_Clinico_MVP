from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace

import pytest
from flask import Flask

from src.modules.agenda import routes as agenda_routes


def _app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        AGENDA_MAX_DIAS_PERIODO=31,
        INTERNAL_REQUEST_SECRET="segredo-interno",
    )
    return app


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


class ProbeFake:
    @contextmanager
    def etapa(self, *_args, **_kwargs):
        yield

    def valor(self, *_args, **_kwargs):
        return None

    def finalizar(self, *_args, **_kwargs):
        return None


def test_periodo_agenda_rejeita_intervalo_maior_que_limite():
    app = _app()

    with app.app_context():
        with pytest.raises(ValueError, match="Período máximo permitido"):
            agenda_routes._validar_periodo_agenda(date(2026, 9, 1), date(2026, 10, 5))


def test_requisicao_automatica_exige_segredo_interno_valido():
    app = _app()

    with app.test_request_context(
        "/agenda-medica/",
        headers={
            "X-Origem-Requisicao": "sse-poll",
            "X-Internal-Secret": "segredo-interno",
        },
    ):
        assert agenda_routes._requisicao_automatica() is True

    with app.test_request_context(
        "/agenda-medica/",
        headers={
            "X-Origem-Requisicao": "sse-poll",
            "X-Internal-Secret": "errado",
        },
    ):
        assert agenda_routes._requisicao_automatica() is False


def test_listar_agenda_nao_marca_auditoria_dedup_quando_servico_falha(monkeypatch):
    app = _app()
    marcacoes = []

    monkeypatch.setattr(agenda_routes, "get_jwt_identity", lambda: "10")
    monkeypatch.setattr(agenda_routes, "unidade_id_request", lambda: 2)
    monkeypatch.setattr(agenda_routes, "iniciar_probe", lambda *_args, **_kwargs: ProbeFake())
    monkeypatch.setattr(agenda_routes, "obter_cache_json", lambda _key: None)
    monkeypatch.setattr(agenda_routes, "marcar_se_ausente", lambda *_args, **_kwargs: marcacoes.append(True))
    monkeypatch.setattr(agenda_routes.db.session, "rollback", lambda: None)

    def falhar(*_args, **_kwargs):
        raise RuntimeError("SPDATA indisponível")

    monkeypatch.setattr(agenda_routes, "listar_agenda_medica", falhar)

    with app.test_request_context("/agenda-medica/?data=2026-09-29"):
        _response, status = _unwrap(agenda_routes.listar_agenda)()

    assert status == 500
    assert marcacoes == []


def test_listar_agenda_marca_auditoria_dedup_apos_sucesso(monkeypatch):
    app = _app()
    marcacoes = []
    auditorias = []

    monkeypatch.setattr(agenda_routes, "get_jwt_identity", lambda: "10")
    monkeypatch.setattr(agenda_routes, "unidade_id_request", lambda: 2)
    monkeypatch.setattr(agenda_routes, "iniciar_probe", lambda *_args, **_kwargs: ProbeFake())
    monkeypatch.setattr(agenda_routes, "obter_cache_json", lambda _key: None)
    monkeypatch.setattr(agenda_routes, "listar_agenda_medica", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(agenda_routes, "salvar_cache_json", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(agenda_routes, "marcar_se_ausente", lambda *_args, **_kwargs: marcacoes.append(True) or True)
    monkeypatch.setattr(agenda_routes, "registrar_auditoria", lambda *_args, **_kwargs: auditorias.append(True))

    with app.test_request_context("/agenda-medica/?data=2026-09-29"):
        _response, status = _unwrap(agenda_routes.listar_agenda)()

    assert status == 200
    assert marcacoes == [True]
    assert auditorias == [True]


@pytest.mark.parametrize(
    ("query", "somente_visiveis_medico"),
    [
        ("data=2026-09-29", False),
        ("data=2026-09-29&contexto=dashboard", True),
    ],
)
def test_listar_agenda_aplica_visibilidade_tuss_apenas_no_dashboard(
    monkeypatch,
    query,
    somente_visiveis_medico,
):
    app = _app()
    chamadas = []

    monkeypatch.setattr(agenda_routes, "get_jwt_identity", lambda: "10")
    monkeypatch.setattr(agenda_routes, "unidade_id_request", lambda: 2)
    monkeypatch.setattr(agenda_routes, "iniciar_probe", lambda *_args, **_kwargs: ProbeFake())
    monkeypatch.setattr(agenda_routes, "obter_cache_json", lambda _key: None)
    monkeypatch.setattr(agenda_routes, "salvar_cache_json", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        agenda_routes,
        "_registrar_auditoria_visualizacao_agenda",
        lambda *_args, **_kwargs: None,
    )

    def listar(*_args, **kwargs):
        chamadas.append(kwargs)
        return []

    monkeypatch.setattr(agenda_routes, "listar_agenda_medica", listar)

    with app.test_request_context(f"/agenda-medica/?{query}"):
        _response, status = _unwrap(agenda_routes.listar_agenda)()

    assert status == 200
    assert chamadas[0]["somente_visiveis_medico"] is somente_visiveis_medico


def test_marcadores_da_agenda_nao_aplicam_filtro_tuss(monkeypatch):
    app = _app()
    chamadas = []

    monkeypatch.setattr(agenda_routes, "get_jwt_identity", lambda: "10")
    monkeypatch.setattr(agenda_routes, "unidade_id_request", lambda: 2)

    def listar(*_args, **kwargs):
        chamadas.append(kwargs)
        return []

    monkeypatch.setattr(agenda_routes, "listar_marcadores_agenda_medica", listar)

    with app.test_request_context("/agenda-medica/marcadores?data=2026-09-29"):
        _response, status = _unwrap(agenda_routes.listar_marcadores_agenda)()

    assert status == 200
    assert chamadas[0].get("somente_visiveis_medico", False) is False


def test_auditoria_remove_marca_dedup_se_registro_falhar(monkeypatch):
    app = _app()
    remocoes = []

    monkeypatch.setattr(agenda_routes, "marcar_se_ausente", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(agenda_routes, "apagar_marca", lambda *_args, **_kwargs: remocoes.append(True))

    def falhar(*_args, **_kwargs):
        raise RuntimeError("auditoria indisponível")

    monkeypatch.setattr(agenda_routes, "registrar_auditoria", falhar)

    with app.test_request_context("/agenda-medica/?data=2026-09-29"):
        with pytest.raises(RuntimeError, match="auditoria indisponível"):
            agenda_routes._registrar_auditoria_visualizacao_agenda(
                10,
                2,
                date(2026, 9, 29),
                date(2026, 9, 29),
                None,
                None,
                None,
                "Listagem de agenda médica.",
            )

    assert remocoes == [True]


def test_auditoria_remove_marca_dedup_quando_registro_retorna_none(monkeypatch):
    app = _app()
    remocoes = []

    monkeypatch.setattr(agenda_routes, "marcar_se_ausente", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(agenda_routes, "apagar_marca", lambda *_args, **_kwargs: remocoes.append(True))
    monkeypatch.setattr(agenda_routes, "registrar_auditoria", lambda *_args, **_kwargs: None)

    with app.test_request_context("/agenda-medica/?data=2026-09-29"):
        agenda_routes._registrar_auditoria_visualizacao_agenda(
            10,
            2,
            date(2026, 9, 29),
            date(2026, 9, 29),
            None,
            None,
            None,
            "Listagem de agenda médica.",
        )

    assert remocoes == [True]


def test_atendimento_em_andamento_retorna_payload_do_servico(monkeypatch):
    app = _app()
    payload = {"emAtendimento": True, "paciente": {"nome": "Paciente Teste"}}

    monkeypatch.setattr(agenda_routes, "get_jwt_identity", lambda: "10")
    monkeypatch.setattr(agenda_routes, "unidade_id_request", lambda: 2)
    monkeypatch.setattr(
        agenda_routes,
        "buscar_atendimento_em_andamento_local",
        lambda *_args, **_kwargs: payload,
    )

    with app.test_request_context("/agenda-medica/em-atendimento?data=2026-09-29"):
        response, status = _unwrap(agenda_routes.atendimento_em_andamento)()

    assert status == 200
    assert response.get_json() == payload


def test_atendimento_em_andamento_loga_erro_de_verificacao(monkeypatch, caplog):
    app = _app()

    monkeypatch.setattr(agenda_routes, "get_jwt_identity", lambda: "10")
    monkeypatch.setattr(agenda_routes, "unidade_id_request", lambda: 2)
    monkeypatch.setattr(agenda_routes.db.session, "rollback", lambda: None)

    def falhar(*_args, **_kwargs):
        raise RuntimeError("falha local")

    monkeypatch.setattr(agenda_routes, "buscar_atendimento_em_andamento_local", falhar)

    with app.test_request_context("/agenda-medica/em-atendimento?data=2026-09-29"):
        with caplog.at_level("ERROR"):
            response, status = _unwrap(agenda_routes.atendimento_em_andamento)()

    assert status == 500
    assert response.get_json()["error"] == "Erro interno ao verificar atendimento em andamento"
    assert "Falha ao verificar atendimento em andamento" in caplog.text
    assert "usuario_id=10" in caplog.text
    assert "unidade_id=2" in caplog.text


def test_atendimento_em_andamento_retorna_400_para_unidade_invalida(monkeypatch):
    app = _app()

    monkeypatch.setattr(agenda_routes, "get_jwt_identity", lambda: "10")

    def unidade_invalida():
        raise ValueError("Unidade inválida")

    monkeypatch.setattr(agenda_routes, "unidade_id_request", unidade_invalida)

    with app.test_request_context("/agenda-medica/em-atendimento?clinicaId=abc"):
        response, status = _unwrap(agenda_routes.atendimento_em_andamento)()

    assert status == 400
    assert response.get_json()["error"] == "Unidade inválida"
