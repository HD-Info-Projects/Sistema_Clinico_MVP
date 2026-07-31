from werkzeug.security import check_password_hash, generate_password_hash


PASSWORD_HASH_PREFIXES = (
    "scrypt:",
    "pbkdf2:",
)


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Senha não pode ser vazia")

    return generate_password_hash(password)


def is_hashed_password(stored_password: str | None) -> bool:
    return bool(stored_password and stored_password.startswith(PASSWORD_HASH_PREFIXES))


def verify_password(stored_password: str | None, password: str | None) -> tuple[bool, bool]:
    if not stored_password or not password:
        return False, False

    if is_hashed_password(stored_password):
        try:
            return check_password_hash(stored_password, password), False
        except ValueError:
            return False, False

    return stored_password == password, True
