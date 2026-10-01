from flask import current_app
from redis import Redis
from rq import Queue


def get_spdata_queue():
    connection = Redis.from_url(
        current_app.config["RQ_REDIS_URL"],
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    return Queue(
        current_app.config["SPDATA_QUEUE_NAME"],
        connection=connection,
        default_timeout=current_app.config["SPDATA_JOB_TIMEOUT_SECONDS"],
    )
