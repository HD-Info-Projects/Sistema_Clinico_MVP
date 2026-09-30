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


def _digest_partes(partes):
    normalizado = json.dumps(
        partes,
        default=_json_default,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(normalizado.encode("utf-8")).hexdigest()


def chave_cache(prefixo, **partes):
    return f"perf:{prefixo}:{_digest_partes(partes)}"


def marcar_se_ausente(prefixo, ttl, **partes):
    """Grava uma marca no Redis apenas se ela ainda não existir (SET NX EX).

    Retorna True quando a marca foi criada agora (primeira ocorrência dentro da
    janela `ttl`) e False quando já existia. Se o Redis estiver indisponível,
    retorna True para não suprimir o evento.
    """
    chave = f"{prefixo}:{_digest_partes(partes)}"
    with ConnectionDBRedis() as redis_connection:
        resultado = redis_connection.set_if_absent(chave, "1", ttl)
    return True if resultado is None else resultado


def apagar_marca(prefixo, **partes):
    chave = f"{prefixo}:{_digest_partes(partes)}"
    with ConnectionDBRedis() as redis_connection:
        return redis_connection.delete_cache(chave)


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
    with ConnectionDBRedis() as redis_connection:
        return redis_connection.delete_by_pattern(padrao)
