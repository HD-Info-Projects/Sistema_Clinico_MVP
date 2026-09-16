"""Security facade shared by domain modules."""

from src.security.decorators import active_user_required, roles_required
from src.security.jwt_blocklist import is_jti_revoked, revoke_jti
from src.security.passwords import (
    DEFAULT_MIN_PASSWORD_LENGTH,
    PASSWORD_HASH_PREFIXES,
    hash_password,
    is_hashed_password,
    validate_password_strength,
    verify_password,
)
from src.security.unidades import unidade_atual_required, unidade_id_request

__all__ = [
    "DEFAULT_MIN_PASSWORD_LENGTH",
    "PASSWORD_HASH_PREFIXES",
    "active_user_required",
    "hash_password",
    "is_hashed_password",
    "is_jti_revoked",
    "roles_required",
    "revoke_jti",
    "unidade_atual_required",
    "unidade_id_request",
    "validate_password_strength",
    "verify_password",
]
