from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_PASSWORD_BYTES = 72


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_length(password: str) -> None:
    """
    Validate password meets length requirements.

    Raises:
        ValueError: If password is too short or exceeds bcrypt's 72-byte limit
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    password_bytes = len(password.encode("utf-8"))
    if password_bytes > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password too long ({password_bytes} bytes). "
            f"Maximum is {MAX_PASSWORD_BYTES} bytes"
        )


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Raises:
        ValueError: If password doesn't meet length requirements
    """
    validate_password_length(password)
    return pwd_context.hash(password)
