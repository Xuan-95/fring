from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from src.auth.jwt import verify_token
from src.db.connection import _get_db
from src.models.orm.todo import User


async def get_current_user(
    access_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(_get_db),
) -> User:
    """
    Dependency to get the current authenticated user from the access token cookie.

    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found/inactive
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = verify_token(access_token, token_type="access")
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
