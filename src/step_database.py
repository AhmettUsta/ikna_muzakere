import logging
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import Engine, and_, case, create_engine, delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import URL
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from sqlalchemy.orm import Session

from content_types import STYLE_ORDER, StyleKey
from db_models import AiComment, Attempt, Participant

logger = logging.getLogger(__name__)

POOLER_MARKER = "-pooler."


class NicknameTaken(Exception):
    """Takma ad başka bir katılımcı tarafından kullanılıyor."""


class DatabaseUnavailable(Exception):
    """Veritabanına ulaşılamıyor."""


class ParticipantMissing(Exception):
    """Katılımcı kaydı yok (ör. yönetici tarafından silinmiş)."""


@dataclass
class ParticipantRow:
    id: int
    nickname: str
    pin_hash: bytes
    pin_salt: bytes
    failed_pins: int
    locked_until: datetime | None


@dataclass
class AttemptRow:
    id: int
    public_id: uuid.UUID
    participant_id: int
    answers: str
    scores: dict[StyleKey, int]
    created_at: datetime


@dataclass
class ParticipantSummary:
    id: int
    nickname: str
    attempt_count: int
    last_attempt_at: datetime | None


def build_engine(direct: bool = False) -> Engine:
    """Config'teki Neon bilgileriyle bağlantı havuzu kurar."""
    from config import config

    host = config.PG_HOST
    if direct:
        # Neon şema değişikliklerinin havuzsuz adresle yapılmasını önerir.
        host = host.replace(POOLER_MARKER, ".")
    url = URL.create(
        "postgresql+psycopg",
        username=config.PG_USER,
        password=config.PG_PASSWORD,
        host=host,
        port=config.PG_PORT,
        database=config.PG_DATABASE,
        query={"sslmode": config.PG_SSLMODE},
    )
    engine = create_engine(
        url,
        pool_size=2,
        max_overflow=2,
        pool_pre_ping=True,
        # PgBouncer (transaction modu) hazır sorgularla sorun çıkarabildiği için kapatılır.
        connect_args={"prepare_threshold": None, "connect_timeout": 15},
    )
    return engine.execution_options(schema_translate_map={None: config.PG_SCHEMA})


def _to_participant(row: Participant) -> ParticipantRow:
    return ParticipantRow(
        id=row.id,
        nickname=row.nickname,
        pin_hash=bytes(row.pin_hash),
        pin_salt=bytes(row.pin_salt),
        failed_pins=row.failed_pins,
        locked_until=row.locked_until,
    )


def _to_attempt(row: Attempt) -> AttemptRow:
    return AttemptRow(
        id=row.id,
        public_id=row.public_id,
        participant_id=row.participant_id,
        answers=row.answers,
        scores={style: getattr(row, f"score_{style}") for style in STYLE_ORDER},
        created_at=row.created_at,
    )


