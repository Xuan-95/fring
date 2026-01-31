from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.auth.password import get_password_hash
from src.db.connection import _get_db
from src.models.exceptions import UserException
from src.models.orm.todo import Task, User
from src.models.schemas import (
    TaskResponse,
    TaskStatus,
    UserModel,
    UserResponse,
    UserUpdate,
    UserWithTasks,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, description="""Create new user"""
)
def create_user(user: UserModel, db: Session = Depends(_get_db)):
    """
    Create a new user in DB
    """
    if not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )

    if len(user.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    existing_user = (
        db.query(User)
        .filter((User.username == user.username) | (User.email == user.email))
        .first()
    )

    if existing_user:
        if existing_user.username == user.username:
            raise UserException("Already existing username")
        else:
            raise UserException("Already existing email")

    user_data = user.dict(exclude={"password"})
    user_data["password_hash"] = get_password_hash(user.password)

    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/", response_model=list[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    username: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    db: Session = Depends(_get_db),
):
    # TODO: Aggiungere paginazione
    """
    Get users with optional filters
    """
    query = db.query(User)

    if username:
        query = query.filter(User.username.contains(username))
    if email:
        query = query.filter(User.email.contains(email))

    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserWithTasks)
def get_user(user_id: int, db: Session = Depends(_get_db)):
    """
    Get user by id
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserException(f"User ID {user_id} not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(_get_db)):
    """
    Update user
    """
    user = get_user(user_id, db)

    update_data = user_update.dict(exclude_unset=True)

    if "username" in update_data:
        existing = (
            db.query(User)
            .filter(User.username == update_data["username"], User.id != user_id)
            .first()
        )
        if existing:
            raise UserException("Username already used")

    if "email" in update_data:
        existing = (
            db.query(User)
            .filter(User.email == update_data["email"], User.id != user_id)
            .first()
        )
        if existing:
            raise UserException("Email already used")

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(_get_db)):
    """
    Delete user
    """
    user = get_user(user_id, db)
    db.delete(user)
    db.commit()
    return


@router.get("/{user_id}/tasks", response_model=List[TaskResponse])
def get_user_tasks(
    user_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(_get_db),
):
    """
    Get all tasks from a user id
    """
    user = get_user(user_id, db)
    tasks = user.tasks
    if status:
        try:
            status_enum = TaskStatus(status)
            tasks = [t for t in tasks if t.status == status_enum]
        except ValueError:
            raise UserException(f"Status '{status}' not valid")
    return tasks


@router.post("/{user_id}/tasks/{task_id}", status_code=status.HTTP_201_CREATED)
def assign_task_to_user(user_id: int, task_id: int, db: Session = Depends(_get_db)):
    """
    Assing task to user ID
    """
    user = get_user(user_id, db)

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise UserException(f"Task ID {task_id} not found")
    if task in user.tasks:
        raise UserException("Task already assigned to the user")
    user.tasks.append(task)
    db.commit()

    return {"message": f"Task {task_id} assigned to {user_id}"}


@router.delete("/{user_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task_from_user(user_id: int, task_id: int, db: Session = Depends(_get_db)):
    """
    Remove task from a user
    """
    user = get_user(user_id, db)

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise UserException(f"Task ID {task_id} not found")
    if task not in user.tasks:
        raise UserException("Task not assigned to this user")

    user.tasks.remove(task)
    db.commit()

    return None
