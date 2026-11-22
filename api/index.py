"""Vercel giriş noktası: src/ altındaki uygulamayı sunucusuz fonksiyon olarak açar."""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

# Vercel'de proje klasörü salt okunurdur. Logger yalnızca LOG_TO_FILE açıkken logs/ oluşturur;
# bu yüzden Vercel ortamında LOG_TO_FILE kapalı kalmalıdır.
from main import build_default_app  # noqa: E402

app = build_default_app()
