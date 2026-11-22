import os
from pathlib import Path
from typing import Final, Literal

from dotenv import load_dotenv
from pydantic import BaseModel

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent
SECRETS_ENV: Final = "ikna_muzakere_secrets"

load_dotenv(PROJECT_ROOT / ".env")


class Config(BaseModel):
    VERSION: str = "1.0.0"
    DEBUG_MODE: bool = False

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    LOG_TO_FILE: bool = False

    # Postgres
    PG_USER: str
    PG_PASSWORD: str
    PG_HOST: str
    PG_PORT: int = 5432
    PG_DATABASE: str
    PG_SCHEMA: str
    PG_SSLMODE: str = "require"

    # Web
    SESSION_SECRET: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    COOKIE_SECURE: bool = True

    # Gemini
    LIVE_COMMENT_ENABLED: bool = False
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str | None = None


config = Config.model_validate_json(os.environ[SECRETS_ENV])
