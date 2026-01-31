from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from src.config.settings import auth_settings


def create_access_token(data: dict[str, Any]) -> str:
    """Create a short-lived JWT access token (30 minutes)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, auth_settings.JWT_SECRET_KEY, algorithm=auth_settings.JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a long-lived JWT refresh token (7 days)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, auth_settings.JWT_SECRET_KEY, algorithm=auth_settings.JWT_ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        JWTError: If token is invalid, expired, or type doesn't match
    """
    payload = jwt.decode(token, auth_settings.JWT_SECRET_KEY, algorithms=[auth_settings.JWT_ALGORITHM])

    if payload.get("type") != token_type:
        raise JWTError(f"Invalid token type. Expected {token_type}, got {payload.get('type')}")

    return payload
