import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.auth.password import get_password_hash
from src.models.orm.todo import Task, User


@pytest.fixture
def test_user(test_db: Session) -> User:
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password123"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def test_create_user_success(client: TestClient):
    """Test creating a new user"""
    response = client.post(
        "/api/v1/users/",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "password" not in data


def test_create_user_duplicate_username(client: TestClient, test_user: User):
    """Test creating user with existing username"""
    response = client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "username" in response.json()["detail"].lower()


def test_create_user_duplicate_email(client: TestClient, test_user: User):
    """Test creating user with existing email"""
    response = client.post(
        "/api/v1/users/",
        json={
            "username": "anotheruser",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_create_user_without_password(client: TestClient):
    """Test creating user without password"""
    response = client.post(
        "/api/v1/users/",
        json={
            "username": "newuser",
            "email": "new@example.com",
        },
    )

    assert response.status_code == 400
    assert "password" in response.json()["detail"].lower()


def test_get_users(client: TestClient, test_db: Session):
    """Test getting list of users"""
    users = [
        User(username=f"user{i}", email=f"user{i}@example.com", password_hash="hash")
        for i in range(3)
    ]
    test_db.add_all(users)
    test_db.commit()

    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("username" in user for user in data)


def test_get_users_with_filters(client: TestClient, test_db: Session):
    """Test getting users with username filter"""
    users = [
        User(username="alice", email="alice@example.com", password_hash="hash"),
        User(username="bob", email="bob@example.com", password_hash="hash"),
        User(username="alicia", email="alicia@example.com", password_hash="hash"),
    ]
    test_db.add_all(users)
    test_db.commit()

    response = client.get("/api/v1/users/?username=ali")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("ali" in user["username"] for user in data)


def test_get_users_pagination(client: TestClient, test_db: Session):
    """Test user list pagination"""
    users = [
        User(username=f"user{i}", email=f"user{i}@example.com", password_hash="hash")
        for i in range(10)
    ]
    test_db.add_all(users)
    test_db.commit()

    response = client.get("/api/v1/users/?skip=2&limit=3")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_user_by_id(client: TestClient, test_user: User):
    """Test getting a specific user by ID"""
    response = client.get(f"/api/v1/users/{test_user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "tasks" in data


def test_get_nonexistent_user(client: TestClient):
    """Test getting a user that doesn't exist"""
    response = client.get("/api/v1/users/99999")

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_update_user(client: TestClient, test_user: User):
    """Test updating user information"""
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json={"username": "updateduser", "email": "updated@example.com"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updateduser"
    assert data["email"] == "updated@example.com"


def test_update_user_partial(client: TestClient, test_user: User):
    """Test partial user update"""
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json={"username": "partialupdate"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "partialupdate"
    assert data["email"] == "test@example.com"


def test_update_user_duplicate_username(client: TestClient, test_db: Session, test_user: User):
    """Test updating user to duplicate username"""
    other_user = User(
        username="otheruser",
        email="other@example.com",
        password_hash="hash",
    )
    test_db.add(other_user)
    test_db.commit()

    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json={"username": "otheruser"},
    )

    assert response.status_code == 400
    assert "username" in response.json()["detail"].lower()


def test_delete_user(client: TestClient, test_user: User):
    """Test deleting a user"""
    response = client.delete(f"/api/v1/users/{test_user.id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/users/{test_user.id}")
    assert get_response.status_code == 400


def test_get_user_tasks(client: TestClient, test_db: Session, test_user: User):
    """Test getting all tasks for a user"""
    tasks = [
        Task(title=f"Task {i}", description=f"Description {i}")
        for i in range(3)
    ]
    test_db.add_all(tasks)
    test_db.commit()

    for task in tasks:
        task.assigned_users.append(test_user)
    test_db.commit()

    response = client.get(f"/api/v1/users/{test_user.id}/tasks")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_user_tasks_with_status_filter(client: TestClient, test_db: Session, test_user: User):
    """Test filtering user tasks by status"""
    from src.models.schemas import TaskStatus

    task1 = Task(title="Todo Task", status=TaskStatus.TODO)
    task2 = Task(title="In Progress Task", status=TaskStatus.IN_PROGRESS)
    test_db.add_all([task1, task2])
    test_db.commit()

    task1.assigned_users.append(test_user)
    task2.assigned_users.append(test_user)
    test_db.commit()

    response = client.get(f"/api/v1/users/{test_user.id}/tasks?status=todo")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "todo"


def test_assign_task_to_user(client: TestClient, test_db: Session, test_user: User):
    """Test assigning a task to a user"""
    task = Task(title="New Task", description="To be assigned")
    test_db.add(task)
    test_db.commit()

    response = client.post(f"/api/v1/users/{test_user.id}/tasks/{task.id}")

    assert response.status_code == 201
    assert f"Task {task.id} assigned" in response.json()["message"]

    test_db.refresh(test_user)
    assert task in test_user.tasks


def test_assign_nonexistent_task(client: TestClient, test_user: User):
    """Test assigning a nonexistent task"""
    response = client.post(f"/api/v1/users/{test_user.id}/tasks/99999")

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_assign_already_assigned_task(client: TestClient, test_db: Session, test_user: User):
    """Test assigning an already assigned task"""
    task = Task(title="Task")
    test_db.add(task)
    test_db.commit()

    task.assigned_users.append(test_user)
    test_db.commit()

    response = client.post(f"/api/v1/users/{test_user.id}/tasks/{task.id}")

    assert response.status_code == 400
    assert "already assigned" in response.json()["detail"].lower()


def test_remove_task_from_user(client: TestClient, test_db: Session, test_user: User):
    """Test removing a task from a user"""
    task = Task(title="Task to remove")
    test_db.add(task)
    test_db.commit()

    task.assigned_users.append(test_user)
    test_db.commit()

    response = client.delete(f"/api/v1/users/{test_user.id}/tasks/{task.id}")

    assert response.status_code == 204

    test_db.refresh(test_user)
    assert task not in test_user.tasks
