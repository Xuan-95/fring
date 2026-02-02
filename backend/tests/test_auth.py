import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.auth.jwt import create_refresh_token
from src.auth.password import get_password_hash
from src.models.orm.todo import User


@pytest.fixture
def test_user(test_db: Session) -> User:
    """Create a test user for authentication tests"""
    user = User(
        username="authuser",
        email="auth@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def test_login_success(client: TestClient, test_user: User):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "authuser", "password": "password123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, test_user: User):
    """Test login with incorrect password"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "authuser", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent username"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "password123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_inactive_user(client: TestClient, test_db: Session):
    """Test login with inactive user account"""
    inactive_user = User(
        username="inactive",
        email="inactive@example.com",
        password_hash=get_password_hash("password123"),
        is_active=False,
    )
    test_db.add(inactive_user)
    test_db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "inactive", "password": "password123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User account is inactive"


def test_logout(client: TestClient):
    """Test logout endpoint"""
    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"message": "Successfully logged out"}


def test_get_me_authenticated(client: TestClient, test_user: User):
    """Test getting current user info when authenticated"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "authuser", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "authuser"
    assert data["email"] == "auth@example.com"
    assert data["id"] == test_user.id


def test_get_me_unauthenticated(client: TestClient):
    """Test getting current user without authentication"""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_refresh_token_success(client: TestClient, test_user: User):
    """Test refreshing access token"""
    refresh_token = create_refresh_token(data={"sub": str(test_user.id)})

    response = client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_missing(client: TestClient):
    """Test refresh endpoint without refresh token"""
    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token missing"


def test_change_password_success(client: TestClient, test_user: User):
    """Test successful password change"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "authuser", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "newpassword456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Password changed successfully"}

    login_with_new = client.post(
        "/api/v1/auth/login",
        json={"username": "authuser", "password": "newpassword456"},
    )
    assert login_with_new.status_code == 200


def test_change_password_wrong_current(client: TestClient, test_user: User):
    """Test password change with incorrect current password"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "authuser", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect"
