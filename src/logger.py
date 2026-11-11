"""
Logging configuration and setup utilities
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from config import config


def setup_logging():
    """
    Set up comprehensive logging with both time and size rotation
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    log_level = config.LOG_LEVEL
    root_logger.setLevel(getattr(logging, log_level))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console formatter
    log_format = "%(asctime)s - %(levelname)s [PID %(process)d - TID %(thread)d]: %(filename)s:%(lineno)d - %(message)s"
    log_formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
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

    # Single unified log file with both time and size rotation
    if config.LOG_TO_FILE:
        # File handler
        unified_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "log.log"),
            when="midnight",
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding="utf-8",
        )

        unified_handler.setFormatter(log_formatter)
        unified_handler.suffix = "%Y-%m-%d"
        root_logger.addHandler(unified_handler)

