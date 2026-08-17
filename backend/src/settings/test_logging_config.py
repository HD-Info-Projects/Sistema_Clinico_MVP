from src import create_app
from src.settings.config import Config
from src.settings.logging_config import REDACTED, REQUEST_ID_HEADER, sanitize_log_value


def _test_app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(Config, "TESTING", True, raising=False)
    monkeypatch.setattr(Config, "LOG_FORMAT", "text")
    app = create_app()
    app.config["TESTING"] = True
    app.config["LOG_REQUESTS"] = False
    return app


def test_sanitize_log_value_mascara_dados_sensiveis():
    payload = {
        "senha": "segredo",
        "access_token": "token-secreto",
        "dados": {
            "email": "paciente@example.com",
            "observacao": "CPF 123.456.789-00 Authorization: Bearer abc.def",
        },
    }

    sanitized = sanitize_log_value(payload)

    assert sanitized["senha"] == REDACTED
    assert sanitized["access_token"] == REDACTED
    assert sanitized["dados"]["email"] == REDACTED
    assert "123.456.789-00" not in sanitized["dados"]["observacao"]
    assert "paciente@example.com" not in sanitized["dados"]["observacao"]
    assert "abc.def" not in sanitized["dados"]["observacao"]


def test_sanitize_log_value_preserva_tupla_de_args_do_logger():
    sanitized = sanitize_log_value(("ok", {"senha": "segredo"}))

    assert isinstance(sanitized, tuple)
    assert sanitized == ("ok", {"senha": REDACTED})


def test_request_id_header_recebido_e_reaproveitado(monkeypatch):
    app = _test_app(monkeypatch)

    with app.test_client() as client:
        response = client.get("/", headers={REQUEST_ID_HEADER: "req-test-123456"})

    assert response.headers[REQUEST_ID_HEADER] == "req-test-123456"


def test_request_id_e_gerado_quando_header_ausente(monkeypatch):
    app = _test_app(monkeypatch)

    with app.test_client() as client:
        response = client.get("/")

    assert len(response.headers[REQUEST_ID_HEADER]) == 32
