import json
import logging
import logging.config
import re
import uuid
from datetime import datetime, timezone

from flask import g, has_request_context, request
from flask.logging import default_handler


REQUEST_ID_HEADER = "X-Request-ID"
REDACTED = "[REDACTED]"

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
CNPJ_PATTERN = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
BEARER_PATTERN = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*")
SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)([\"']?)(authorization|cookie|jwt|password|senha|secret|token|access_token|"
    r"refresh_token|api_key|cpf|cnpj|cnpj_cpf|telefone|celular|phone|email)\b"
    r"\1"
    r"\s*[:=]\s*"
    r"(\"[^\"]*\"|'[^']*'|[^\s,;})]+)"
)

SENSITIVE_KEYS = frozenset({
    "authorization",
    "cookie",
    "jwt",
    "password",
    "senha",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "cpf",
    "cnpj",
    "cnpj_cpf",
    "cnpjcpf",
    "telefone",
    "celular",
    "phone",
    "email",
})


def sanitize_text(value):
    text = str(value)
    text = BEARER_PATTERN.sub(r"\1" + REDACTED, text)
    text = SENSITIVE_ASSIGNMENT_PATTERN.sub(lambda match: f"{match.group(2)}={REDACTED}", text)
    text = CNPJ_PATTERN.sub(REDACTED, text)
    text = CPF_PATTERN.sub(REDACTED, text)
    text = EMAIL_PATTERN.sub(REDACTED, text)
    return text


def sanitize_log_value(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if normalized_key in SENSITIVE_KEYS:
                sanitized[key] = REDACTED
            else:
                sanitized[key] = sanitize_log_value(item)
        return sanitized

    if isinstance(value, tuple):
        return tuple(sanitize_log_value(item) for item in value)

    if isinstance(value, (list, set)):
        return [sanitize_log_value(item) for item in value]

    if value is None or isinstance(value, (bool, int, float)):
        return value

    return sanitize_text(value)


def make_request_id(value=None):
    candidate = str(value or "").strip()
    if REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate

    return uuid.uuid4().hex


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            record.request_id = getattr(g, "request_id", None) or "-"
            record.http_method = request.method
            record.path = request.path
            record.remote_addr = request.headers.get(
                "X-Forwarded-For",
                request.remote_addr or "-",
            ).split(",", 1)[0].strip()
        else:
            record.request_id = getattr(record, "request_id", "-")
            record.http_method = getattr(record, "http_method", "-")
            record.path = getattr(record, "path", "-")
            record.remote_addr = getattr(record, "remote_addr", "-")

        record.status_code = getattr(record, "status_code", None)
        record.duration_ms = getattr(record, "duration_ms", None)
        return True


class SanitizingFormatter(logging.Formatter):
    def format(self, record):
        original_args = record.args
        try:
            record.args = sanitize_log_value(original_args)
            return sanitize_text(super().format(record))
        finally:
            record.args = original_args


class JsonFormatter(logging.Formatter):
    def format(self, record):
        original_args = record.args
        record.args = sanitize_log_value(original_args)
        try:
            message = sanitize_text(record.getMessage())
        finally:
            record.args = original_args

        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                timezone.utc,
            ).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "request_id": getattr(record, "request_id", "-"),
            "method": getattr(record, "http_method", "-"),
            "path": getattr(record, "path", "-"),
            "remote_addr": getattr(record, "remote_addr", "-"),
        }

        status_code = getattr(record, "status_code", None)
        if status_code is not None:
            payload["status_code"] = status_code

        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms

        if record.exc_info:
            payload["exception"] = sanitize_text(self.formatException(record.exc_info))

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(app):
    log_level = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    log_format = str(app.config.get("LOG_FORMAT", "text")).lower()
    formatter = "json" if log_format == "json" else "text"

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {"()": RequestContextFilter},
        },
        "formatters": {
            "json": {"()": JsonFormatter},
            "text": {
                "()": SanitizingFormatter,
                "format": (
                    "%(asctime)s %(levelname)s [%(name)s] "
                    "request_id=%(request_id)s method=%(http_method)s path=%(path)s "
                    "status=%(status_code)s duration_ms=%(duration_ms)s %(message)s"
                ),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "level": log_level,
                "formatter": formatter,
                "filters": ["request_context"],
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "src": {"level": log_level, "propagate": True},
            "werkzeug": {"level": "WARNING", "propagate": True},
        },
    })

    app.logger.removeHandler(default_handler)
    app.logger.setLevel(log_level)
