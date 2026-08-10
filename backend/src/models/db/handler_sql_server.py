import os

import pyodbc
from dotenv import load_dotenv


load_dotenv()

_last_success_host = None


def _get_env(name, default=None, required=False):
    value = os.getenv(name)
    if value:
        return value

    if required:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")

    return default


def _parse_hosts(raw):
    return [host.strip() for host in raw.split(",") if host.strip()]


class ConnectionSqlServer:

    def __init__(self, host=None):
        self.hosts = _parse_hosts(_get_env("SQLSERVER_HOST", required=True))
        if not self.hosts:
            raise RuntimeError("SQLSERVER_HOST ausente ou vazio")

        if host is not None:
            self.hosts = [host]

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

    @classmethod
    def ordered_hosts(cls):
        hosts = _parse_hosts(_get_env("SQLSERVER_HOST", required=True))
        if not hosts:
            raise RuntimeError("SQLSERVER_HOST ausente ou vazio")

        if _last_success_host in hosts and hosts[0] != _last_success_host:
            hosts = [_last_success_host] + [h for h in hosts if h != _last_success_host]

        return hosts

    def _connect(self):
        global _last_success_host

        hosts = self.hosts
        if _last_success_host in hosts and hosts[0] != _last_success_host:
            hosts = [_last_success_host] + [h for h in hosts if h != _last_success_host]

        last_error = None
        for host in hosts:
            self.host = host
            try:
                self._connection = pyodbc.connect(
                    self._connection_string(),
                    timeout=self.timeout,
                )
                self._connection.timeout = self.timeout
                _last_success_host = host
                return
            except Exception as e:
                last_error = e
                continue

        if last_error is not None:
            raise last_error

        raise RuntimeError("Nenhum host SQL Server configurado")

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
    last_error = None
    for host in ConnectionSqlServer.ordered_hosts():
        try:
            with ConnectionSqlServer(host=host) as con:
                cursor = con.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()

            print("Conexão SQL Server OK:", result[0], f"(host: {host})")
            return True

        except Exception as e:
            last_error = e
            print("Falha no host:", host, "-", e)

    print("Erro ao conectar no SQL Server:", last_error)
    return False


if __name__ == "__main__":
    ok = test_connection()
    raise SystemExit(0 if ok else 1)
