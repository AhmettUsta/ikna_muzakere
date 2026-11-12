import logging
import uuid
from typing import Final

from fastapi import APIRouter, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response

from chart import chart_svg
from scoring import ANSWER_COUNT
from service import LOGIN_FAILED_MESSAGE, LoginError, RegistrationError
from step_database import ParticipantMissing
from step_gemini import LiveCommentUnavailable
from web.deps import current_participant, get_service, render, viewer_of
from web.routes_yonetici import LOCKED_MESSAGE, try_admin_login

logger = logging.getLogger(__name__)
router = APIRouter()

INCOMPLETE_MESSAGE: Final[str] = "Lütfen 30 sorunun hepsini cevaplayın."
LIVE_ERROR_MESSAGE: Final[str] = "Şu anda canlı yorum üretilemiyor, daha sonra tekrar deneyin."


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def _not_found(request: Request) -> Response:
    return render(request, "hata.html", {"mesaj": "Aradığınız sayfa bulunamadı."}, status_code=404)


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


@router.get("/")
def home(request: Request) -> Response:
    return render(request, "giris.html")


@router.post("/kayit")
def register(request: Request, nickname: str = Form(""), pin: str = Form(""), pin_again: str = Form("")) -> Response:
    try:
        participant_id = get_service(request).register(nickname, pin, pin_again)
    except RegistrationError as exc:
        return render(request, "giris.html", {"kayit_hata": str(exc), "nickname": nickname}, status_code=400)
    request.session.clear()
    request.session["participant_id"] = participant_id
    return _redirect("/test")


@router.post("/giris")
def login(request: Request, nickname: str = Form(""), pin: str = Form("")) -> Response:
    service = get_service(request)
    if service.is_admin_name(nickname):
        # Yönetici, aday giriş formundan da girebilir; kilit kuralı yönetici sayfasıyla ortaktır.
        outcome = try_admin_login(request, pin)
        if outcome == "basarili":
            return _redirect("/yonetici/adaylar")
        message = LOCKED_MESSAGE if outcome == "kilitli" else LOGIN_FAILED_MESSAGE
        status = 429 if outcome == "kilitli" else 400
        return render(request, "giris.html", {"giris_hata": message, "giris_nickname": nickname}, status_code=status)
    try:
        participant_id = service.login(nickname, pin)
    except LoginError as exc:
        return render(request, "giris.html", {"giris_hata": str(exc), "giris_nickname": nickname}, status_code=400)
    request.session.clear()
    request.session["participant_id"] = participant_id
    return _redirect("/gecmis")


@router.post("/cikis")
def logout(request: Request) -> Response:
    request.session.clear()
    return _redirect("/")


@router.get("/test")
def test_page(request: Request) -> Response:
    if current_participant(request) is None:
        return _redirect("/")
    return render(request, "test.html", {"questions": get_service(request).content.questions})


@router.post("/test")
async def submit_test(request: Request) -> Response:
    participant_id = current_participant(request)
    if participant_id is None:
        return _redirect("/")
    form = await request.form()
    service = get_service(request)
    values = [str(form.get(f"q{number}", "")) for number in range(1, ANSWER_COUNT + 1)]
    try:
        # Her alan tek tek kontrol edilir; birleştirilmiş metnin uzunluğu "AB" + boş gibi
        # kaydırılmış cevapları ayırt edemez.
        if any(value not in ("A", "B") for value in values):
            raise ValueError("Her soru için A veya B seçilmeli")
        public_id = service.submit(participant_id, "".join(values))
    except ParticipantMissing:
        # Aday yönetici tarafından silinmiş; eski oturum kapatılır.
        request.session.clear()
        return _redirect("/")
    except ValueError:
        previous = {f"q{n}": str(form.get(f"q{n}", "")) for n in range(1, ANSWER_COUNT + 1)}
        return render(
            request,
            "test.html",
            {"questions": service.content.questions, "hata": INCOMPLETE_MESSAGE, "onceki": previous},
            status_code=400,
        )
    return _redirect(f"/sonuc/{public_id}")


def _result_page(
    request: Request, public_id: uuid.UUID, live_error: str | None = None, tab: str | None = None
) -> Response:
    service = get_service(request)
    view = service.result_view(public_id, viewer_of(request))
    if view is None:
        return _not_found(request)
    return render(
        request,
        "sonuc.html",
        {
            "view": view,
            "styles": service.content.style_by_key,
            "sources": {source.id: source for source in service.content.sources},
            "grafik": chart_svg(view.score, service.content.styles),
            "canli_hata": live_error,
            "aktif_sekme": "kaynak" if live_error else tab,
        },
    )


@router.get("/sonuc/{public_id}")
def result(request: Request, public_id: str, sekme: str | None = None) -> Response:
    parsed = _parse_uuid(public_id)
    if parsed is None:
        return _not_found(request)
    return _result_page(request, parsed, tab=sekme)


@router.post("/sonuc/{public_id}/canli-yorum")
def live_comment(request: Request, public_id: str) -> Response:
    parsed = _parse_uuid(public_id)
    participant_id = current_participant(request)
    if parsed is None or participant_id is None:
        return _not_found(request)
    try:
        text = get_service(request).live_comment(parsed, participant_id)
    except LiveCommentUnavailable:
        return _result_page(request, parsed, live_error=LIVE_ERROR_MESSAGE)
    if text is None:
        return _not_found(request)
    return _redirect(f"/sonuc/{parsed}?sekme=kaynak#canli")


@router.get("/gecmis")
def history(request: Request) -> Response:
    participant_id = current_participant(request)
    if participant_id is None:
        return _redirect("/")
    view = get_service(request).history_view(participant_id)
    if view is None:
        request.session.clear()
        return _redirect("/")
    return render(request, "gecmis.html", {"view": view, "yonetici_gorunumu": False})


@router.get("/robots.txt")
def robots() -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nDisallow: /\n")


@router.get("/saglik")
def health() -> PlainTextResponse:
    return PlainTextResponse("ok")
