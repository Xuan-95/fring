from contextlib import asynccontextmanager

from src.db.connection import engine
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from src.models.orm.todo import Base
from src.routers import auth, tasks, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    yield
    # Shutdown
    print("Application shutdown")


app = FastAPI(
    title="Task Management API",
    description="TODO List",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["root"])
def read_root():
    return {
        "message": "Task Management API",
        "version": "1.0.0",
        "endpoints": {"users": "/api/v1/users", "tasks": "/api/v1/tasks", "docs": "/docs", "redoc": "/redoc"},
    }


# Health check endpoint
@app.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy", "service": "Task Management API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
