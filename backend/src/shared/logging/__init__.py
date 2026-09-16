"""Logging facade shared by the application factory and modules."""

from src.settings.logging_config import (
    REQUEST_ID_HEADER,
    REDACTED,
    ColorizingFormatter,
    JsonFormatter,
    RequestContextFilter,
    SanitizingFormatter,
    configure_logging,
    make_request_id,
    sanitize_log_value,
    sanitize_text,
    should_color_logs,
    strip_ansi,
)

__all__ = [
    "ColorizingFormatter",
    "JsonFormatter",
    "REDACTED",
    "REQUEST_ID_HEADER",
    "RequestContextFilter",
    "SanitizingFormatter",
    "configure_logging",
    "make_request_id",
    "sanitize_log_value",
    "sanitize_text",
    "should_color_logs",
    "strip_ansi",
]
