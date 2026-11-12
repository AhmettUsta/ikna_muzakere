import hmac
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from content_types import Content, ProfileText
from presentation import AiCard, AnswerRow, StyleCard, ai_card, answer_rows, style_card
from scoring import Scorer, ScoreResult
from security import LockoutPolicy, PinHasher, normalize_nickname, validate_pin
from step_database import AttemptRow, DatabaseStep, NicknameTaken, ParticipantSummary
from step_gemini import GeminiStep, LiveCommentUnavailable, build_prompt

logger = logging.getLogger(__name__)

LOGIN_FAILED_MESSAGE = "Takma ad veya PIN hatalı."


class RegistrationError(ValueError):
    """Kayıt bilgileri geçersiz ya da takma ad alınmış."""


class LoginError(ValueError):
    """Giriş başarısız."""


class AccountLocked(LoginError):
    def __init__(self, until: datetime) -> None:
        super().__init__("Çok fazla hatalı deneme yapıldı. Lütfen 15 dakika sonra tekrar deneyin.")
        self.until = until


@dataclass(frozen=True)
class Viewer:
    participant_id: int | None
    is_admin: bool


@dataclass
class ResultView:
    nickname: str
    created_at: datetime
    public_id: uuid.UUID
    score: ScoreResult
    kartlar_sunum: list[StyleCard]
    kartlar_kaynakli: list[AiCard]
    profile: ProfileText
    answers: list[AnswerRow]
    ai_comment: str | None
    live_enabled: bool
    can_request_live: bool


@dataclass
class HistoryView:
    nickname: str
    attempts: list[AttemptRow]


