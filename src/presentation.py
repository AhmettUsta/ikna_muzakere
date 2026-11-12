from dataclasses import dataclass, field
from typing import Final

from content_types import AiSectionType, Block, Level, Question, Section, SourcedText, StyleKey
from scoring import StyleResult

LOW_NOTE: Final[str] = "Bu tarzı az kullanıyorsunuz. Aşağıdaki uygun koşullarda bu tarza geçmeyi deneyin."
MID_NOTE: Final[str] = "Bu tarzı orta düzeyde kullanıyorsunuz. Uygun koşullarda bilinçli olarak tercih edin."


@dataclass(frozen=True)
class Advice:
    not_metni: str | None
    liste_basligi: str | None
    maddeler: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StyleCard:
    style: StyleKey
    level: Level
    acik: bool
    davranis: Section
    uygun: Section
    uygun_degil: Section
    tavsiye: Advice
    karsi_taraf: Section


def _first(sections: list[Section], tur: str) -> Section | None:
    return next((section for section in sections if section.tur == tur), None)


def _is_open(level: Level) -> bool:
    # Uç seviyeler (yüksek ve düşük) dikkat gerektirir; yalnızca orta seviye kapalı başlar.
    return level != "orta"


def _sunum_advice(level: Level, siz_iseniz: Section, level_advice: dict[Level, list[str]]) -> Advice:
    if level == "yuksek":
        return Advice(not_metni=None, liste_basligi=None, maddeler=list(siz_iseniz.maddeler))
    note = LOW_NOTE if level == "dusuk" else MID_NOTE
    return Advice(not_metni=note, liste_basligi=None, maddeler=list(level_advice[level]))


def style_card(result: StyleResult, sections: list[Section], level_advice: dict[Level, list[str]]) -> StyleCard:
    """Sunum sekmesindeki kartı kurar; tavsiye yüksekte sunumdan, düşük ve ortada seviye maddelerinden gelir."""
    return StyleCard(
        style=result.style,
        level=result.level,
        acik=_is_open(result.level),
        davranis=_first(sections, "davranis"),
        uygun=_first(sections, "uygun"),
        uygun_degil=_first(sections, "uygun_degil"),
        tavsiye=_sunum_advice(result.level, _first(sections, "siz_iseniz"), level_advice),
        karsi_taraf=_first(sections, "karsi_taraf"),
    )


@dataclass(frozen=True)
class AiCard:
    """AI destekli sekmedeki kart: bütün bölümler kaynaklı düz yazıdır."""

    style: StyleKey
    level: Level
    acik: bool
    davranis: str
    tavsiye: str
    uygun: str
    uygun_degil: str
    karsi_taraf: str


def ai_card(result: StyleResult, block: Block, sections: dict[AiSectionType, SourcedText]) -> AiCard:
    """Davranış ve tavsiye seviyeye özel bloktan, diğer bölümler tarza özel metinlerden gelir."""
    return AiCard(
        style=result.style,
        level=result.level,
        acik=_is_open(result.level),
        davranis=block.aciklama,
        tavsiye=block.gelisim,
        uygun=sections["uygun"].metin,
        uygun_degil=sections["uygun_degil"].metin,
        karsi_taraf=sections["karsi_taraf"].metin,
    )


@dataclass(frozen=True)
class AnswerRow:
    question: Question
    secilen: str
    secilen_tarz: StyleKey
    harfler: dict[StyleKey, str]


def answer_rows(questions: list[Question], answer_key: dict[int, dict[str, StyleKey]], answers: str) -> list[AnswerRow]:
    """Her soru için seçilen şıkkı ve cevap anahtarındaki tarz sütunlarını (tarz -> harf) verir."""
    if len(answers) != len(questions):
        raise ValueError(f"{len(questions)} cevap bekleniyordu, {len(answers)} geldi")
    rows = []
    for question, letter in zip(questions, answers):
        options = answer_key[question.no]
        rows.append(
            AnswerRow(
                question=question,
                secilen=letter,
                secilen_tarz=options[letter],
                harfler={style: option for option, style in options.items()},
            )
        )
    return rows
