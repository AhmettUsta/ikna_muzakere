import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Config(BaseModel):
    VERSION: str = "1.0.0"
    DEBUG_MODE: Optional[bool] = False

    # Logging
    LOG_LEVEL: str
    LOG_TO_FILE: Optional[bool] = False

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
    COOKIE_SECURE: Optional[bool] = True

    # Gemini
    LIVE_COMMENT_ENABLED: Optional[bool] = False
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: Optional[str] = None

config = Config.model_validate_json(os.environ["ikna_muzakere_secrets"])
