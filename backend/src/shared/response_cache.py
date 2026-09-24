import hashlib
import json
from datetime import date, datetime, time
from decimal import Decimal

from flask import current_app

from src.models.db.handler_redis_db import ConnectionDBRedis


def _json_default(valor):
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, time):
        return valor.strftime("%H:%M:%S")
    if isinstance(valor, Decimal):
        return int(valor) if valor == int(valor) else float(valor)
    raise TypeError(f"Tipo não serializável: {type(valor).__name__}")


def cache_ttl(default=60):
    try:
        return int(current_app.config.get("PERFORMANCE_CACHE_TTL_SECONDS", default))
    except (TypeError, ValueError):
        return default


def chave_cache(prefixo, **partes):
    normalizado = json.dumps(
        partes,
        default=_json_default,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(normalizado.encode("utf-8")).hexdigest()
    return f"perf:{prefixo}:{digest}"


def obter_cache_json(chave):
    valor = ConnectionDBRedis().get_cache(chave)
    if valor is None:
        return None

    try:
        return json.loads(valor)
    except (TypeError, ValueError):
        return None


def salvar_cache_json(chave, payload, ttl=None):
    ttl = ttl or cache_ttl()
    try:
        serializado = json.dumps(
            payload,
            default=_json_default,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    except TypeError:
        return None

    return ConnectionDBRedis().set_cache(chave, serializado, ttl=ttl)


def apagar_cache_por_padrao(padrao):
    redis_connection = ConnectionDBRedis()
    connection = redis_connection.get_connection()
    if connection is None:
        return 0

    apagados = 0
    try:
        for chave in connection.scan_iter(match=padrao):
            apagados += connection.delete(chave)
    except Exception:
        current_app.logger.exception("Falha ao apagar cache Redis por padrão")
        return apagados
    finally:
        connection.close()

    return apagados
