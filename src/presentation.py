from dataclasses import dataclass
from typing import Final

from content_types import Level, Section, StyleKey
from scoring import StyleResult

LOW_NOTE: Final[str] = "Bu tarzı az kullanıyorsunuz. Şu durumlarda işe yarayabilir:"


@dataclass(frozen=True)
class SunumView:
    style: StyleKey
    level: Level
    acik: bool
    not_metni: str | None
    bolumler: list[Section]


def sunum_view(result: StyleResult, sections: list[Section]) -> SunumView:
    """Tarzın seviyesine göre sunum bölümlerinden hangilerinin, hangi sırayla gösterileceğini seçer."""
    if result.level == "yuksek":
        first = [section for section in sections if section.tur == "siz_iseniz"]
        rest = [section for section in sections if section.tur != "siz_iseniz"]
        return SunumView(result.style, result.level, True, None, first + rest)
    if result.level == "dusuk":
        uygun = [section for section in sections if section.tur == "uygun"]
        return SunumView(result.style, result.level, True, LOW_NOTE, uygun)
    return SunumView(result.style, result.level, False, None, list(sections))
