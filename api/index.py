"""Vercel giriş noktası: src/ altındaki uygulamayı sunucusuz fonksiyon olarak açar."""

import os
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

# Vercel'de proje klasörü salt okunurdur; logger.setup_logging() çalışma klasöründe
# logs/ oluşturduğu için çalışma klasörü yazılabilir geçici klasöre alınır.
# İçerik, şablon ve statik dosya yolları __file__ üzerinden mutlak olduğu için etkilenmez.
os.chdir(tempfile.gettempdir())

from main import build_default_app  # noqa: E402

app = build_default_app()
