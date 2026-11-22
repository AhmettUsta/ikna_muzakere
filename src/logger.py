"""
Logging configuration and setup utilities
"""

import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Final

from config import PROJECT_ROOT, config

LOG_DIR: Final = PROJECT_ROOT / "logs"


def setup_logging() -> None:
    """
    Set up console logging and, if enabled, a daily rotating log file
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.LOG_LEVEL)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console formatter
    log_format = "%(asctime)s - %(levelname)s [PID %(process)d - TID %(thread)d]: %(filename)s:%(lineno)d - %(message)s"
    log_formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config.LOG_LEVEL)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Silence verbose Azure SDK HTTP request/response logs.
    for azure_logger_name in [
        "azure",
        "azure.core",
        "azure.storage",
        "azure.core.pipeline.policies.http_logging_policy",
        "httpx",
        "openai",
        "openai._base_client",
    ]:
        logging.getLogger(azure_logger_name).setLevel(logging.WARNING)

    # Single log file, rotated daily at midnight
    if config.LOG_TO_FILE:
        # Path is anchored to the project root so the working directory does not matter
        LOG_DIR.mkdir(exist_ok=True)

        # File handler
        unified_handler = TimedRotatingFileHandler(
            filename=LOG_DIR / "log.log",
            when="midnight",
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding="utf-8",
        )

        unified_handler.setFormatter(log_formatter)
        unified_handler.suffix = "%Y-%m-%d"
        root_logger.addHandler(unified_handler)
