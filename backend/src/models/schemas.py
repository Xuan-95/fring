from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class UserModel(BaseModel):
    id: int | None = None
    username: str
    email: EmailStr
    password: str | None = None


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


class UserResponse(UserModel):
    created_at: datetime


class UserWithTasks(UserResponse):
    tasks: list["TaskResponse"]


class TaskModel(BaseModel):
    id: int | None = None
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    assigned_to: list[UserModel] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None


class TaskResponse(TaskModel):
    id: int
    created_at: datetime
    assigned_to: list[UserResponse]


class TaskWithUsers(TaskResponse):
    assigned_to: list[UserResponse]


class TaskAssignment(BaseModel):
    user_id: int
    task_id: int


class BulkTaskAssignment(BaseModel):
    user_ids: list[int]
    task_id: int


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


UserWithTasks.model_rebuild()
TaskWithUsers.model_rebuild()
