# Fring Backend - Technical Specifications

## Table of Contents
- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Code Organization](#code-organization)
- [Best Practices & Patterns](#best-practices--patterns)

---

## Overview

Fring backend is a RESTful API service for task management built with FastAPI and PostgreSQL. It provides user management, task management, and assignment capabilities through a clean, async-first architecture.

**Key Features:**
- User CRUD operations with unique username/email validation
- Task management with status tracking
- Many-to-many user-task assignments
- Query filtering and pagination
- Auto-generated API documentation (OpenAPI/Swagger)
- Integration testing with Hurl

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | ≥0.116.1 | Modern, async web framework with automatic API docs |
| **ORM** | SQLAlchemy | ≥2.0.43 | Database abstraction with declarative models |
| **Database** | PostgreSQL | Latest | Production-grade relational database |
| **DB Driver** | psycopg2 | ≥2.9.10 | PostgreSQL adapter for Python |
| **Validation** | Pydantic | ≥2.0 | Data validation and settings management |
| **Settings** | pydantic-settings | ≥2.12.0 | Environment-based configuration |
| **Server** | Uvicorn | ≥0.35.0 | ASGI server with hot reload support |
| **Package Manager** | uv | Latest | Fast Python package and project manager |
| **Testing** | Hurl | Latest | HTTP integration testing |
| **Python Version** | 3.13 | - | Latest stable Python |

---

## Architecture

### Layered Architecture Pattern

```
┌─────────────────────────────────────────────────┐
│                 Client Layer                     │
│        (Frontend, Mobile, API Consumers)         │
└────────────────────┬────────────────────────────┘
                     │ HTTP/JSON
┌────────────────────▼────────────────────────────┐
│              API Layer (Routers)                 │
│  - Request validation (Pydantic schemas)         │
│  - Business logic & error handling               │
│  - Response serialization                        │
└────────────────────┬────────────────────────────┘
                     │ Dependency Injection
┌────────────────────▼────────────────────────────┐
│           Database Session Layer                 │
│  - Connection pooling (SQLAlchemy engine)        │
│  - Transaction management                        │
│  - Session lifecycle (context manager)           │
└────────────────────┬────────────────────────────┘
                     │ SQL Queries
┌────────────────────▼────────────────────────────┐
│              ORM Layer (Models)                  │
│  - Entity definitions (User, Task)               │
│  - Relationships (many-to-many)                  │
│  - Column constraints & defaults                 │
└────────────────────┬────────────────────────────┘
                     │ DDL/DML
┌────────────────────▼────────────────────────────┐
│         PostgreSQL Database Layer                │
│  - Data persistence                              │
│  - Referential integrity (CASCADE)               │
│  - Indexing (username, email unique indexes)     │
└──────────────────────────────────────────────────┘
```

### Application Lifecycle

**Startup Sequence:**
1. Load environment variables from `.env` and `.env.development`
2. Validate `DATABASE_URL` configuration (Pydantic)
3. Create SQLAlchemy engine with connection pool
4. Initialize database tables from ORM metadata
5. Register API routers with `/api/v1` prefix
6. Configure CORS middleware (permissive for development)
7. Start Uvicorn server on `0.0.0.0:8000`

**Request Lifecycle:**
1. Client sends HTTP request → Uvicorn receives
2. FastAPI routes to appropriate endpoint handler
3. Pydantic validates request body/query params
4. Dependency injection provides database session
5. Business logic executes (queries, mutations)
6. SQLAlchemy commits transaction
7. Pydantic serializes response to JSON
8. FastAPI returns HTTP response with proper status code

---

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────────────┐            ┌─────────────────────┐
│       User          │            │       Task          │
├─────────────────────┤            ├─────────────────────┤
│ id (PK)             │            │ id (PK)             │
│ username (UNIQUE)   │            │ title               │
│ email (UNIQUE)      │            │ description         │
│ created_at          │            │ status              │
└──────────┬──────────┘            │ created_at          │
           │                       │ updated_at          │
           │                       └──────────┬──────────┘
           │                                  │
           │         ┌──────────────┐         │
           └────────▶│  user_tasks  │◀────────┘
                     ├──────────────┤
                     │ user_id (FK) │
                     │ task_id (FK) │
                     └──────────────┘
                     (Composite PK)
                     CASCADE DELETE
```

### Table Definitions

#### `users` Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL UNIQUE,
    email VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key, Auto-increment | Unique user identifier |
| `username` | String | NOT NULL, UNIQUE | User's display name |
| `email` | String | NOT NULL, UNIQUE | User's email address |
| `created_at` | DateTime | NOT NULL, Default: UTC now | Account creation timestamp |

**Indexes:**
- Primary key index on `id`
- Unique index on `username`
- Unique index on `email`

#### `tasks` Table
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    description VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'todo',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key, Auto-increment | Unique task identifier |
| `title` | String | NOT NULL | Task title/summary |
| `description` | String | Nullable | Detailed task description |
| `status` | Enum | NOT NULL, Default: 'todo' | Task status (see below) |
| `created_at` | DateTime | NOT NULL, Default: UTC now | Task creation timestamp |
| `updated_at` | DateTime | NOT NULL, Auto-update on change | Last modification timestamp |

**Status Values (Enum):**
- `todo` - Task not started
- `in_progress` - Task currently being worked on
- `completed` - Task finished successfully
- `canceled` - Task abandoned/cancelled

#### `user_tasks` Join Table (Association Table)
```sql
CREATE TABLE user_tasks (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, task_id)
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | Integer | FK to users.id, CASCADE DELETE | User being assigned |
| `task_id` | Integer | FK to tasks.id, CASCADE DELETE | Task being assigned |

**Cascade Behavior:**
- Deleting a user removes all their task assignments (not the tasks themselves)
- Deleting a task removes all user assignments to that task
- Allows tasks to exist without assignees (unassigned tasks)
- Allows users to exist without tasks (onboarding state)

**Indexes:**
- Composite primary key index on `(user_id, task_id)`
- Foreign key index on `user_id`
- Foreign key index on `task_id`

---

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

### Health & Metadata

#### `GET /health`
Health check endpoint for monitoring/load balancers.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-01-31T10:30:00Z"
}
```

#### `GET /`
API root with metadata and available endpoints.

**Response:** `200 OK`
```json
{
  "name": "Fring API",
  "version": "1.0.0",
  "endpoints": {
    "users": "/api/v1/users",
    "tasks": "/api/v1/tasks"
  }
}
```

---

### User Management

#### `POST /api/v1/users/`
Create a new user.

**Request Body:**
```json
{
  "id": 1,  // Optional: if omitted, auto-generated
  "username": "johndoe",
  "email": "john@example.com"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "created_at": "2025-01-31T10:30:00Z"
}
```

**Validation:**
- Username must be unique (case-sensitive)
- Email must be unique (case-sensitive)
- Both fields are required

**Errors:**
- `400 Bad Request` - "Already existing username"
- `400 Bad Request` - "Already existing email"

---

#### `GET /api/v1/users/`
List users with optional filtering and pagination.

**Query Parameters:**
- `skip` (int, default: 0) - Offset for pagination
- `limit` (int, default: 100, max: 1000) - Number of results
- `username` (string, optional) - Filter by username (partial match)
- `email` (string, optional) - Filter by email (partial match)

**Example:** `GET /api/v1/users/?username=john&limit=10`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2025-01-31T10:30:00Z"
  }
]
```

---

#### `GET /api/v1/users/{user_id}`
Get user details with assigned tasks.

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "created_at": "2025-01-31T10:30:00Z",
  "tasks": [
    {
      "id": 1,
      "title": "Complete API docs",
      "description": "Write comprehensive documentation",
      "status": "in_progress",
      "created_at": "2025-01-31T09:00:00Z",
      "updated_at": "2025-01-31T10:15:00Z"
    }
  ]
}
```

**Errors:**
- `400 Bad Request` - User not found

---

#### `PUT /api/v1/users/{user_id}`
Update user information (partial update supported).

**Request Body:**
```json
{
  "username": "johndoe_updated",
  "email": "newemail@example.com"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "johndoe_updated",
  "email": "newemail@example.com",
  "created_at": "2025-01-31T10:30:00Z"
}
```

**Validation:**
- New username must be unique (excludes current user)
- New email must be unique (excludes current user)
- Fields not provided are not updated

**Errors:**
- `400 Bad Request` - "Username already used"
- `400 Bad Request` - "Email already used"
- `400 Bad Request` - User not found

---

#### `DELETE /api/v1/users/{user_id}`
Delete a user and remove all their task assignments.

**Response:** `204 No Content`

**Side Effects:**
- Removes all entries from `user_tasks` where `user_id` matches
- Does NOT delete the tasks themselves
- Cascade handled by database foreign key constraint

**Errors:**
- `400 Bad Request` - User not found

---

### User Task Assignments

#### `GET /api/v1/users/{user_id}/tasks`
Get all tasks assigned to a user.

**Query Parameters:**
- `status` (string, optional) - Filter by task status

**Example:** `GET /api/v1/users/1/tasks?status=in_progress`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Complete API docs",
    "description": "Write comprehensive documentation",
    "status": "in_progress",
    "created_at": "2025-01-31T09:00:00Z",
    "updated_at": "2025-01-31T10:15:00Z"
  }
]
```

