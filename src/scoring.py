from collections import Counter
from dataclasses import dataclass
from typing import Final

from content_types import STYLE_ORDER, Level, StyleDef, StyleKey

ANSWER_COUNT: Final[int] = 30
VALID_LETTERS: Final[frozenset[str]] = frozenset({"A", "B"})


@dataclass(frozen=True)
class StyleResult:
    style: StyleKey
    score: int
    level: Level
    relative: float


@dataclass(frozen=True)
class ScoreResult:
    results: list[StyleResult]
    dominant: StyleKey
    least: StyleKey

    def by_style(self, style: StyleKey) -> StyleResult:
        return next(result for result in self.results if result.style == style)


class Scorer:
    """Cevaplardan tarz puanlarını, seviyeleri ve baskın / en az kullanılan tarzı hesaplar."""

    def __init__(self, styles: list[StyleDef], answer_key: dict[int, dict[str, StyleKey]]) -> None:
        self._styles = {style.key: style for style in styles}
        self._answer_key = answer_key

    def count(self, answers: str) -> dict[StyleKey, int]:
        if len(answers) != ANSWER_COUNT:
            raise ValueError(f"{ANSWER_COUNT} cevap gerekli, {len(answers)} geldi")
        invalid = set(answers) - VALID_LETTERS
        if invalid:
            raise ValueError(f"Cevaplar yalnızca A veya B olabilir: {sorted(invalid)}")
        counter = Counter(self._answer_key[index + 1][letter] for index, letter in enumerate(answers))
        return {style: counter.get(style, 0) for style in STYLE_ORDER}

    def from_scores(self, scores: dict[StyleKey, int]) -> ScoreResult:
        results = [self._style_result(style, scores[style]) for style in STYLE_ORDER]
        # max/min ilk eşleşeni döndürür; liste STYLE_ORDER sırasında olduğu için
        # eşitlikte sabit sıra kuralı kendiliğinden uygulanır.
        dominant = max(results, key=lambda result: result.relative)
        least = min(
            (result for result in results if result.style != dominant.style),
            key=lambda result: result.relative,
        )
        return ScoreResult(results=results, dominant=dominant.style, least=least.style)

    def score(self, answers: str) -> ScoreResult:
        return self.from_scores(self.count(answers))

    def _style_result(self, style: StyleKey, score: int) -> StyleResult:
        definition = self._styles[style]
        if score >= definition.high:
            level: Level = "yuksek"
        elif score <= definition.low:
            level = "dusuk"
        else:
            level = "orta"
        # Eşikler tarzlar arasında farklı olduğu için ham puan yerine
        # eşik aralığına göre normalize edilmiş puan karşılaştırılır.
        relative = (score - definition.low) / (definition.high - definition.low)
        return StyleResult(style=style, score=score, level=level, relative=relative)
