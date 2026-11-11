from pathlib import Path
from unittest.mock import MagicMock

import pytest
from google.genai import errors as genai_errors

from scoring import Scorer
from step_content import ContentStep
from step_gemini import GeminiStep, LiveCommentUnavailable, build_prompt

CONTENT_ROOT = Path(__file__).resolve().parent.parent / "src" / "content"
DESIGN_EXAMPLE = "ABBABBBBBBBBBBABAAABBBABABBABB"


@pytest.fixture(scope="module")
def content():
    return ContentStep(CONTENT_ROOT).load()


def test_build_prompt_contains_scores_and_sources(content) -> None:
    score = Scorer(content.styles, content.answer_key).score(DESIGN_EXAMPLE)

    prompt = build_prompt(score, content)

    assert "Rekabetçi: 9 (yüksek)" in prompt
    assert "Kaçınmacı: 3 (düşük)" in prompt
    assert "Baskın tarz: Rekabetçi" in prompt
    assert "En az kullanılan tarz: Kaçınmacı" in prompt
    for source in content.sources:
        assert f"[{source.id}]" in prompt
    assert "takma" not in prompt.lower()


def _client_returning(text: str | None) -> MagicMock:
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(text=text)
    return client


def test_generate_returns_text() -> None:
    client = _client_returning("Yorum metni")
    step = GeminiStep(api_key="k", model="m", client=client)

    assert step.generate("prompt") == "Yorum metni"
    assert client.models.generate_content.call_args.kwargs["model"] == "m"


@pytest.mark.parametrize("text", [None, "", "   "])
def test_generate_empty_text_raises(text: str | None) -> None:
    step = GeminiStep(api_key="k", model="m", client=_client_returning(text))

    with pytest.raises(LiveCommentUnavailable):
        step.generate("prompt")


def test_generate_maps_api_errors() -> None:
    client = MagicMock()
    client.models.generate_content.side_effect = genai_errors.ClientError(
        429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}}
    )
    step = GeminiStep(api_key="k", model="m", client=client)

    with pytest.raises(LiveCommentUnavailable):
        step.generate("prompt")