**Errors:**
- `400 Bad Request` - "Status '{status}' not valid"

---

#### `POST /api/v1/users/{user_id}/tasks/{task_id}`
Assign a task to a user.

**Response:** `201 Created`
```json
{
  "message": "Task 1 assigned to 1"
}
```

**Validation:**
- User must exist
- Task must exist
- Task cannot already be assigned to user (duplicate prevention)

**Errors:**
- `400 Bad Request` - "User ID {user_id} not found"
- `400 Bad Request` - "Task ID {task_id} not found"
- `400 Bad Request` - "Task already assigned to the user"

---

#### `DELETE /api/v1/users/{user_id}/tasks/{task_id}`
Remove a task assignment from a user.

**Response:** `204 No Content`

**Validation:**
- User must exist
- Task must exist
- Task must be currently assigned to user

**Errors:**
- `400 Bad Request` - "User ID {user_id} not found"
- `400 Bad Request` - "Task ID {task_id} not found"
- `400 Bad Request` - "Task not assigned to this user"

---

### Task Management

#### `POST /api/v1/tasks/`
Create a new task.

**Request Body:**
```json
{
  "id": 1,  // Optional: if omitted, auto-generated
  "title": "Complete API documentation",
  "description": "Write comprehensive technical specs",
  "status": "todo"  // Optional: defaults to "todo"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "Complete API documentation",
  "description": "Write comprehensive technical specs",
  "status": "todo",
  "created_at": "2025-01-31T10:30:00Z",
  "updated_at": "2025-01-31T10:30:00Z"
}
```

