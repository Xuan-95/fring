import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.auth.password import get_password_hash
from src.models.orm.todo import Task, User
from src.models.schemas import TaskStatus


@pytest.fixture
def auth_user(test_db: Session) -> User:
    """Create an authenticated test user"""
    user = User(
        username="taskuser",
        email="taskuser@example.com",
        password_hash=get_password_hash("password123"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, auth_user: User) -> dict:
    """Get authentication headers for test user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "taskuser", "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_task_authenticated(client: TestClient, auth_headers: dict, test_db: Session, auth_user: User):
    """Test creating a task as authenticated user"""
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "New Task",
            "description": "Task description",
            "status": "todo",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Task"
    assert data["description"] == "Task description"
    assert "id" in data

    test_db.refresh(auth_user)
    assert len(auth_user.tasks) == 1


def test_create_task_unauthenticated(client: TestClient):
    """Test creating task without authentication"""
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "description": "Description"},
    )

    assert response.status_code == 401


def test_create_task_minimal(client: TestClient, auth_headers: dict):
    """Test creating task with minimal required fields"""
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Minimal Task"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal Task"
    assert data["status"] == "todo"


def test_get_tasks_authenticated(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test getting tasks for authenticated user"""
    tasks = [
        Task(title=f"Task {i}", description=f"Description {i}")
        for i in range(3)
    ]
    test_db.add_all(tasks)
    test_db.commit()

    for task in tasks:
        task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.get("/api/v1/tasks/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_tasks_only_assigned(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test that users only see their assigned tasks"""
    other_user = User(username="other", email="other@example.com", password_hash="hash")
    test_db.add(other_user)
    test_db.commit()

    my_task = Task(title="My Task")
    other_task = Task(title="Other Task")
    test_db.add_all([my_task, other_task])
    test_db.commit()

    my_task.assigned_users.append(auth_user)
    other_task.assigned_users.append(other_user)
    test_db.commit()

    response = client.get("/api/v1/tasks/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "My Task"


def test_get_tasks_with_status_filter(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test filtering tasks by status"""
    task1 = Task(title="Todo", status=TaskStatus.TODO)
    task2 = Task(title="In Progress", status=TaskStatus.IN_PROGRESS)
    task3 = Task(title="Completed", status=TaskStatus.COMPLETED)
    test_db.add_all([task1, task2, task3])
    test_db.commit()

    for task in [task1, task2, task3]:
        task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.get("/api/v1/tasks/?status=in_progress", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "in_progress"


def test_get_tasks_with_title_filter(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test filtering tasks by title"""
    task1 = Task(title="Buy groceries")
    task2 = Task(title="Buy tickets")
    task3 = Task(title="Write report")
    test_db.add_all([task1, task2, task3])
    test_db.commit()

    for task in [task1, task2, task3]:
        task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.get("/api/v1/tasks/?title=Buy", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("Buy" in task["title"] for task in data)


def test_get_tasks_pagination(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test task pagination"""
    tasks = [Task(title=f"Task {i}") for i in range(10)]
    test_db.add_all(tasks)
    test_db.commit()

    for task in tasks:
        task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.get("/api/v1/tasks/?skip=3&limit=4", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4


def test_get_task_by_id(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test getting a specific task by ID"""
    task = Task(title="Specific Task", description="Details here")
    test_db.add(task)
    test_db.commit()

    task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Specific Task"
    assert "assigned_to" in data


def test_get_task_not_assigned(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test accessing task not assigned to current user"""
    other_user = User(username="other", email="other@example.com", password_hash="hash")
    task = Task(title="Other's Task")
    test_db.add_all([other_user, task])
    test_db.commit()

    task.assigned_users.append(other_user)
    test_db.commit()

    response = client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers)

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


def test_get_nonexistent_task(client: TestClient, auth_headers: dict):
    """Test getting task that doesn't exist"""
    response = client.get("/api/v1/tasks/99999", headers=auth_headers)

    assert response.status_code == 404


def test_update_task(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test updating a task"""
    task = Task(title="Original", description="Original description")
    test_db.add(task)
    test_db.commit()

    task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.put(
        f"/api/v1/tasks/{task.id}",
        json={
            "title": "Updated Title",
            "description": "Updated description",
            "status": "in_progress",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"
    assert data["status"] == "in_progress"


def test_update_task_partial(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test partial task update"""
    task = Task(title="Original", description="Description", status=TaskStatus.TODO)
    test_db.add(task)
    test_db.commit()

    task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.put(
        f"/api/v1/tasks/{task.id}",
        json={"status": "completed"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Original"
    assert data["status"] == "completed"


def test_update_task_not_authorized(client: TestClient, test_db: Session, auth_headers: dict):
    """Test updating task not assigned to user"""
    other_user = User(username="other", email="other@example.com", password_hash="hash")
    task = Task(title="Other's Task")
    test_db.add_all([other_user, task])
    test_db.commit()

    task.assigned_users.append(other_user)
    test_db.commit()

    response = client.put(
        f"/api/v1/tasks/{task.id}",
        json={"title": "Hacked"},
        headers=auth_headers,
    )

    assert response.status_code == 403


def test_delete_task(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test deleting a task"""
    task = Task(title="To Delete")
    test_db.add(task)
    test_db.commit()

    task.assigned_users.append(auth_user)
    test_db.commit()
    task_id = task.id

    response = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)

    assert response.status_code == 204

    assert test_db.query(Task).filter(Task.id == task_id).first() is None


def test_delete_task_not_authorized(client: TestClient, test_db: Session, auth_headers: dict):
    """Test deleting task not assigned to user"""
    other_user = User(username="other", email="other@example.com", password_hash="hash")
    task = Task(title="Protected Task")
    test_db.add_all([other_user, task])
    test_db.commit()

    task.assigned_users.append(other_user)
    test_db.commit()

    response = client.delete(f"/api/v1/tasks/{task.id}", headers=auth_headers)

    assert response.status_code == 403


def test_get_task_users(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test getting users assigned to a task"""
    other_user = User(username="other", email="other@example.com", password_hash="hash")
    task = Task(title="Shared Task")
    test_db.add_all([other_user, task])
    test_db.commit()

    task.assigned_users.extend([auth_user, other_user])
    test_db.commit()

    response = client.get(f"/api/v1/tasks/{task.id}/users", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    usernames = [u["username"] for u in data]
    assert "taskuser" in usernames
    assert "other" in usernames


def test_assign_user_to_task(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test assigning another user to a task"""
    other_user = User(username="other", email="other@example.com", password_hash="hash")
    task = Task(title="Task to share")
    test_db.add_all([other_user, task])
    test_db.commit()

    task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.post(
        f"/api/v1/tasks/{task.id}/users/{other_user.id}",
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert "assigned" in response.json()["message"].lower()

    test_db.refresh(task)
    assert other_user in task.assigned_users


def test_assign_already_assigned_user(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test assigning user already assigned to task"""
    task = Task(title="Task")
    test_db.add(task)
    test_db.commit()

    task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.post(
        f"/api/v1/tasks/{task.id}/users/{auth_user.id}",
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "already assigned" in response.json()["detail"].lower()


def test_remove_user_from_task(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test removing a user from a task"""
    other_user = User(username="other", email="other@example.com", password_hash="hash")
    task = Task(title="Shared Task")
    test_db.add_all([other_user, task])
    test_db.commit()

    task.assigned_users.extend([auth_user, other_user])
    test_db.commit()

    response = client.delete(
        f"/api/v1/tasks/{task.id}/users/{other_user.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    test_db.refresh(task)
    assert other_user not in task.assigned_users
    assert auth_user in task.assigned_users


def test_update_task_status(client: TestClient, test_db: Session, auth_user: User, auth_headers: dict):
    """Test updating task status via PATCH endpoint"""
    task = Task(title="Task", status=TaskStatus.TODO)
    test_db.add(task)
    test_db.commit()

    task.assigned_users.append(auth_user)
    test_db.commit()

    response = client.patch(
        f"/api/v1/tasks/{task.id}/status?status=completed",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
