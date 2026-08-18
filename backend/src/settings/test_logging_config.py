import json
import logging

from src import create_app
from src.settings.config import Config
from src.settings.logging_config import (
    REDACTED,
    REQUEST_ID_HEADER,
    ColorizingFormatter,
    JsonFormatter,
    sanitize_log_value,
    should_color_logs,
)


def _test_app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(Config, "TESTING", True, raising=False)
    monkeypatch.setattr(Config, "LOG_FORMAT", "text")
    app = create_app()
    app.config["TESTING"] = True
    app.config["LOG_REQUESTS"] = False
    return app


def _log_record(level=logging.ERROR, message="Erro cpf=123.456.789-00"):
    record = logging.LogRecord(
        "teste",
        level,
        __file__,
        1,
        message,
        (),
        None,
    )
    record.status_code = 500
    record.duration_ms = 12.34
    record.request_id = "req-test-123456"
    record.http_method = "GET"
    record.path = "/teste"
    record.remote_addr = "127.0.0.1"
    return record


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


def test_should_color_logs_respeita_opcoes(monkeypatch):
    class TerminalFake:
        def isatty(self):
            return True

    monkeypatch.delenv("NO_COLOR", raising=False)

    assert should_color_logs("true") is True
    assert should_color_logs("false") is False
    assert should_color_logs("auto", TerminalFake()) is True


def test_colorizing_formatter_colore_nivel_e_status_sem_expor_sensiveis():
    formatter = ColorizingFormatter("%(levelname)s status=%(status_code)s %(message)s")
    output = formatter.format(_log_record())

    assert "\033[" in output
    assert "ERROR" in output
    assert "500" in output
    assert "123.456.789-00" not in output
    assert REDACTED in output


def test_json_formatter_nao_inclui_ansi():
    formatter = JsonFormatter()
    record = _log_record(message="\033[31mErro\033[0m cpf=123.456.789-00")
    output = formatter.format(record)

    assert "\033[" not in output

    payload = json.loads(output)
    assert payload["level"] == "ERROR"
    assert payload["status_code"] == 500
    assert "\033[" not in payload["message"]
    assert "123.456.789-00" not in payload["message"]
    assert REDACTED in payload["message"]


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