**Validation:**
- Title is required
- ID must be unique (if provided)
- Status must be valid enum value

**Errors:**
- `400 Bad Request` - Duplicate task ID

---

#### `GET /api/v1/tasks/`
List tasks with filtering and pagination.

**Query Parameters:**
- `skip` (int, default: 0) - Offset for pagination
- `limit` (int, default: 100) - Number of results
- `status` (TaskStatus, optional) - Filter by status
- `title` (string, optional) - Filter by title (partial match)
- `assigned` (boolean, optional) - Filter by assignment status
  - `true` - Only tasks with at least one assigned user
  - `false` - Only unassigned tasks

**Example:** `GET /api/v1/tasks/?status=in_progress&assigned=true&limit=20`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Complete API docs",
    "description": "Write comprehensive documentation",
    "status": "in_progress",
    "created_at": "2025-01-31T09:00:00Z",
    "updated_at": "2025-01-31T10:15:00Z"
  }
]
```

---

#### `GET /api/v1/tasks/{task_id}`
Get task details with assigned users.

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Complete API docs",
  "description": "Write comprehensive documentation",
  "status": "in_progress",
  "created_at": "2025-01-31T09:00:00Z",
  "updated_at": "2025-01-31T10:15:00Z",
  "assigned_users": [
    {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "created_at": "2025-01-31T10:30:00Z"
    }
  ]
}
```