class TestService:
    """Kayıt, giriş, test, sonuç ve yönetici akışlarını yönetir."""

    __test__ = False  # pytest'in bu sınıfı test sınıfı sanmasını engeller.

    def __init__(
        self,
        content: Content,
        scorer: Scorer,
        db: DatabaseStep,
        hasher: PinHasher,
        lockout: LockoutPolicy,
        gemini: GeminiStep | None,
        gemini_model: str | None,
        admin_username: str,
        admin_password: str,
        clock: Callable[[], datetime],
    ) -> None:
        self.content = content
        self._scorer = scorer
        self._db = db
        self._hasher = hasher
        self._lockout = lockout
        self._gemini = gemini
        self._gemini_model = gemini_model
        self._admin_key = normalize_nickname(admin_username)[1]
        self._admin_password = admin_password
        self._clock = clock

    def register(self, nickname: str, pin: str, pin_again: str) -> int:
        display, key = self._checked_nickname(nickname)
        try:
            validate_pin(pin)
        except ValueError as exc:
            raise RegistrationError(str(exc)) from exc
        if pin != pin_again:
            raise RegistrationError("PIN'ler birbiriyle aynı değil.")
        digest, salt = self._hasher.hash(pin)
        try:
            participant_id = self._db.create_participant(display, key, digest, salt)
        except NicknameTaken as exc:
            raise RegistrationError("Bu takma ad alınmış, lütfen başka bir ad seçin.") from exc
        logger.info("Yeni katılımcı kaydedildi: id=%d", participant_id)
        return participant_id

    def _checked_nickname(self, nickname: str) -> tuple[str, str]:
        """Takma adı kayıt kurallarıyla doğrular; (görünen ad, anahtar) döner."""
        try:
            display, key = normalize_nickname(nickname)
        except ValueError as exc:
            raise RegistrationError(str(exc)) from exc
        if key == self._admin_key:
            raise RegistrationError("Bu takma ad kullanılamaz, lütfen başka bir ad seçin.")
        return display, key

    def login(self, nickname: str, pin: str) -> int:
        try:
            _, key = normalize_nickname(nickname)
        except ValueError as exc:
            raise LoginError(LOGIN_FAILED_MESSAGE) from exc

        now = self._clock()
        reserved = self._db.reserve_login_attempt(
            key, now, self._lockout.max_failures, self._lockout.lock_minutes
        )
        if reserved is None:
            participant = self._db.get_participant_by_key(key)
            if participant is not None and self._lockout.is_locked(participant.locked_until, now):
                raise AccountLocked(participant.locked_until)
            raise LoginError(LOGIN_FAILED_MESSAGE)

        if not self._hasher.verify(pin, reserved.pin_hash, reserved.pin_salt):
            logger.info("Hatalı PIN denemesi: id=%d", reserved.id)
            if self._lockout.is_locked(reserved.locked_until, now):
                raise AccountLocked(reserved.locked_until)
            raise LoginError(LOGIN_FAILED_MESSAGE)

        self._db.update_pin_state(reserved.id, 0, None)
        logger.info("Giriş yapıldı: id=%d", reserved.id)
        return reserved.id

    def submit(self, participant_id: int, answers: str) -> uuid.UUID:
        counts = self._scorer.count(answers)
        public_id = self._db.create_attempt(participant_id, answers, counts)
        logger.info("Test kaydedildi: katılımcı=%d", participant_id)
        return public_id

    def result_view(self, public_id: uuid.UUID, viewer: Viewer) -> ResultView | None:
        attempt = self._db.get_attempt(public_id)
        if attempt is None:
            return None
        is_owner = viewer.participant_id is not None and viewer.participant_id == attempt.participant_id
        if not (is_owner or viewer.is_admin):
            return None
        participant = self._db.get_participant(attempt.participant_id)
        score = self._scorer.from_scores(attempt.scores)
        live_enabled = self._gemini is not None
        return ResultView(
            nickname=participant.nickname if participant else "",
            created_at=attempt.created_at,
            public_id=attempt.public_id,
            score=score,
            kartlar_sunum=[
                style_card(result, self.content.sunum[result.style], self.content.sunum_tavsiye[result.style])
                for result in score.results
            ],
            kartlar_kaynakli=[
                ai_card(
                    result,
                    self.content.blocks[(result.style, result.level)],
                    self.content.ai_bolumler[result.style],
                )
                for result in score.results
            ],
            profile=self.content.profiles[(score.dominant, score.least)],
            answers=answer_rows(self.content.questions, self.content.answer_key, attempt.answers),
            ai_comment=self._db.get_ai_comment(attempt.id),
            live_enabled=live_enabled,
            can_request_live=live_enabled and is_owner,
        )

    def history_view(self, participant_id: int) -> HistoryView | None:
        participant = self._db.get_participant(participant_id)
        if participant is None:
            return None
        return HistoryView(nickname=participant.nickname, attempts=self._db.list_attempts(participant_id))

    def live_comment(self, public_id: uuid.UUID, participant_id: int) -> str | None:
        attempt = self._db.get_attempt(public_id)
        if attempt is None or attempt.participant_id != participant_id:
            return None
        saved = self._db.get_ai_comment(attempt.id)
        if saved is not None:
            return saved
        if self._gemini is None:
            raise LiveCommentUnavailable("Canlı yorum bu sitede kapalı")
        prompt = build_prompt(self._scorer.from_scores(attempt.scores), self.content)
        text = self._gemini.generate(prompt)
        self._db.save_ai_comment(attempt.id, self._gemini_model or "", text)
        # Aynı anda iki istek gelirse ilk kaydedilen yorum geçerli olur.
        return self._db.get_ai_comment(attempt.id) or text

    def is_admin_name(self, nickname: str) -> bool:
        try:
            return normalize_nickname(nickname)[1] == self._admin_key
        except ValueError:
            return False

    def check_admin(self, password: str) -> bool:
        return hmac.compare_digest(password.encode("utf-8"), self._admin_password.encode("utf-8"))

    def admin_participants(self) -> list[ParticipantSummary]:
        return self._db.list_participant_summaries()

    def admin_rename(self, participant_id: int, nickname: str) -> str:
        """Adayın takma adını değiştirir; geçersiz ya da alınmış adda RegistrationError, aday yoksa LookupError."""
        display, key = self._checked_nickname(nickname)
        try:
            found = self._db.rename_participant(participant_id, display, key)
        except NicknameTaken as exc:
            raise RegistrationError("Bu takma ad alınmış, lütfen başka bir ad seçin.") from exc
        if not found:
            raise LookupError(f"Aday bulunamadı: id={participant_id}")
        logger.info("Yönetici adayın adını değiştirdi: id=%d", participant_id)
        return display

    def admin_delete(self, participant_id: int) -> bool:
        """Adayı bütün denemeleriyle siler; aday yoksa False döner."""
        deleted = self._db.delete_participant(participant_id)
        if deleted:
            logger.info("Yönetici adayı sildi: id=%d", participant_id)
        return deleted
