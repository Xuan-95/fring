import os
from pathlib import Path
from typing import Annotated

from dotenv import dotenv_values, load_dotenv
from pydantic import AfterValidator
from pydantic_settings import BaseSettings

base_path = Path(__file__).parent.parent.parent
load_dotenv(base_path / ".env", override=True)
load_dotenv(base_path / ".env.development", override=True)


def required(value):
    if not value:
        raise ValueError("Missing field")
    return value


class DatabaseSettings(BaseSettings):
    DATABASE_URL: Annotated[str, AfterValidator(required)] = ""


class AuthSettings(BaseSettings):
    JWT_SECRET_KEY: Annotated[str, AfterValidator(required)] = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


db_settings = DatabaseSettings()
auth_settings = AuthSettings()
