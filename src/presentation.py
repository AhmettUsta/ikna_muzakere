from dataclasses import dataclass, field
from typing import Final

from content_types import Block, Level, Question, Section, StyleKey
from scoring import StyleResult

LOW_NOTE: Final[str] = "Bu tarzı az kullanıyorsunuz. Yukarıdaki uygun koşullarda bu tarza geçmeyi deneyin."
MID_NOTE: Final[str] = "Bu tarzı orta düzeyde kullanıyorsunuz. Uygun koşullarda bilinçli olarak tercih edin."
CAUTION_TITLE: Final[str] = "Bu tarzı kullandığınızda dikkat edin"


@dataclass(frozen=True)
class Advice:
    not_metni: str | None
    liste_basligi: str | None
    maddeler: list[str] = field(default_factory=list)
    metin: str | None = None
    kaynakli: bool = False


@dataclass(frozen=True)
class StyleCard:
    style: StyleKey
    level: Level
    acik: bool
    davranis: Section
    kaynak_aciklama: str | None
    uygun: list[Section]
    uygun_degil: Section | None
    tavsiye: Advice
    karsi_taraf: Section


def _first(sections: list[Section], tur: str) -> Section | None:
    return next((section for section in sections if section.tur == tur), None)


def _sunum_advice(level: Level, siz_iseniz: Section) -> Advice:
    if level == "yuksek":
        return Advice(not_metni=None, liste_basligi=None, maddeler=list(siz_iseniz.maddeler))
    # Sunumda yalnızca bu tarzı çok kullananlara tavsiye var; az ya da orta kullananlara
    # aynı maddeler "kullandığınızda dikkat edin" çerçevesiyle gösterilir.
    note = LOW_NOTE if level == "dusuk" else MID_NOTE
    return Advice(not_metni=note, liste_basligi=CAUTION_TITLE, maddeler=list(siz_iseniz.maddeler))


def style_card(result: StyleResult, sections: list[Section], block: Block | None) -> StyleCard:
    """Bir tarzın kartını sabit sırayla kurar; block verilirse tavsiye kaynaklı metinden gelir."""
    siz_iseniz = _first(sections, "siz_iseniz")
    if block is None:
        advice = _sunum_advice(result.level, siz_iseniz)
    else:
        advice = Advice(not_metni=None, liste_basligi=None, metin=block.gelisim, kaynakli=True)
    return StyleCard(
        style=result.style,
        level=result.level,
        acik=result.level == "yuksek",
        davranis=_first(sections, "davranis"),
        kaynak_aciklama=block.aciklama if block is not None else None,
        uygun=[section for section in sections if section.tur == "uygun"],
        uygun_degil=_first(sections, "uygun_degil"),
        tavsiye=advice,
        karsi_taraf=_first(sections, "karsi_taraf"),
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
