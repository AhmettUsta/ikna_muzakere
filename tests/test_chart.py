from chart import chart_svg
from conftest import DESIGN_EXAMPLE
from scoring import Scorer


def test_chart_svg_contains_all_styles(real_content) -> None:
    score = Scorer(real_content.styles, real_content.answer_key).score(DESIGN_EXAMPLE)

    svg = chart_svg(score, real_content.styles)

    assert svg.startswith("<svg")
    for style in real_content.styles:
        assert style.name in svg
    assert "Rekabetçi · 9" in svg
    assert "Kendi ilgisini tatmin" in svg
    assert "Karşı tarafın ilgisini tatmin" in svg
    assert svg.count("<circle") == 5
    assert 'class="seviye-yuksek"' in svg and 'class="seviye-dusuk"' in svg
