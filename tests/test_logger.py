import json
import logging
from collections.abc import Iterator
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pytest

SECRETS = {
    "LOG_LEVEL": "INFO", "PG_USER": "u", "PG_PASSWORD": "p", "PG_HOST": "127.0.0.1",
    "PG_DATABASE": "db", "PG_SCHEMA": "ikna_muzakere", "SESSION_SECRET": "s",
    "ADMIN_USERNAME": "a", "ADMIN_PASSWORD": "x",
}


@pytest.fixture
def logger_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator:
    monkeypatch.setenv("ikna_muzakere_secrets", json.dumps(SECRETS))
    import logger

    monkeypatch.setattr(logger, "LOG_DIR", tmp_path / "logs")
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    yield logger
    for handler in root.handlers:
        if handler not in saved_handlers:
            handler.close()
    root.handlers[:] = saved_handlers
    root.setLevel(saved_level)


def test_setup_logging_without_file_creates_no_log_dir(logger_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(logger_module.config, "LOG_TO_FILE", False)

    logger_module.setup_logging()

    assert not logger_module.LOG_DIR.exists()
    assert not any(isinstance(h, TimedRotatingFileHandler) for h in logging.getLogger().handlers)


def test_setup_logging_with_file_writes_under_log_dir(logger_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(logger_module.config, "LOG_TO_FILE", True)

    logger_module.setup_logging()

    file_handlers = [h for h in logging.getLogger().handlers if isinstance(h, TimedRotatingFileHandler)]
    assert len(file_handlers) == 1
    assert Path(file_handlers[0].baseFilename) == logger_module.LOG_DIR / "log.log"
