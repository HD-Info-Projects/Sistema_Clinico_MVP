import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

class Config:
    APP_ENV = os.getenv('APP_ENV', os.getenv('FLASK_ENV', 'development')).lower()
    IS_PRODUCTION = APP_ENV == 'production'
    FLASK_APP=os.getenv('FLASK_APP')
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES_SECONDS = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_SECONDS', 60 * 60 * 12))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES_SECONDS)
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
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

    FIREBIRD_HOST = os.getenv('FIREBIRD_HOST')
    FIREBIRD_PORT = int(os.getenv('FIREBIRD_PORT', 3050))
    FIREBIRD_DATABASE = os.getenv('FIREBIRD_DATABASE')
    FIREBIRD_USER = os.getenv('FIREBIRD_USER')
    FIREBIRD_PASSWORD = os.getenv('FIREBIRD_PASSWORD')
