import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1",
    reason="Gerçek veritabanı testleri yalnızca RUN_DB_TESTS=1 ile çalışır",
)

SCORES = {"rekabet": 9, "isbirligi": 7, "uzlasma": 6, "kacinma": 3, "iltifat": 5}
ANSWERS = "ABBABBBBBBBBBBABAAABBBABABBABB"


@pytest.fixture(scope="module")
def engine():
    from step_database import build_engine

    engine = build_engine()
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def db(engine):
    from step_database import DatabaseStep

    return DatabaseStep(engine)


@pytest.fixture
def nickname_key(engine):
    from sqlalchemy import delete, select

    from db_models import AiComment, Attempt, Participant

    key = f"test-{uuid.uuid4().hex[:12]}"
    yield key
    # Testin oluşturduğu satırları, yabancı anahtar sırasına göre temizler.
    with engine.begin() as conn:
        ids = select(Participant.id).where(Participant.nickname_key == key)
        attempt_ids = select(Attempt.id).where(Attempt.participant_id.in_(ids))
        conn.execute(delete(AiComment).where(AiComment.attempt_id.in_(attempt_ids)))
        conn.execute(delete(Attempt).where(Attempt.participant_id.in_(ids)))
        conn.execute(delete(Participant).where(Participant.nickname_key == key))


def test_create_and_get_participant(db, nickname_key: str) -> None:
    participant_id = db.create_participant("Test Kişi", nickname_key, b"hash", b"salt")

    row = db.get_participant_by_key(nickname_key)
    assert row is not None
    assert row.id == participant_id
    assert row.nickname == "Test Kişi"
    assert row.pin_hash == b"hash" and row.pin_salt == b"salt"
    assert row.failed_pins == 0 and row.locked_until is None
    assert db.get_participant(participant_id).nickname == "Test Kişi"


def test_duplicate_nickname_raises(db, nickname_key: str) -> None:
    from step_database import NicknameTaken

    db.create_participant("A", nickname_key, b"h", b"s")

    with pytest.raises(NicknameTaken):
        db.create_participant("B", nickname_key, b"h", b"s")


def test_attempt_roundtrip(db, nickname_key: str) -> None:
    participant_id = db.create_participant("A", nickname_key, b"h", b"s")

    first = db.create_attempt(participant_id, ANSWERS, SCORES)
    second = db.create_attempt(participant_id, "A" * 30, SCORES)

    row = db.get_attempt(first)
    assert row.answers == ANSWERS
    assert row.scores == SCORES
    assert row.participant_id == participant_id
    assert [a.public_id for a in db.list_attempts(participant_id)] == [second, first]


def test_ai_comment_saved_once(db, nickname_key: str) -> None:
    participant_id = db.create_participant("A", nickname_key, b"h", b"s")
    attempt = db.get_attempt(db.create_attempt(participant_id, ANSWERS, SCORES))

    db.save_ai_comment(attempt.id, "model-x", "ilk")
    db.save_ai_comment(attempt.id, "model-x", "ikinci")

    assert db.get_ai_comment(attempt.id) == "ilk"


def test_summaries_count_attempts(db, nickname_key: str) -> None:
    participant_id = db.create_participant("Özet", nickname_key, b"h", b"s")
    db.create_attempt(participant_id, ANSWERS, SCORES)
    db.create_attempt(participant_id, ANSWERS, SCORES)

    summary = next(s for s in db.list_participant_summaries() if s.id == participant_id)
    assert summary.nickname == "Özet"
    assert summary.attempt_count == 2
    assert summary.last_attempt_at is not None


def test_update_pin_state(db, nickname_key: str) -> None:
    from datetime import datetime, timezone

    participant_id = db.create_participant("A", nickname_key, b"h", b"s")
    until = datetime(2030, 1, 1, tzinfo=timezone.utc)

    db.update_pin_state(participant_id, 3, until)

    row = db.get_participant(participant_id)
    assert row.failed_pins == 3
    assert row.locked_until == until


def test_reserve_login_attempt_concurrent_allows_only_five(db, nickname_key: str) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timezone

    db.create_participant("A", nickname_key, b"h", b"s")
    now = datetime.now(timezone.utc)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: db.reserve_login_attempt(nickname_key, now, 5, 15), range(12)))

    reserved = [r for r in results if r is not None]
    assert len(reserved) == 5
    assert max(r.failed_pins for r in reserved) == 5
    assert db.get_participant_by_key(nickname_key).locked_until is not None


def test_reserve_login_attempt_after_lock_expires(db, nickname_key: str) -> None:
    from datetime import datetime, timedelta, timezone

    participant_id = db.create_participant("A", nickname_key, b"h", b"s")
    now = datetime.now(timezone.utc)
    db.update_pin_state(participant_id, 5, now - timedelta(minutes=1))

    row = db.reserve_login_attempt(nickname_key, now, 5, 15)

    assert row is not None
    assert row.failed_pins == 1
    assert row.locked_until is None


def test_reserve_login_attempt_unknown_key(db) -> None:
    from datetime import datetime, timezone

    assert db.reserve_login_attempt("olmayan-anahtar-xyz", datetime.now(timezone.utc), 5, 15) is None