class DatabaseStep:
    """Katılımcı, deneme ve yapay zekâ yorumu kayıtlarını yönetir."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @contextmanager
    def _session(self) -> Iterator[Session]:
        try:
            with Session(self._engine, expire_on_commit=False) as session, session.begin():
                yield session
        except (OperationalError, PoolTimeoutError) as exc:
            logger.error("Veritabanına ulaşılamadı: %s", exc.__class__.__name__)
            raise DatabaseUnavailable("Veritabanına ulaşılamadı") from exc

    def create_participant(self, nickname: str, nickname_key: str, pin_hash: bytes, pin_salt: bytes) -> int:
        try:
            with self._session() as session:
                participant = Participant(
                    nickname=nickname, nickname_key=nickname_key, pin_hash=pin_hash, pin_salt=pin_salt
                )
                session.add(participant)
                session.flush()
                return participant.id
        except IntegrityError as exc:
            raise NicknameTaken(nickname_key) from exc

    def get_participant_by_key(self, key: str) -> ParticipantRow | None:
        with self._session() as session:
            row = session.scalar(select(Participant).where(Participant.nickname_key == key))
            return _to_participant(row) if row else None

    def get_participant(self, participant_id: int) -> ParticipantRow | None:
        with self._session() as session:
            row = session.get(Participant, participant_id)
            return _to_participant(row) if row else None

    def update_pin_state(self, participant_id: int, failed_pins: int, locked_until: datetime | None) -> None:
        with self._session() as session:
            session.execute(
                update(Participant)
                .where(Participant.id == participant_id)
                .values(failed_pins=failed_pins, locked_until=locked_until)
            )

    def reserve_login_attempt(
        self, key: str, now: datetime, max_failures: int, lock_minutes: int
    ) -> ParticipantRow | None:
        """Kilitli olmayan katılımcı için bir giriş denemesini PIN doğrulanmadan önce atomik olarak sayar.

        Sayaç doğrulamadan önce tek bir UPDATE ile artırıldığı için eşzamanlı istekler
        kilit penceresinde en fazla max_failures deneme yapabilir. Kilitliyse ya da
        takma ad yoksa None döner.
        """
        expired = and_(Participant.locked_until.is_not(None), Participant.locked_until <= now)
        next_count = case((expired, 1), else_=Participant.failed_pins + 1)
        statement = (
            update(Participant)
            .where(Participant.nickname_key == key)
            .where(or_(Participant.locked_until.is_(None), Participant.locked_until <= now))
            .values(
                failed_pins=next_count,
                locked_until=case(
                    (next_count >= max_failures, now + timedelta(minutes=lock_minutes)),
                    (expired, None),
                    else_=Participant.locked_until,
                ),
            )
            .returning(Participant)
        )
        with self._session() as session:
            row = session.execute(statement, execution_options={"synchronize_session": False}).scalar_one_or_none()
            return _to_participant(row) if row else None

    def create_attempt(self, participant_id: int, answers: str, scores: dict[StyleKey, int]) -> uuid.UUID:
        try:
            with self._session() as session:
                attempt = Attempt(
                    public_id=uuid.uuid4(),
                    participant_id=participant_id,
                    answers=answers,
                    **{f"score_{style}": scores[style] for style in STYLE_ORDER},
                )
                session.add(attempt)
                session.flush()
                return attempt.public_id
        except IntegrityError as exc:
            # Tek yabancı anahtar participant_id'dir; ihlal, katılımcının silinmiş olduğu anlamına gelir.
            raise ParticipantMissing(participant_id) from exc

    def rename_participant(self, participant_id: int, nickname: str, nickname_key: str) -> bool:
        """Takma adı değiştirir; katılımcı yoksa False döner, ad alınmışsa NicknameTaken fırlatır."""
        try:
            with self._session() as session:
                result = session.execute(
                    update(Participant)
                    .where(Participant.id == participant_id)
                    .values(nickname=nickname, nickname_key=nickname_key)
                )
                return result.rowcount > 0
        except IntegrityError as exc:
            raise NicknameTaken(nickname_key) from exc

    def delete_participant(self, participant_id: int) -> bool:
        """Katılımcıyı, denemelerini ve yapay zekâ yorumlarını tek işlemde siler; yoksa False döner."""
        with self._session() as session:
            attempt_ids = select(Attempt.id).where(Attempt.participant_id == participant_id)
            # Yabancı anahtarlarda cascade yok; çocuk satırlar önce silinir.
            session.execute(delete(AiComment).where(AiComment.attempt_id.in_(attempt_ids)))
            session.execute(delete(Attempt).where(Attempt.participant_id == participant_id))
            result = session.execute(delete(Participant).where(Participant.id == participant_id))
            return result.rowcount > 0

    def get_attempt(self, public_id: uuid.UUID) -> AttemptRow | None:
        with self._session() as session:
            row = session.scalar(select(Attempt).where(Attempt.public_id == public_id))
            return _to_attempt(row) if row else None

    def list_attempts(self, participant_id: int) -> list[AttemptRow]:
        with self._session() as session:
            rows = session.scalars(
                select(Attempt)
                .where(Attempt.participant_id == participant_id)
                .order_by(Attempt.created_at.desc(), Attempt.id.desc())
            )
            return [_to_attempt(row) for row in rows]

    def get_ai_comment(self, attempt_id: int) -> str | None:
        with self._session() as session:
            return session.scalar(select(AiComment.text).where(AiComment.attempt_id == attempt_id))

    def save_ai_comment(self, attempt_id: int, model: str, text: str) -> None:
        with self._session() as session:
            session.execute(
                insert(AiComment)
                .values(attempt_id=attempt_id, model=model, text=text)
                .on_conflict_do_nothing(index_elements=[AiComment.attempt_id])
            )

    def list_participant_summaries(self) -> list[ParticipantSummary]:
        with self._session() as session:
            last = func.max(Attempt.created_at)
            rows = session.execute(
                select(Participant.id, Participant.nickname, func.count(Attempt.id), last)
                .outerjoin(Attempt, Attempt.participant_id == Participant.id)
                .group_by(Participant.id, Participant.nickname)
                .order_by(last.desc().nulls_last(), Participant.nickname)
            )
            return [ParticipantSummary(id=r[0], nickname=r[1], attempt_count=r[2], last_attempt_at=r[3]) for r in rows]
