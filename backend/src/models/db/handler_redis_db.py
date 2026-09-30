from dotenv import load_dotenv
import logging
import os
import threading
import time

try:
    import redis
    from redis.backoff import NoBackoff
    from redis.retry import Retry
except ImportError:
    redis = None

load_dotenv()

logger = logging.getLogger(__name__)


def _float_env(nome, default):
    try:
        return float(os.getenv(nome, default))
    except (TypeError, ValueError):
        return default


# Timeouts curtos e sem retry: o Redis é só cache, então se ele estiver fora do ar
# a aplicação deve seguir sem cache em vez de travar segundos em cada operação.
REDIS_CONNECT_TIMEOUT = _float_env("REDIS_CONNECT_TIMEOUT", 0.3)
REDIS_SOCKET_TIMEOUT = _float_env("REDIS_SOCKET_TIMEOUT", 1.0)
# Após uma falha, o Redis é ignorado por essa janela (circuit breaker).
REDIS_CIRCUIT_SECONDS = _float_env("REDIS_CIRCUIT_SECONDS", 30.0)

_lock = threading.Lock()
_pool = None
_indisponivel_ate = 0.0


def redis_disponivel():
    return redis is not None and time.monotonic() >= _indisponivel_ate


def registrar_falha_redis(exc=None):
    """Abre o circuito por REDIS_CIRCUIT_SECONDS e loga uma única vez por janela."""
    global _indisponivel_ate
    with _lock:
        agora = time.monotonic()
        ja_aberto = agora < _indisponivel_ate
        _indisponivel_ate = agora + REDIS_CIRCUIT_SECONDS
    if not ja_aberto:
        logger.warning(
            "Redis indisponível (%s). Cache desativado pelos próximos %.0fs.",
            exc.__class__.__name__ if exc else "erro",
            REDIS_CIRCUIT_SECONDS,
        )


def _get_pool():
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                _pool = redis.ConnectionPool(
                    host=os.getenv("REDIS_HOST") or "localhost",
                    port=int(os.getenv("REDIS_PORT", 6379)),
                    db=int(os.getenv("REDIS_DB", 0)),
                    password=os.getenv("REDIS_PASSWORD") or None,
                    decode_responses=True,
                    socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
                    socket_timeout=REDIS_SOCKET_TIMEOUT,
                    retry=Retry(NoBackoff(), 0),
                )
    return _pool


class ConnectionDBRedis:

    def __init__(self):
        self._connection = None

    def get_connection(self):
        """Retorna um cliente Redis (pool compartilhado) ou None se indisponível."""
        if not redis_disponivel():
            return None

        if self._connection is None:
            self._connection = redis.Redis(connection_pool=_get_pool())
        return self._connection

    def _executar(self, operacao, default=None):
        connection = self.get_connection()
        if connection is None:
            return default
        try:
            return operacao(connection)
        except redis.RedisError as exc:
            registrar_falha_redis(exc)
            return default

    def ping(self):
        return bool(self._executar(lambda c: c.ping(), default=False))

    def set_cache(self, key, value, ttl=300):
        return self._executar(lambda c: c.setex(key, ttl, value))

    def get_cache(self, key):
        return self._executar(lambda c: c.get(key))

    def delete_cache(self, key):
        return self._executar(lambda c: c.delete(key))

    def set_if_absent(self, key, value, ttl):
        """SET NX EX. Retorna True/False, ou None se o Redis estiver indisponível."""
        resultado = self._executar(lambda c: c.set(key, value, nx=True, ex=int(ttl)), default=None)
        if resultado is None and not redis_disponivel():
            return None
        return bool(resultado)

    def delete_by_pattern(self, padrao):
        def apagar(connection):
            chaves = list(connection.scan_iter(match=padrao, count=500))
            return connection.delete(*chaves) if chaves else 0

        return self._executar(apagar, default=0) or 0

    def close(self):
        # Com pool compartilhado, close() apenas devolve as conexões ao pool.
        if self._connection is not None:
            self._connection.close()
        self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
