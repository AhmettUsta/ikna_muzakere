from collections import Counter

import pytest

from content_types import Block, Section, SourcedText
from presentation import LOW_NOTE, MID_NOTE, ai_card, answer_rows, style_card
from scoring import StyleResult

DAVRANIS = Section(tur="davranis", baslik="D", maddeler=["d"])
UYGUN = Section(tur="uygun", baslik="U1", maddeler=["u1"])
UYGUN_DEGIL = Section(tur="uygun_degil", baslik="UD", maddeler=["ud"])
SIZ = Section(tur="siz_iseniz", baslik="S", maddeler=["s1", "s2"])
KARSI = Section(tur="karsi_taraf", baslik="K", maddeler=["k"])
# Sunumdaki sıra kartta kullanılmaz; kart sırası sabittir.
SECTIONS = [DAVRANIS, UYGUN, UYGUN_DEGIL, KARSI, SIZ]
BLOCK = Block(metin="Akademik açıklama.\n\n**Gelişim için:** Şunu deneyin.", kaynaklar=["thomas-1977"])
AI_SECTIONS = {
    "uygun": SourcedText(metin="Uygun metni.", kaynaklar=["thomas-1977"]),
    "uygun_degil": SourcedText(metin="Uygun değil metni.", kaynaklar=["rahim-2002"]),
    "karsi_taraf": SourcedText(metin="Karşı taraf metni.", kaynaklar=["fisher-ury-1981"]),
}


def _result(level: str) -> StyleResult:
    return StyleResult(style="rekabet", score=5, level=level, relative=0.5)


def test_card_has_fixed_section_order() -> None:
    card = style_card(_result("yuksek"), SECTIONS)

    assert card.davranis == DAVRANIS
    assert card.uygun == UYGUN
    assert card.uygun_degil == UYGUN_DEGIL
    assert card.karsi_taraf == KARSI


def test_card_high_sunum_advice_is_siz_iseniz() -> None:
    card = style_card(_result("yuksek"), SECTIONS)

    assert card.acik is True
    assert card.tavsiye.not_metni is None
    assert card.tavsiye.maddeler == ["s1", "s2"]


def test_card_low_sunum_advice_is_derived_from_presentation() -> None:
    card = style_card(_result("dusuk"), SECTIONS)

    assert card.acik is False
    assert card.tavsiye.not_metni == LOW_NOTE
    assert card.tavsiye.liste_basligi == "Bu tarzı kullandığınızda dikkat edin"
    assert card.tavsiye.maddeler == ["s1", "s2"]


def test_card_mid_sunum_advice_has_mid_note() -> None:
    card = style_card(_result("orta"), SECTIONS)

    assert card.acik is False
    assert card.tavsiye.not_metni == MID_NOTE
    assert card.tavsiye.maddeler == ["s1", "s2"]


def test_ai_card_uses_prose_for_every_section() -> None:
    card = ai_card(_result("dusuk"), BLOCK, AI_SECTIONS)

    assert card.style == "rekabet" and card.level == "dusuk" and card.acik is False
    assert card.davranis == "Akademik açıklama."
    assert card.tavsiye == "Şunu deneyin."
    assert card.uygun == "Uygun metni."
    assert card.uygun_degil == "Uygun değil metni."
    assert card.karsi_taraf == "Karşı taraf metni."


def test_ai_card_high_level_is_open() -> None:
    assert ai_card(_result("yuksek"), BLOCK, AI_SECTIONS).acik is True


def test_answer_rows_places_letters_in_style_columns(real_content) -> None:
    rows = answer_rows(real_content.questions, real_content.answer_key, "ABBABBBBBBBBBBABAAABBBABABBABB")

    assert len(rows) == 30
    # Cevap anahtarı fotoğrafı: 1. soruda A Kaçınma, B İltifatkar sütununda; A seçilmiş.
    assert rows[0].question.no == 1
    assert rows[0].harfler == {"kacinma": "A", "iltifat": "B"}
    assert rows[0].secilen == "A" and rows[0].secilen_tarz == "kacinma"
    assert rows[1].harfler == {"uzlasma": "A", "isbirligi": "B"}
    assert rows[1].secilen == "B" and rows[1].secilen_tarz == "isbirligi"


def test_answer_rows_column_counts_match_scores(real_content) -> None:
    rows = answer_rows(real_content.questions, real_content.answer_key, "ABBABBBBBBBBBBABAAABBBABABBABB")

    chosen = Counter(row.secilen_tarz for row in rows)
    assert chosen == {"rekabet": 9, "isbirligi": 7, "uzlasma": 6, "kacinma": 3, "iltifat": 5}


def test_answer_rows_rejects_wrong_length(real_content) -> None:
    with pytest.raises(ValueError):
        answer_rows(real_content.questions, real_content.answer_key, "A" * 29)
