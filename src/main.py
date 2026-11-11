import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from service import TestService
from step_database import DatabaseUnavailable
from web.deps import WEB_ROOT, render
from web.routes_aday import router as aday_router
from web.routes_yonetici import router as yonetici_router

logger = logging.getLogger(__name__)

SESSION_MAX_AGE = 7 * 24 * 60 * 60
CONTENT_ROOT = Path(__file__).resolve().parent / "content"


def create_app(service: TestService, session_secret: str, cookie_secure: bool) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.service = service
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        max_age=SESSION_MAX_AGE,
        same_site="lax",
        https_only=cookie_secure,
    )
    app.mount("/static", StaticFiles(directory=str(WEB_ROOT / "static")), name="static")
    app.include_router(aday_router)
    app.include_router(yonetici_router)

    @app.exception_handler(DatabaseUnavailable)
    async def database_unavailable(request: Request, exc: DatabaseUnavailable) -> Response:
        return render(
            request, "hata.html", {"mesaj": "Şu anda hizmet veremiyoruz, biraz sonra tekrar deneyin."}, 503
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> Response:
        message = "Aradığınız sayfa bulunamadı." if exc.status_code == 404 else "İstek işlenemedi."
        return render(request, "hata.html", {"mesaj": message}, exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> Response:
        # Son savunma hattı: kullanıcıya iç hata ayrıntısı gösterilmez, ayrıntı loglanır.
        logger.exception("Beklenmeyen hata: %s %s", request.method, request.url.path)
        return render(request, "hata.html", {"mesaj": "Beklenmeyen bir hata oluştu."}, 500)

    return app


def build_default_app() -> FastAPI:
    """Gerçek nesneleri config'ten kurar; yalnızca uvicorn başlatırken çağrılır."""
    from config import config
    from logger import setup_logging
    from scoring import Scorer
    from security import LockoutPolicy, PinHasher
    from step_content import ContentStep
    from step_database import DatabaseStep, build_engine
    from step_gemini import GeminiStep

    setup_logging()
    content = ContentStep(CONTENT_ROOT).load()
    gemini = None
    # Kişiselleştirme kutusu ayar açık değilse tıklanamaz görünür.
    if config.LIVE_COMMENT_ENABLED and config.GEMINI_API_KEY and config.GEMINI_MODEL:
        gemini = GeminiStep(api_key=config.GEMINI_API_KEY, model=config.GEMINI_MODEL)
    service = TestService(
        content=content,
        scorer=Scorer(content.styles, content.answer_key),
        db=DatabaseStep(build_engine()),
        hasher=PinHasher(),
        lockout=LockoutPolicy(),
        gemini=gemini,
        gemini_model=config.GEMINI_MODEL,
        admin_username=config.ADMIN_USERNAME,
        admin_password=config.ADMIN_PASSWORD,
        clock=lambda: datetime.now(timezone.utc),
    )
    logger.info("Uygulama hazır; canlı yorum %s", "açık" if gemini else "kapalı")
    return create_app(service, config.SESSION_SECRET, bool(config.COOKIE_SECURE))


def __getattr__(name: str) -> FastAPI:
    # "uvicorn main:app" bu özniteliği ister; testler create_app'i doğrudan kullanır
    # ve config yüklenmeden modül import edilebilir.
    if name == "app":
        globals()["app"] = build_default_app()
        return globals()["app"]
    raise AttributeError(name)
