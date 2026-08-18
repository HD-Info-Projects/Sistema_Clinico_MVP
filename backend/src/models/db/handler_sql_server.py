import os
import logging

import pyodbc
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)


def _get_env(name, default=None, required=False):
    value = os.getenv(name)
    if value:
        return value

    if required:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")

    return default


class ConnectionSqlServer:

    def __init__(self):
        self.host = _get_env("SQLSERVER_HOST", required=True)
        self.port = _get_env("SQLSERVER_PORT", default="1433")
        self.database = _get_env("SQLSERVER_DATABASE", default="master")
        self.user = _get_env("SQLSERVER_USER", required=True)
        self.password = _get_env("SQLSERVER_PASSWORD", required=True)
        self.driver = _get_env(
            "SQLSERVER_DRIVER",
            default="ODBC Driver 18 for SQL Server",
        )
        self.encrypt = _get_env("SQLSERVER_ENCRYPT", default="yes")
        self.trust_certificate = _get_env(
            "SQLSERVER_TRUST_CERTIFICATE",
            default="yes",
        )
        self.timeout = int(_get_env("SQLSERVER_TIMEOUT", default="10"))
        self._connection = None
        self._connect()

    def _server(self):
        if self.port:
            return f"{self.host},{self.port}"

        return self.host

    def _connection_string(self):
        return ";".join([
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self._server()}",
            f"DATABASE={self.database}",
            f"UID={self.user}",
            f"PWD={self.password}",
            f"Encrypt={self.encrypt}",
            f"TrustServerCertificate={self.trust_certificate}",
            f"Connection Timeout={self.timeout}",
        ])

    def _connect(self):
        self._connection = pyodbc.connect(
            self._connection_string(),
            timeout=self.timeout,
        )
        self._connection.timeout = self.timeout

    def cursor(self):
        return self._connection.cursor()

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def test_connection():
    try:
        with ConnectionSqlServer() as con:
            cursor = con.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()

        logger.info("Conexao SQL Server OK: %s", result[0])
        return True

    except Exception:
        logger.exception("Erro ao conectar no SQL Server")
        return False


if __name__ == "__main__":
    ok = test_connection()
    raise SystemExit(0 if ok else 1)
