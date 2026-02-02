from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.orm.todo import Task, User
from src.models.schemas import TaskStatus


def test_create_user(test_db: Session):
    """Test creating a user with all required fields"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert isinstance(user.created_at, datetime)


def test_user_unique_username(test_db: Session):
    """Test that username must be unique"""
    user1 = User(username="testuser", email="test1@example.com", password_hash="hash")
    user2 = User(username="testuser", email="test2@example.com", password_hash="hash")

    test_db.add(user1)
    test_db.commit()

    test_db.add(user2)
    with pytest.raises(IntegrityError):
        test_db.commit()


def test_user_unique_email(test_db: Session):
    """Test that email must be unique"""
    user1 = User(username="user1", email="test@example.com", password_hash="hash")
    user2 = User(username="user2", email="test@example.com", password_hash="hash")

    test_db.add(user1)
    test_db.commit()

    test_db.add(user2)
    with pytest.raises(IntegrityError):
        test_db.commit()


def test_create_task(test_db: Session):
    """Test creating a task"""
    task = Task(
        title="Test Task",
        description="Test description",
        status=TaskStatus.TODO,
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)

    assert task.id is not None
    assert task.title == "Test Task"
    assert task.description == "Test description"
    assert task.status == TaskStatus.TODO
    assert isinstance(task.created_at, datetime)
    assert isinstance(task.updated_at, datetime)


def test_user_task_relationship(test_db: Session):
    """Test many-to-many relationship between users and tasks"""
    user1 = User(username="user1", email="user1@example.com", password_hash="hash")
    user2 = User(username="user2", email="user2@example.com", password_hash="hash")
    task = Task(title="Shared Task", description="Shared between users")

    test_db.add_all([user1, user2, task])
    test_db.commit()

    task.assigned_users.extend([user1, user2])
    test_db.commit()

    assert len(task.assigned_users) == 2
    assert user1 in task.assigned_users
    assert user2 in task.assigned_users
    assert task in user1.tasks
    assert task in user2.tasks


def test_cascade_delete_user(test_db: Session):
    """Test that deleting a user removes task assignments but not tasks"""
    user = User(username="user", email="user@example.com", password_hash="hash")
    task = Task(title="Task", description="Test")

    test_db.add_all([user, task])
    test_db.commit()

    task.assigned_users.append(user)
    test_db.commit()

    test_db.delete(user)
    test_db.commit()

    test_db.refresh(task)
    assert len(task.assigned_users) == 0
    assert test_db.query(Task).filter(Task.id == task.id).first() is not None


def test_cascade_delete_task(test_db: Session):
    """Test that deleting a task removes assignments but not users"""
    user = User(username="user", email="user@example.com", password_hash="hash")
    task = Task(title="Task", description="Test")

    test_db.add_all([user, task])
    test_db.commit()

    task.assigned_users.append(user)
    test_db.commit()

    test_db.delete(task)
    test_db.commit()

    test_db.refresh(user)
    assert len(user.tasks) == 0
    assert test_db.query(User).filter(User.id == user.id).first() is not None
