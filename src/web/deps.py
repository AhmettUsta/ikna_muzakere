import re
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from typing import Any, Final

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from service import TestService, Viewer

WEB_ROOT: Final[Path] = Path(__file__).resolve().parent
BOLD_PATTERN: Final[re.Pattern[str]] = re.compile(r"\*\*(.+?)\*\*")
# Türkiye 2016'dan beri yaz saati uygulamadan sabit UTC+3 kullanıyor; tzdata gerektirmemek için sabit ofset.
TURKEY_TZ: Final[timezone] = timezone(timedelta(hours=3), "TRT")
MONTHS: Final[tuple[str, ...]] = (
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
)


def render_markdown(text: str) -> Markup:
    """Yalnızca paragraf ve **kalın** destekleyen küçük bir Markdown çevirici; önce HTML kaçışı yapılır."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    html = []
    for paragraph in paragraphs:
        safe = BOLD_PATTERN.sub(r"<strong>\1</strong>", escape(paragraph))
        html.append(f"<p>{safe.replace(chr(10), '<br>')}</p>")
    return Markup("".join(html))


def format_date(value: datetime) -> str:
    local = value.astimezone(TURKEY_TZ)
    return f"{local.day} {MONTHS[local.month - 1]} {local.year}, {local:%H:%M}"


templates = Jinja2Templates(directory=str(WEB_ROOT / "templates"))
templates.env.filters["md"] = render_markdown
templates.env.filters["tarih"] = format_date


def get_service(request: Request) -> TestService:
    return request.app.state.service


def current_participant(request: Request) -> int | None:
    value = request.session.get("participant_id")
    return int(value) if value is not None else None


def is_admin(request: Request) -> bool:
    return bool(request.session.get("is_admin"))


def viewer_of(request: Request) -> Viewer:
    return Viewer(participant_id=current_participant(request), is_admin=is_admin(request))


def render(request: Request, name: str, context: dict[str, Any] | None = None, status_code: int = 200) -> HTMLResponse:
    base = {"participant_id": current_participant(request), "is_admin": is_admin(request)}
    return templates.TemplateResponse(request, name, {**base, **(context or {})}, status_code=status_code)
