import logging
from typing import Any, Final

import httpx
import httpx2
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from content_types import Content, Level
from scoring import ScoreResult

logger = logging.getLogger(__name__)

# Düşünen Flash modelleri 30 sn sınırını aşabildiği için süre geniş tutulur.
TIMEOUT_MS: Final[int] = 90_000
LEVEL_NAMES: Final[dict[Level, str]] = {"yuksek": "yüksek", "orta": "orta", "dusuk": "düşük"}

INSTRUCTIONS: Final[str] = """Sen müzakere ve çatışma yönetimi konusunda bilgili, dikkatli bir eğitmensin.
Aşağıda bir kişinin Thomas-Kilmann tipi çatışma tarzı testindeki puanları ve bir kaynak listesi var.

Kurallar:
- Yalnızca aşağıdaki kaynak listesindeki bilgilere dayan. Listede olmayan bir bilgiyi kaynaklıymış gibi sunma.
- Her tespitin sonuna dayandığı kaynağın kimliğini köşeli parantez içinde yaz, örneğin [thomas-1977].
- Kaynaklarda olmayan sayısal iddia ya da alıntı yazma.
- Kişilik tanısı koyma; "siz şusunuz" yerine "bu profil çoğunlukla şunu tercih eder" gibi ifadeler kullan.
- Test, çatışma anındaki davranış tercihini gösterir; psikolojik değerlendirme yerine geçmez.
- Türkçe, 250-400 kelime yaz. Puanların birlikte ne anlattığını, güçlü yanları, dikkat edilecek noktaları ve somut gelişim önerilerini anlat.
- Son satıra "Kullanılan kaynaklar:" başlığıyla kullandığın kaynak kimliklerini listele."""


class LiveCommentUnavailable(Exception):
    """Canlı yapay zekâ yorumu şu anda üretilemiyor."""


def build_prompt(score: ScoreResult, content: Content) -> str:
    """Puanlardan ve kaynak paketinden Gemini'ye gönderilecek metni üretir (kişisel bilgi içermez)."""
    names = {style.key: style.name for style in content.styles}
    score_lines = [
        f"- {names[result.style]}: {result.score} ({LEVEL_NAMES[result.level]})" for result in score.results
    ]
    source_lines = [f"[{source.id}] {source.kaynakca}\n{source.ozet}" for source in content.sources]
    return "\n".join(
        [
            INSTRUCTIONS,
            "",
            "Puanlar (toplam 30):",
            *score_lines,
            f"Baskın tarz: {names[score.dominant]}",
            f"En az kullanılan tarz: {names[score.least]}",
            "",
            "Kaynak listesi:",
            "\n\n".join(source_lines),
        ]
    )


class GeminiStep:
    """Google Gemini'den canlı yorum ister."""

    def __init__(self, api_key: str, model: str, client: Any | None = None) -> None:
        self._model = model
        self._client = client or genai.Client(
            api_key=api_key, http_options=genai_types.HttpOptions(timeout=TIMEOUT_MS)
        )

    @property
    def model(self) -> str:
        return self._model

    def generate(self, prompt: str) -> str:
        try:
            response = self._client.models.generate_content(model=self._model, contents=prompt)
        except (genai_errors.APIError, httpx.HTTPError, httpx2.HTTPError, OSError) as exc:
            logger.warning("Gemini isteği başarısız: %s", exc.__class__.__name__)
            raise LiveCommentUnavailable("Canlı yorum üretilemedi") from exc
        text = (response.text or "").strip()
        if not text:
            logger.warning("Gemini boş cevap döndürdü")
            raise LiveCommentUnavailable("Canlı yorum boş geldi")
        return text
