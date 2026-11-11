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


def test_vercel_entry_builds_app_without_writing_to_project(tmp_path) -> None:
    import json
    import os
    import subprocess
    import sys

    secrets = {
        "LOG_LEVEL": "INFO", "PG_USER": "u", "PG_PASSWORD": "p", "PG_HOST": "127.0.0.1",
        "PG_DATABASE": "db", "PG_SCHEMA": "ikna_muzakere", "SESSION_SECRET": "s",
        "ADMIN_USERNAME": "ustaoglu", "ADMIN_PASSWORD": "x",
    }
    env = {**os.environ, "ikna_muzakere_secrets": json.dumps(secrets)}
    code = (
        "import sys, os; sys.path.insert(0, 'api'); import index; "
        "print(type(index.app).__name__, os.getcwd() != sys.argv[1], os.path.isdir('logs'))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(ROOT)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60
    )

    assert result.returncode == 0, result.stderr
    # Vercel'de proje klasörü salt okunur: log klasörü proje dışında oluşturulmalı.
    assert result.stdout.split() == ["FastAPI", "True", "True"]


def test_vercel_routes_everything_to_entry_before_filesystem() -> None:
    import json

    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))

    # "routes" dosya sisteminden önce işlenir; böylece içerik JSON'ları ve repo dosyaları
    # statik olarak sunulmaz, her istek uygulamaya gider.
    assert "rewrites" not in config
    assert config["routes"] == [{"src": "/(.*)", "dest": "/api/index"}]