**Errors:**
- `400 Bad Request` - Task not found

---

#### `PUT /api/v1/tasks/{task_id}`
Update task information (partial update supported).

**Request Body:**
```json
{
  "title": "Updated title",
  "status": "completed"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Updated title",
  "description": "Write comprehensive documentation",
  "status": "completed",
  "created_at": "2025-01-31T09:00:00Z",
  "updated_at": "2025-01-31T11:00:00Z"
}
```

**Note:** `updated_at` is automatically set to current timestamp.

**Errors:**
- `400 Bad Request` - Task not found

---

#### `PATCH /api/v1/tasks/{task_id}/status`
Update only the task status (convenience endpoint).

**Query Parameters:**
- `status` (TaskStatus, required) - New status value

**Example:** `PATCH /api/v1/tasks/1/status?status=completed`

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Complete API docs",
  "description": "Write comprehensive documentation",
  "status": "completed",
  "created_at": "2025-01-31T09:00:00Z",
  "updated_at": "2025-01-31T11:00:00Z"
}
```

---

#### `DELETE /api/v1/tasks/{task_id}`
Delete a task and all its user assignments.

**Response:** `204 No Content`

**Side Effects:**
- Removes all entries from `user_tasks` where `task_id` matches
- Cascade handled by database foreign key constraint

**Errors:**
- `400 Bad Request` - Task not found

---

### Task User Assignments

#### `GET /api/v1/tasks/{task_id}/users`
Get all users assigned to a task.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2025-01-31T10:30:00Z"
  }
]
```

---

#### `POST /api/v1/tasks/{task_id}/users/{user_id}`
Assign a user to a task.

**Response:** `201 Created`
```json
{
  "message": "User 1 assigned successfully to task 1"
}
```

**Validation:**
- Task must exist
- User must exist
- User cannot already be assigned to task (duplicate prevention)

**Errors:**
- `400 Bad Request` - Task not found
- `400 Bad Request` - User not found
- `400 Bad Request` - "User already assigned to this task"

---

#### `DELETE /api/v1/tasks/{task_id}/users/{user_id}`
Remove a user assignment from a task.

**Response:** `204 No Content`

**Validation:**
- Task must exist
- User must exist
- User must be currently assigned to task

**Errors:**
- `400 Bad Request` - Task not found
- `400 Bad Request` - User not found
- `400 Bad Request` - "User already assigned to this task" *(Note: Error message is misleading, should say "not assigned")*

---

## Configuration

### Environment Variables

Configuration is managed via `.env` files using Pydantic Settings.

**Load Order:**
1. `.env` (shared/production settings)
2. `.env.development` (development overrides)

#### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `DATABASE_URL` | String | PostgreSQL connection string | `postgresql://user:pass@host/db` |

**Development Default:**
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost/life-manager
```

### Settings Class

**Location:** `src/config/settings.py`

```python
from pydantic_settings import BaseSettings

class PostgresSettings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**Features:**
- Type validation (raises error if DATABASE_URL missing)
- Automatic `.env` file loading
- Environment variable override support

---

## Development Setup

### Prerequisites
- Python 3.13+
- PostgreSQL database
- `uv` package manager

### Installation

