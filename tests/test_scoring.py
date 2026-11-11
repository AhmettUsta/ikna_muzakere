from pathlib import Path

import pytest

from content_types import STYLE_ORDER
from scoring import Scorer
from step_content import ContentStep

CONTENT_ROOT = Path(__file__).resolve().parent.parent / "src" / "content"
DESIGN_EXAMPLE = "ABBABBBBBBBBBBABAAABBBABABBABB"


@pytest.fixture(scope="module")
def scorer() -> Scorer:
    content = ContentStep(CONTENT_ROOT).load()
    return Scorer(content.styles, content.answer_key)


def test_score_design_example(scorer: Scorer) -> None:
    result = scorer.score(DESIGN_EXAMPLE)

    assert [r.style for r in result.results] == list(STYLE_ORDER)
    assert [r.score for r in result.results] == [9, 7, 6, 3, 5]
    assert [r.level for r in result.results] == ["yuksek", "orta", "orta", "dusuk", "orta"]
    assert result.dominant == "rekabet"
    assert result.least == "kacinma"


@pytest.mark.parametrize(
    ("style", "score", "expected"),
    [
        ("rekabet", 8, "yuksek"),
        ("rekabet", 7, "orta"),
        ("rekabet", 4, "orta"),
        ("rekabet", 3, "dusuk"),
        ("isbirligi", 10, "yuksek"),
        ("isbirligi", 5, "dusuk"),
    ],
)
def test_level_boundaries(scorer: Scorer, style: str, score: int, expected: str) -> None:
    scores = {key: 6 for key in STYLE_ORDER}
    scores[style] = score

    result = scorer.from_scores(scores)

    level = next(r.level for r in result.results if r.style == style)
    assert level == expected


def test_relative_tie_uses_style_order(scorer: Scorer) -> None:
    # Her tarz tam yüksek eşiğinde: göreli puanların hepsi 1.0 olur.
    scores = {"rekabet": 8, "isbirligi": 10, "uzlasma": 9, "kacinma": 8, "iltifat": 7}

    result = scorer.from_scores(scores)

    assert {r.relative for r in result.results} == {1.0}
    assert result.dominant == "rekabet"
    assert result.least == "isbirligi"


@pytest.mark.parametrize("answers", ["A" * 29, "A" * 31, "A" * 29 + "C", "a" * 30, ""])
def test_count_rejects_bad_input(scorer: Scorer, answers: str) -> None:
    with pytest.raises(ValueError):
        scorer.count(answers)


@pytest.mark.parametrize("answers", ["A" * 30, "B" * 30, DESIGN_EXAMPLE])
def test_scores_always_sum_to_30(scorer: Scorer, answers: str) -> None:
    assert sum(scorer.count(answers).values()) == 30
