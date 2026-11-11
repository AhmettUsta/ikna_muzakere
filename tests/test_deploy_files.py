from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_dockerfile_creates_logs_dir_owned_by_app() -> None:
    lines = (ROOT / "Dockerfile").read_text(encoding="utf-8").splitlines()
    user_line = next(i for i, line in enumerate(lines) if line.startswith("USER app"))
    setup = "\n".join(lines[:user_line])

    # logger.setup_logging() açılışta logs/ oluşturur; non-root kullanıcı yazabilmeli.
    assert "mkdir -p /app/logs" in setup
    assert "chown app:app /app/logs" in setup


def test_requirements_pin_directly_imported_httpx2() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

    assert any(line.startswith("httpx2==") for line in requirements)
