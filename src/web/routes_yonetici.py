import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Final, Literal

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, Response

from security import LockoutPolicy
from service import RegistrationError
from web.deps import get_service, is_admin, render

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/yonetici")

AdminLoginOutcome = Literal["basarili", "hatali", "kilitli"]
LOCKED_MESSAGE: Final[str] = "Çok fazla hatalı deneme yapıldı. Lütfen 15 dakika sonra tekrar deneyin."


@dataclass
class AdminLoginGuard:
    """Yönetici girişindeki hatalı denemeleri bellekte sayar (tek süreçli uygulama için yeterli)."""

    policy: LockoutPolicy = field(default_factory=LockoutPolicy)
    failed: int = 0
    locked_until: datetime | None = None

    def is_locked(self, now: datetime) -> bool:
        return self.policy.is_locked(self.locked_until, now)

    def register_failure(self, now: datetime) -> None:
        self.failed, self.locked_until = self.policy.after_failure(self.failed, now)

    def reset(self) -> None:
        self.failed, self.locked_until = 0, None


def admin_guard(request: Request) -> AdminLoginGuard:
    guard = getattr(request.app.state, "admin_guard", None)
    if guard is None:
        guard = AdminLoginGuard()
        request.app.state.admin_guard = guard
    return guard


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


@router.get("")
def admin_home(request: Request) -> Response:
    if is_admin(request):
        return _redirect("/yonetici/adaylar")
    return render(request, "yonetici_giris.html")


@router.post("")
def admin_login(request: Request, password: str = Form("")) -> Response:
    outcome = try_admin_login(request, password)
    if outcome == "kilitli":
        return render(request, "yonetici_giris.html", {"hata": LOCKED_MESSAGE}, status_code=429)
    if outcome == "hatali":
        return render(request, "yonetici_giris.html", {"hata": "Şifre hatalı."}, status_code=400)
    return _redirect("/yonetici/adaylar")


def try_admin_login(request: Request, password: str) -> AdminLoginOutcome:
    """Yönetici şifresini kilit kuralıyla kontrol eder; doğruysa oturumu yönetici olarak açar."""
    guard = admin_guard(request)
    now = datetime.now(timezone.utc)
    if guard.is_locked(now):
        return "kilitli"
    if not get_service(request).check_admin(password):
        guard.register_failure(now)
        logger.warning("Hatalı yönetici girişi denemesi")
        return "hatali"
    guard.reset()
    request.session.clear()
    request.session["is_admin"] = True
    logger.info("Yönetici girişi yapıldı")
    return "basarili"


@router.get("/adaylar")
def candidates(request: Request) -> Response:
    if not is_admin(request):
        return _redirect("/yonetici")
    return _candidate_list(request)


@router.get("/aday/{participant_id}")
def candidate(request: Request, participant_id: int) -> Response:
    if not is_admin(request):
        return _redirect("/yonetici")
    view = get_service(request).history_view(participant_id)
    if view is None:
        return render(request, "hata.html", {"mesaj": "Aday bulunamadı."}, status_code=404)
    return render(request, "gecmis.html", {"view": view, "yonetici_gorunumu": True})


def _candidate_list(request: Request, hata: str | None = None, status_code: int = 200) -> Response:
    context = {"adaylar": get_service(request).admin_participants(), "hata": hata}
    return render(request, "yonetici_adaylar.html", context, status_code=status_code)


@router.post("/aday/{participant_id}/ad")
def rename_candidate(request: Request, participant_id: int, nickname: str = Form("")) -> Response:
    if not is_admin(request):
        return _redirect("/yonetici")
    try:
        get_service(request).admin_rename(participant_id, nickname)
    except RegistrationError as exc:
        return _candidate_list(request, hata=str(exc), status_code=400)
    except LookupError:
        return render(request, "hata.html", {"mesaj": "Aday bulunamadı."}, status_code=404)
    return _redirect("/yonetici/adaylar")


@router.post("/aday/{participant_id}/sil")
def delete_candidate(request: Request, participant_id: int) -> Response:
    if not is_admin(request):
        return _redirect("/yonetici")
    if not get_service(request).admin_delete(participant_id):
        return render(request, "hata.html", {"mesaj": "Aday bulunamadı."}, status_code=404)
    return _redirect("/yonetici/adaylar")
