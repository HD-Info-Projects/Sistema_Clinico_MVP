import os
from datetime import timedelta

from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()


def _env_bool(name, default=False):
    default_value = 'true' if default else 'false'
    return os.getenv(name, default_value).lower() == 'true'


def _database_uri():
    explicit_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if explicit_uri:
        return explicit_uri

    required = ('MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE')
    if not all(os.getenv(key) for key in required):
        return None

    return URL.create(
        'mysql+pymysql',
        username=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        host=os.getenv('MYSQL_HOST', 'mysql'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        database=os.getenv('MYSQL_DATABASE'),
    )


class Config:
    APP_ENV = os.getenv('APP_ENV', os.getenv('FLASK_ENV', 'development')).lower()
    IS_PRODUCTION = APP_ENV == 'production'
    FLASK_APP=os.getenv('FLASK_APP')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json' if IS_PRODUCTION else 'text').lower()
    LOG_COLOR = os.getenv('LOG_COLOR', 'auto').lower()
    LOG_REQUESTS = _env_bool('LOG_REQUESTS', True)
    LOG_HEALTHCHECKS = _env_bool('LOG_HEALTHCHECKS', False)
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES_SECONDS = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_SECONDS', 60 * 60 * 12))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES_SECONDS)
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')
    LOGIN_RATE_LIMIT_IP = os.getenv('LOGIN_RATE_LIMIT_IP', '10 per minute')
    LOGIN_RATE_LIMIT_EMAIL = os.getenv('LOGIN_RATE_LIMIT_EMAIL', '5 per minute')
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv('CORS_ORIGINS', '').split(',')
        if origin.strip()
    ]
    SECURITY_HSTS_ENABLED = os.getenv('SECURITY_HSTS_ENABLED', 'false').lower() == 'true'
    SECURITY_HSTS_MAX_AGE = int(os.getenv('SECURITY_HSTS_MAX_AGE', 31536000))
    ENABLE_TTS = os.getenv('ENABLE_TTS', 'false').lower() == 'true'
    TTS_RATE_LIMIT = os.getenv('TTS_RATE_LIMIT', '30 per minute')
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    JWT_BLOCKLIST_STORAGE_URI = os.getenv('JWT_BLOCKLIST_STORAGE_URI') or RATELIMIT_STORAGE_URI

    LGPD_RETENTION_LOGS_INTEGRACAO_DAYS = int(
        os.getenv('LGPD_RETENTION_LOGS_INTEGRACAO_DAYS', 180)
    )
    LGPD_RETENTION_FILA_SINCRONIZACAO_DAYS = int(
        os.getenv('LGPD_RETENTION_FILA_SINCRONIZACAO_DAYS', 90)
    )
    LGPD_RETENTION_AUDITORIA_DAYS = int(
        os.getenv('LGPD_RETENTION_AUDITORIA_DAYS', 1825)
    )
    LGPD_RETENTION_SPDATA_ESPELHO_DAYS = int(
        os.getenv('LGPD_RETENTION_SPDATA_ESPELHO_DAYS', 730)
    )
    LGPD_RETENTION_BATCH_SIZE = int(os.getenv('LGPD_RETENTION_BATCH_SIZE', 500))

    FIREBIRD_HOST = os.getenv('FIREBIRD_HOST')
    FIREBIRD_PORT = int(os.getenv('FIREBIRD_PORT', 3050))
    FIREBIRD_DATABASE = os.getenv('FIREBIRD_DATABASE')
    FIREBIRD_USER = os.getenv('FIREBIRD_USER')
    FIREBIRD_PASSWORD = os.getenv('FIREBIRD_PASSWORD')
