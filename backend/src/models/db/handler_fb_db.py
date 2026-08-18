import firebird.driver as fdb
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)


def _get_env(*names, default=None, required=False):
    for name in names:
        value = os.getenv(name)
        if value:
            return value

    if required:
        raise RuntimeError(
            f"Variável de ambiente obrigatória ausente: {', '.join(names)}"
        )

    return default


class ConnectionDBFireBird:
    
    def __init__(self):
        self.host = _get_env("FIREBIRD_HOST_teste", "FIREBIRD_HOST", required=True)
        self.port = _get_env("FIREBIRD_PORT_teste", "FIREBIRD_PORT")
        self.database = _get_env("FIREBIRD_DATABASE_teste", "FIREBIRD_DATABASE", required=True)
        self.user = _get_env("FIREBIRD_USER_teste", "FIREBIRD_USER", required=True)
        self.password = _get_env("FIREBIRD_PASSWORD_teste", "FIREBIRD_PASSWORD", required=True)
        self.charset = _get_env("FIREBIRD_CHARSET_teste", "FIREBIRD_CHARSET", default="WIN1252")
        self._connection = None
        self._connect()

    def _connect(self):
        if self.port:
            database_url = f"{self.host}/{self.port}:{self.database}"
        else:
            database_url = f"{self.host}:{self.database}"

        self._connection = fdb.connect(
            database_url,
            user=self.user,
            password=self.password,
            charset=self.charset
        )

    def cursor(self):
        return self._connection.cursor()

    def close(self):
        if self._connection:
            self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        

def test_connection():
    try:
        with ConnectionDBFireBird() as con:
            cur = con.cursor()
            cur.execute("SELECT 1 FROM RDB$DATABASE")
            result = cur.fetchone()
            cur.close()

        logger.info("Conexao Firebird OK: %s", result[0])
        return True

    except Exception:
        logger.exception("Erro ao conectar no Firebird")
        return False


if __name__ == "__main__":
    ok = test_connection()
    raise SystemExit(0 if ok else 1)
