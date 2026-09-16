"""Cache facade shared by domain modules."""

from src.models.db.handler_redis_db import ConnectionDBRedis

__all__ = ["ConnectionDBRedis"]
