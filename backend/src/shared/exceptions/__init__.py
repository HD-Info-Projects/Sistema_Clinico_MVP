"""Exception aliases used by modularized services.

The legacy services already use Python built-in exception types. These aliases
provide semantic import names for new modules without changing catch behavior.
"""

AuthorizationError = PermissionError
ConfigurationError = RuntimeError
ConflictError = RuntimeError
ForbiddenError = PermissionError
IntegrationError = RuntimeError
NotFoundError = LookupError
ValidationError = ValueError

__all__ = [
    "AuthorizationError",
    "ConfigurationError",
    "ConflictError",
    "ForbiddenError",
    "IntegrationError",
    "NotFoundError",
    "ValidationError",
]
