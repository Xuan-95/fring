from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from src.auth.jwt import verify_token
from src.db.connection import _get_db
from src.models.orm.todo import User


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    access_token_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
    db: Session = Depends(_get_db),
) -> User:
    """
    Dependency to get the current authenticated user from Authorization header or cookie.
    Supports both Bearer token (header) and cookie-based authentication.

    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found/inactive
    """
    print(f"🔍 Authorization header: {authorization}")
    print(f"🔍 Cookie token: {access_token_cookie}")

    # Try to extract token from Authorization header first
    access_token = None
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.replace("Bearer ", "")
        print(f"🔵 Token from header: {access_token[:20]}...")
    # Fallback to cookie if header not present
    elif access_token_cookie:
        access_token = access_token_cookie
        print(f"🔵 Token from cookie: {access_token[:20]}...")

    if not access_token:
        print("🔴 No token found!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        print(f"🔵 Verifying token...")
        payload = verify_token(access_token, token_type="access")
        print(f"🟢 Token verified! Payload: {payload}")
        user_id_str = payload.get("sub")
        if user_id_str is None:
            print("🔴 No user_id in payload!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        user_id = int(user_id_str)
        print(f"🔵 User ID: {user_id}")
    except JWTError as e:
        print(f"🔴 JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    except Exception as e:
        print(f"🔴 Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"🔴 User not found: {user_id}")
    elif not user.is_active:
        print(f"🔴 User inactive: {user_id}")
    else:
        print(f"🟢 User authenticated: {user.username}")

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
