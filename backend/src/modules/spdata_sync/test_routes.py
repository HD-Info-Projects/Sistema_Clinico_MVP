from types import SimpleNamespace

from flask import Flask

from src.modules.spdata_sync import routes
from src.modules.spdata_sync.service import ActiveJobError, InvalidTargetError


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


def _app():
    app = Flask(__name__)
    app.config.update(TESTING=True)
    return app


def test_criar_rejeita_target_invalido(monkeypatch):
    monkeypatch.setattr(routes, "get_jwt_identity", lambda: "7")
    monkeypatch.setattr(
        routes,
        "criar_e_enfileirar_job",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(InvalidTargetError("Catálogo inválido.")),
    )

    with _app().test_request_context(
        "/admin/spdata-sync/jobs",
        method="POST",
        json={"target": "PACIENTES"},
    ):
        response, status = _unwrap(routes.criar)()

    assert status == 400
    assert response.get_json()["error"] == "Catálogo inválido."


def test_criar_retorna_job_ativo_em_conflito(monkeypatch):
    active_job = SimpleNamespace(id=12, to_dict=lambda: {"id": 12, "status": "RUNNING"})
    monkeypatch.setattr(routes, "get_jwt_identity", lambda: "7")
    monkeypatch.setattr(
        routes,
        "criar_e_enfileirar_job",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ActiveJobError(active_job)),
    )

    with _app().test_request_context(
        "/admin/spdata-sync/jobs",
        method="POST",
        json={"target": "TODOS"},
    ):
        response, status = _unwrap(routes.criar)()

    assert status == 409
    assert response.get_json()["job"]["id"] == 12


def test_criar_retorna_202_com_job_enfileirado(monkeypatch):
    job = SimpleNamespace(id=21, to_dict=lambda: {"id": 21, "status": "QUEUED"})
    monkeypatch.setattr(routes, "get_jwt_identity", lambda: "7")
    monkeypatch.setattr(routes, "criar_e_enfileirar_job", lambda *_args, **_kwargs: job)

    with _app().test_request_context(
        "/admin/spdata-sync/jobs",
        method="POST",
        json={"target": "TODOS"},
    ):
        response = _unwrap(routes.criar)()

    assert response.status_code == 202
    assert response.get_json()["job"]["id"] == 21
    assert response.headers["Location"].endswith("/21")


def test_listar_rejeita_paginacao_invalida():
    with _app().test_request_context("/admin/spdata-sync/jobs?limit=abc"):
        response, status = _unwrap(routes.listar)()

    assert status == 400
    assert response.get_json()["error"] == "Paginação inválida."