1. **Clone repository**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```
   This creates a virtual environment and installs all dependencies from `pyproject.toml`.

3. **Configure environment**
   ```bash
   cp .env.development .env
   # Edit .env with your DATABASE_URL
   ```

4. **Initialize database**
   The application automatically creates tables on startup using:
   ```python
   Base.metadata.create_all(bind=engine)
   ```

5. **Run development server**
   ```bash
   python main.py
   ```
   Server starts on `http://localhost:8000` with hot reload enabled.

### Accessing Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## Testing

### Integration Tests (Hurl)

**Location:** `src/test/hurls/`

**Run all tests:**
```bash
hurl --variable host=localhost --variable port=8000 src/test/hurls/*.hurl
```

**Run specific test suite:**
```bash
hurl --variable host=localhost --variable port=8000 src/test/hurls/user.hurl
hurl --variable host=localhost --variable port=8000 src/test/hurls/task.hurl
```

#### Test Coverage

**`user.hurl`:**
- Health check validation
- User creation (success & duplicate prevention)
- Username uniqueness validation
- Email uniqueness validation
- User retrieval and query filtering

**`task.hurl`:**
- Health check validation
- Task creation (success & duplicate ID prevention)
- Task retrieval with status validation
- Task filtering and pagination

### Manual Testing with curl

**Create user:**
```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com"}'
```

**List users:**
```bash
curl http://localhost:8000/api/v1/users/
```

**Create task:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "description": "Test description", "status": "todo"}'
```

**Assign task to user:**
```bash
curl -X POST http://localhost:8000/api/v1/users/1/tasks/1
```

---

## Code Organization

```
backend/
├── main.py                          # Application entry point
│   ├── FastAPI app initialization
│   ├── Lifecycle management (@asynccontextmanager)
│   ├── Router registration
│   └── CORS middleware configuration
│
├── pyproject.toml                   # Project metadata & dependencies (uv)
├── uv.lock                          # Locked dependency versions
├── .python-version                  # Python 3.13 requirement
├── .env                            # Environment variables (gitignored)
├── .env.development                # Development defaults
│
└── src/
    ├── config/
    │   └── settings.py              # Pydantic settings management
    │
    ├── db/
    │   └── connection.py            # SQLAlchemy engine & session factory
    │       ├── create_engine()
    │       ├── SessionLocal (sessionmaker)
    │       └── _get_db() dependency
    │
    ├── models/
    │   ├── orm/
    │   │   └── todo.py              # SQLAlchemy ORM models
    │   │       ├── Base (DeclarativeBase)
    │   │       ├── User model
    │   │       ├── Task model
    │   │       └── user_tasks (association table)
    │   │
    │   ├── schemas.py               # Pydantic request/response DTOs
    │   │   ├── TaskStatus enum
    │   │   ├── UserModel, UserResponse, UserWithTasks, UserUpdate
    │   │   └── TaskModel, TaskResponse, TaskWithUsers, TaskUpdate
    │   │
    │   └── exceptions.py            # Custom HTTP exceptions
    │       ├── UserException (400)
    │       ├── TaskNotFoundException (400)
    │       └── AlreadyExistingIDException (400)
    │
    ├── routers/
    │   ├── users.py                 # User API endpoints
    │   │   ├── POST /users/
    │   │   ├── GET /users/
    │   │   ├── GET /users/{user_id}
    │   │   ├── PUT /users/{user_id}
    │   │   ├── DELETE /users/{user_id}
    │   │   ├── GET /users/{user_id}/tasks
    │   │   ├── POST /users/{user_id}/tasks/{task_id}
    │   │   └── DELETE /users/{user_id}/tasks/{task_id}
    │   │
    │   └── tasks.py                 # Task API endpoints
    │       ├── POST /tasks/
    │       ├── GET /tasks/
    │       ├── GET /tasks/{task_id}
    │       ├── PUT /tasks/{task_id}
    │       ├── DELETE /tasks/{task_id}
    │       ├── GET /tasks/{task_id}/users
    │       ├── POST /tasks/{task_id}/users/{user_id}
    │       ├── DELETE /tasks/{task_id}/users/{user_id}
    │       └── PATCH /tasks/{task_id}/status
    │
    ├── controllers/                 # [Empty - Future business logic layer]
    ├── utils/                       # [Empty - Future utility functions]
    │
    └── test/
        └── hurls/                   # HTTP integration tests
            ├── user.hurl            # User endpoint tests
            └── task.hurl            # Task endpoint tests
