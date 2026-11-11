from html import escape
from typing import Final

from content_types import StyleDef
from scoring import ScoreResult

SIZE: Final[int] = 400
MARGIN: Final[int] = 48
PLOT: Final[int] = SIZE - 2 * MARGIN


def _point(x: int, y: int) -> tuple[float, float]:
    # İçerikteki konumlar 0-100 aralığında; SVG'de y ekseni aşağı doğru büyüdüğü için ters çevrilir.
    return MARGIN + x / 100 * PLOT, MARGIN + (100 - y) / 100 * PLOT


def chart_svg(score: ScoreResult, styles: list[StyleDef]) -> str:
    """Beş tarzı iki eksenli müzakere diyagramında puanlarıyla gösteren SVG üretir."""
    by_key = {style.key: style for style in styles}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" class="grafik" '
        'role="img" aria-label="Müzakere tarzları grafiği">',
        f'<line x1="{MARGIN}" y1="{SIZE - MARGIN}" x2="{SIZE - MARGIN + 8}" y2="{SIZE - MARGIN}" class="eksen"/>',
        f'<line x1="{MARGIN}" y1="{SIZE - MARGIN}" x2="{MARGIN}" y2="{MARGIN - 8}" class="eksen"/>',
        f'<text x="{SIZE / 2}" y="{SIZE - 12}" text-anchor="middle" class="eksen-yazi">'
        "Karşı tarafın ilgisini tatmin →</text>",
        f'<text x="16" y="{SIZE / 2}" text-anchor="middle" class="eksen-yazi" '
        f'transform="rotate(-90 16 {SIZE / 2})">Kendi ilgisini tatmin →</text>',
    ]
    for result in score.results:
        style = by_key[result.style]
        cx, cy = _point(style.x, style.y)
        radius = 10 + result.score * 2
        label = escape(f"{style.name} · {result.score}")
        parts.append(
            f'<g class="seviye-{result.level}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius}"/>'
            f'<text x="{cx:.1f}" y="{cy + radius + 16:.1f}" text-anchor="middle">{label}</text></g>'
        )
    parts.append("</svg>")
    return "".join(parts)
