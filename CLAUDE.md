# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fring is a full-stack task management application with a Python FastAPI backend and React frontend.

## Commands

### Backend (from `/backend` directory)

```bash
# Install dependencies (uses uv package manager)
uv sync

# Run development server (starts on http://localhost:8000)
python main.py

# Run Hurl API tests
hurl --variable host=localhost --variable port=8000 src/test/hurls/*.hurl
```

### Frontend (from `/frontend` directory)

```bash
# Install dependencies
npm install

# Run development server (starts on http://localhost:5173)
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

## Architecture

### Backend

- **Framework**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL (connection string in `DATABASE_URL` env var)
- **Python Version**: 3.13

**Structure**:
- `main.py` - Application entry point, registers routers and creates tables on startup
- `src/config/settings.py` - Pydantic BaseSettings for environment configuration
- `src/db/connection.py` - SQLAlchemy engine and session factory
- `src/models/orm/todo.py` - ORM models (User, Task with many-to-many relationship via `user_tasks` join table)
- `src/models/schemas.py` - Pydantic request/response DTOs
- `src/routers/` - API endpoint handlers (users.py, tasks.py)

**API**: All endpoints under `/api/v1`, auto-generated docs at `/docs`

### Frontend

- **Framework**: React 19 with Vite
- **Status**: Scaffolded but not yet integrated with backend API
- `src/components/` - React components (header, footer)

## Database Schema

Two main entities with many-to-many relationship:
- **User**: id, username (unique), email (unique), created_at
- **Task**: id, title, description, status (todo/in_progress/completed/canceled), created_at
- **user_tasks**: Join table for user-task assignments (CASCADE delete)