```

---

## Best Practices & Patterns

### 1. Dependency Injection for Database Sessions

FastAPI's `Depends()` manages database sessions automatically:

```python
def _get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db  # Provide session to endpoint
    finally:
        db.close()  # Always cleanup, even on errors

@router.get("/users/")
def get_users(db: Session = Depends(_get_db)):
    # db is automatically injected and cleaned up
    return db.query(User).all()
```

**Benefits:**
- No manual session management
- Guaranteed cleanup (prevents connection leaks)
- Easy to mock for testing
- Thread-safe per-request sessions

### 2. Pydantic Schema Separation (ORM vs DTO)

**ORM Models** (models/orm/todo.py): Database-specific
- Include SQLAlchemy relationships
- May have private/internal fields
- Use Mapped[T] type annotations

**DTOs** (models/schemas.py): API contract
- Only expose public fields
- Validation rules for input
- Response models for output
- Clean JSON serialization

```python
# ORM - Database representation
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    tasks: Mapped[list[Task]] = relationship(...)  # Internal relationship

# DTO - API representation
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    # No internal relationships exposed
```

### 3. Partial Updates with `exclude_unset=True`

Update endpoints support partial updates:

```python
@router.put("/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session):
    user = get_user(user_id, db)

    # Only update fields that were provided in request
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    return user
```

**Example:**
```bash
# Only update email, leave username unchanged
PATCH /users/1 {"email": "new@example.com"}
```

### 4. Automatic Timestamp Management

SQLAlchemy handles timestamps automatically:

```python
class Task(Base):
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow  # Auto-updates on any UPDATE
    )
```

No manual timestamp management needed in endpoints.

### 5. Association Table Pattern (Many-to-Many)

Simple many-to-many without extra data uses Table (not a Model):

```python
user_tasks = Table(
    "user_tasks",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE")),
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE")),
)
```

**When to use Table vs Model:**
- **Table**: Pure many-to-many (no extra fields)
- **Model**: Association object pattern (e.g., add `assigned_at`, `role`)

### 6. Query Filtering Pattern

Build dynamic queries with conditional filters:

```python
query = db.query(Task)

if status:
    query = query.filter(Task.status == status)
if title:
    query = query.filter(Task.title.contains(title))

tasks = query.offset(skip).limit(limit).all()
```

### 7. Cascade Delete Strategy

**Current behavior:**
- Delete user → Remove task assignments (keep tasks)
- Delete task → Remove user assignments (keep users)

**Rationale:**
- Tasks can exist independently (unassigned backlog)
- Users can exist without tasks (onboarding)
- Prevents accidental data loss

**Alternative strategies:**
```python
# To delete tasks when user deleted:
ForeignKey("users.id", ondelete="CASCADE")  # in tasks table

# To prevent deletion if tasks exist:
ForeignKey("users.id", ondelete="RESTRICT")
```

### 8. Error Handling with Custom Exceptions

Centralized error handling with custom exceptions:

```python
class UserException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

# Usage
if existing_user:
    raise UserException("Already existing username")
