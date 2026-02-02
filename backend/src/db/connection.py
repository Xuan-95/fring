import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import db_settings

# SQLite requires check_same_thread=False for FastAPI's threading model
connect_args = {"check_same_thread": False} if db_settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    db_settings.DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
