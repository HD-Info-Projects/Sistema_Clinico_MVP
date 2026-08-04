import time

try:
    import redis
except ImportError:  # pragma: no cover - dependency exists in production requirements
    redis = None

from flask import current_app


_fallback_blocklist = {}
_redis_client = None


def _cleanup_fallback(now=None):
    now = now or time.time()
    expirados = [jti for jti, exp in _fallback_blocklist.items() if exp <= now]
    for jti in expirados:
        _fallback_blocklist.pop(jti, None)


def _get_redis_client():
    global _redis_client

    if redis is None:
        return None

    uri = current_app.config.get("JWT_BLOCKLIST_STORAGE_URI")
    if not uri or uri == "memory://":
        return None

    if _redis_client is None:
        _redis_client = redis.Redis.from_url(uri, decode_responses=True)

    return _redis_client


def revoke_jti(jti, expires_at):
    if not jti:
        return

    ttl = max(int((expires_at or time.time()) - time.time()), 1)
    key = f"jwt:blocklist:{jti}"

    try:
        client = _get_redis_client()
        if client is not None:
            client.setex(key, ttl, "1")
            return
    except Exception:
        current_app.logger.exception("Falha ao revogar JWT no Redis")

    _cleanup_fallback()
    _fallback_blocklist[jti] = time.time() + ttl


def is_jti_revoked(jti):
    if not jti:
        return False

    key = f"jwt:blocklist:{jti}"

    try:
        client = _get_redis_client()
        if client is not None:
            return bool(client.exists(key))
    except Exception:
        current_app.logger.exception("Falha ao consultar blocklist JWT no Redis")

    _cleanup_fallback()
    return jti in _fallback_blocklist