```

**Benefits:**
- Consistent error responses
- Easy to add logging/monitoring hooks
- Type-safe exception handling

### 9. API Versioning

Routes are prefixed with `/api/v1`:

```python
app.include_router(users.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
```

**Future migration:**
```python
# Add v2 endpoints without breaking v1
app.include_router(users_v1.router, prefix="/api/v1")
app.include_router(users_v2.router, prefix="/api/v2")
```

### 10. CORS Configuration

Development uses permissive CORS (update for production):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # Production: specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production recommendations:**
```python
allow_origins=[
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
```

---

## Future Enhancements

### Authentication & Authorization
- [ ] JWT token authentication
- [ ] Password hashing (bcrypt)
- [ ] User roles (admin, member, viewer)
- [ ] Task ownership permissions

### API Improvements
- [ ] Bulk operations (bulk assign, bulk status update)
- [ ] Task priority field
- [ ] Task due dates and reminders
- [ ] Task comments/activity log
- [ ] File attachments

### Data Layer
- [ ] Database migrations (Alembic)
- [ ] Soft deletes (keep audit trail)
- [ ] Full-text search (PostgreSQL FTS)
- [ ] Database connection pooling tuning

### Observability
- [ ] Structured logging (JSON logs)
- [ ] Request ID tracking
- [ ] Metrics (Prometheus)
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (APM)

### Testing
- [ ] Unit tests (pytest)
- [ ] Test database fixtures
- [ ] Coverage reporting
- [ ] CI/CD integration

### Development Experience
- [ ] Docker containerization
- [ ] Docker Compose for local stack
- [ ] Pre-commit hooks (black, ruff)
- [ ] API rate limiting

---

## Deployment Considerations

### Production Checklist

- [ ] **Environment Variables:** Secure secrets management (not `.env` files)
- [ ] **Database:** Connection pooling, read replicas for scaling
- [ ] **CORS:** Whitelist specific origins only
- [ ] **HTTPS:** TLS termination (reverse proxy or cloud load balancer)
- [ ] **Logging:** Structured JSON logs to stdout
- [ ] **Monitoring:** Health checks, metrics, alerting
- [ ] **Migrations:** Use Alembic for schema changes
- [ ] **Backups:** Automated PostgreSQL backups
- [ ] **Scaling:** Horizontal scaling with stateless API servers

### Recommended Stack

**Option 1: Cloud Platform (AWS/GCP/Azure)**
- **Compute:** Elastic Beanstalk / Cloud Run / App Service
- **Database:** RDS PostgreSQL / Cloud SQL / Azure Database
- **Load Balancer:** ALB / Cloud Load Balancing / Azure Load Balancer

**Option 2: Container Platform**
- **Orchestration:** Kubernetes / ECS / Cloud Run
- **Image:** Docker container with Uvicorn
- **Database:** Managed PostgreSQL service

**Option 3: Platform as a Service**
- **Platform:** Render / Railway / Fly.io
- **Database:** Managed PostgreSQL addon
- **Deployment:** Git push to deploy

---

## Troubleshooting

### Common Issues

**1. Database connection errors**
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution:** Check `DATABASE_URL` in `.env` and ensure PostgreSQL is running.

**2. Import errors**
```
ModuleNotFoundError: No module named 'src'
```
**Solution:** Run from `backend/` directory, not nested folders.

**3. Table not found errors**
```
sqlalchemy.exc.ProgrammingError: relation "users" does not exist
```
**Solution:** Tables are auto-created on startup. Restart server or check database permissions.

**4. Unique constraint violations**
```
sqlalchemy.exc.IntegrityError: duplicate key value violates unique constraint
```
**Solution:** Expected behavior for duplicate username/email. Check validation logic in endpoints.

---

## Contact & Support

For questions or issues with the Fring backend:
- **Documentation:** This file (`BACKEND_TECHNICAL_SPECS.md`)
- **API Docs:** http://localhost:8000/docs (when server running)
- **Source Code:** `/backend` directory

---

**Document Version:** 1.0.0
**Last Updated:** 2025-01-31
**Python Version:** 3.13
**FastAPI Version:** ≥0.116.1
