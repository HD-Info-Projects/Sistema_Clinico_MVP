"""Database facade shared by domain modules."""

from src.models.db.handler_fb_db import (
    ConnectionDBFireBird,
    test_connection as test_firebird_connection,
)
from src.models.db.handler_sql_server import (
    ConnectionSqlServer,
    test_connection as test_sql_server_connection,
)
from src.settings.extensions import db, migrate

__all__ = [
    "ConnectionDBFireBird",
    "ConnectionSqlServer",
    "db",
    "migrate",
    "test_firebird_connection",
    "test_sql_server_connection",
]
