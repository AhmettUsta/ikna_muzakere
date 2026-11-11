import json
import re
import shutil
from collections import Counter
from pathlib import Path

import pytest

from content_types import STYLE_ORDER, ContentError
from step_content import ContentStep

CONTENT_ROOT = Path(__file__).resolve().parent.parent / "src" / "content"

EXPECTED_THRESHOLDS = {
    "rekabet": (8, 3),
    "isbirligi": (10, 5),
    "uzlasma": (9, 4),
    "kacinma": (8, 4),
    "iltifat": (7, 3),
}


@pytest.fixture
def content_copy(tmp_path: Path) -> Path:
    target = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, target)
    return target


def _rewrite_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data = mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_load_real_content_passes() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    assert len(content.questions) == 30
    assert content.questions[0].a == (
        "Problemin çözümünde sorumluluğu başkasının almasına izin verdiğim zamanlar vardır."
    )
    assert content.questions[29].b == (
        "Problemi daima onunla paylaşırım, böylece üzerinde çalışabiliriz."
    )
    assert [s.key for s in content.styles] == list(STYLE_ORDER)
    for style in content.styles:
        assert (style.high, style.low) == EXPECTED_THRESHOLDS[style.key]


def test_load_answer_key_each_style_twelve_times() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    counts = Counter(
        style for options in content.answer_key.values() for style in options.values()
    )
    assert counts == {key: 12 for key in STYLE_ORDER}
    assert content.answer_key[1] == {"A": "kacinma", "B": "iltifat"}
    assert content.answer_key[30] == {"A": "iltifat", "B": "isbirligi"}


def test_load_missing_question_raises(content_copy: Path) -> None:
    _rewrite_json(content_copy / "questions.json", lambda data: data[:29])

    with pytest.raises(ContentError):
        ContentStep(content_copy).load()


def test_load_unknown_style_in_key_raises(content_copy: Path) -> None:
    def mutate(data: dict) -> dict:
        data["key"]["1"]["A"] = "X"
        return data

    _rewrite_json(content_copy / "scoring.json", mutate)

    with pytest.raises(ContentError):
        ContentStep(content_copy).load()


def test_load_invalid_json_raises(content_copy: Path) -> None:
    (content_copy / "questions.json").write_text("{bozuk", encoding="utf-8")

    with pytest.raises(ContentError, match="questions.json"):
        ContentStep(content_copy).load()


def test_sunum_section_types_per_style() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    for style in STYLE_ORDER:
        types = Counter(section.tur for section in content.sunum[style])
        assert types == {"davranis": 1, "uygun": 1, "uygun_degil": 1, "siz_iseniz": 1, "karsi_taraf": 1}


def test_sunum_sections_have_at_most_four_items() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    for style in STYLE_ORDER:
        for section in content.sunum[style]:
            assert 1 <= len(section.maddeler) <= 4, f"{style}/{section.tur}"


def test_sunum_items_share_grammar_per_section() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    for style in STYLE_ORDER:
        for section in content.sunum[style]:
            for item in section.maddeler:
                where = f"{style}/{section.tur}: {item}"
                if section.tur in ("uygun", "uygun_degil"):
                    # Koşul maddeleri "-dığında / -dığınızda" yan cümlesiyle, noktasız biter.
                    assert re.search(r"[dt][ıiuü]ğ[ıiuü]n([ıiuü]z)?[dt][ae]$", item), where
                elif section.tur == "davranis":
                    # Davranış maddeleri 3. tekil geniş zamanla (olumlu -r, olumsuz -z) biten tam cümledir.
                    assert item.endswith(("r.", "z.")), where
                else:
                    # Tavsiyeler emir kipiyle ("-in") biten tam cümledir.
                    assert item.endswith("n."), where


def test_sunum_spot_text() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    kacinma_uygun = next(s for s in content.sunum["kacinma"] if s.tur == "uygun")
    kacinma_uygun_degil = next(s for s in content.sunum["kacinma"] if s.tur == "uygun_degil")
    assert kacinma_uygun.maddeler[0] == "Yeni bilgi toplamanız ya da karşı tarafın söylemini doğrulatmanız gerektiğinde"
    assert kacinma_uygun_degil.maddeler[0] == "Elinizdeki bilgiler karar vermeye yettiğinde ve karşı tarafın söylemi doğrulandığında"


def test_sunum_too_many_items_raises(content_copy: Path) -> None:
    def mutate(data: dict) -> dict:
        data["bolumler"][0]["maddeler"] = ["Bir şey yapar."] * 5
        return data

    _rewrite_json(content_copy / "sunum" / "rekabet.json", mutate)

    with pytest.raises(ContentError, match="en fazla 4"):
        ContentStep(content_copy).load()


def test_sunum_missing_type_raises(content_copy: Path) -> None:
    def mutate(data: dict) -> dict:
        data["bolumler"] = [b for b in data["bolumler"] if b["tur"] != "uygun_degil"]
        return data

    _rewrite_json(content_copy / "sunum" / "rekabet.json", mutate)

    with pytest.raises(ContentError):
        ContentStep(content_copy).load()


def test_blocks_complete() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    assert len(content.blocks) == 15
    for style in STYLE_ORDER:
        for level in ("yuksek", "orta", "dusuk"):
            block = content.blocks[(style, level)]
            assert block.metin.strip()
            assert len(block.kaynaklar) >= 1


def test_profiles_complete() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    assert len(content.profiles) == 20
    for dominant, least in content.profiles:
        assert dominant != least
        assert dominant in STYLE_ORDER and least in STYLE_ORDER


def test_unknown_source_id_raises(content_copy: Path) -> None:
    def mutate(data: dict) -> dict:
        data["rekabet"]["yuksek"]["kaynaklar"] = ["olmayan-kaynak"]
        return data

    _rewrite_json(content_copy / "kaynakli" / "bloklar.json", mutate)

    with pytest.raises(ContentError, match="olmayan-kaynak"):
        ContentStep(content_copy).load()


def test_sources_have_citation() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    assert content.sources
    for source in content.sources:
        assert re.search(r"\b(19|20)\d{2}\b", source.kaynakca)
        assert source.ozet.strip()


def test_blocks_split_into_explanation_and_development() -> None:
    content = ContentStep(CONTENT_ROOT).load()

    for block in content.blocks.values():
        assert block.aciklama and "Gelişim için" not in block.aciklama
        assert block.gelisim and not block.gelisim.startswith("**")
