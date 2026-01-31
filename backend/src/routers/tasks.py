from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.db.connection import _get_db
from src.models.exceptions import AlreadyExistingIDException, TaskNotFoundException
from src.models.orm.todo import Task, User
from src.models.schemas import (
    TaskModel,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
    TaskWithUsers,
    UserResponse,
)
from src.routers.users import get_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskModel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    """
    Create new task and auto-assign to current user
    """

    # Check if the ID already exists
    if task.id:
        existing_id = db.query(Task).filter(Task.id == task.id).first()
        if existing_id:
            raise AlreadyExistingIDException(id=existing_id)

    db_task = Task(**task.dict(exclude={"assigned_to"}))
    db_task.assigned_users.append(current_user)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/", response_model=list[TaskResponse])
def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    status: Optional[TaskStatus] = Query(None),
    title: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    """
    Get all tasks assigned to the current user with optional filters
    """
    query = db.query(Task).join(Task.assigned_users).filter(User.id == current_user.id)

    if status:
        query = query.filter(Task.status == status)
    if title:
        query = query.filter(Task.title.contains(title))

    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskWithUsers)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    """
    Get task by ID (only if assigned to current user)
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise TaskNotFoundException()

    if current_user not in task.assigned_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task",
        )

    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    """
    Update task (only if assigned to current user)
    """
    task = get_task(task_id, current_user, db)

    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    """
    Delete task (only if assigned to current user)
    """
    task = get_task(task_id, current_user, db)
    db.delete(task)
    db.commit()
    return None


@router.get("/{task_id}/users", response_model=list[UserResponse])
def get_task_users(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    """
    Get all users that are assigned to a task
    """
    task = get_task(task_id, current_user, db)
    return task.assigned_users


@router.post("/{task_id}/users/{user_id}", status_code=status.HTTP_201_CREATED)
def assign_user_to_task(
    task_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    """
    Assign a user to a task (only if current user has access to task)
    """
    task = get_task(task_id, current_user, db)
    user = get_user(user_id, db)

    if user in task.assigned_users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already assigned to this task")

    task.assigned_users.append(user)
    db.commit()

    return {"message": f"User {user_id} assigned succesfully to task {task_id}"}


@router.delete("/{task_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user_from_task(
    task_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    """
    Remove a task from a user (only if current user has access to task)
    """
    task = get_task(task_id, current_user, db)
    user = get_user(user_id, db)

    if user not in task.assigned_users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not assigned to this task")

    task.assigned_users.remove(user)
    db.commit()

    return None


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    status: TaskStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    """
    Update the status of a task (only if assigned to current user)
    """
    task = get_task(task_id, current_user, db)
    task.status = status
    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return task
