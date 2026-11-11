import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scoring import Scorer
from security import LockoutPolicy, PinHasher
from service import TestService
from step_content import ContentStep
from step_database import AttemptRow, ParticipantRow

CONTENT_ROOT = Path(__file__).resolve().parent.parent / "src" / "content"
DESIGN_EXAMPLE = "ABBABBBBBBBBBBABAAABBBABABBABB"
DESIGN_SCORES = {"rekabet": 9, "isbirligi": 7, "uzlasma": 6, "kacinma": 3, "iltifat": 5}
NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
OWNER_ID = 7
PUBLIC_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture(scope="session")
def real_content():
    return ContentStep(CONTENT_ROOT).load()


@pytest.fixture
def fake_db() -> MagicMock:
    db = MagicMock()
    db.get_attempt.return_value = AttemptRow(
        id=3, public_id=PUBLIC_ID, participant_id=OWNER_ID, answers=DESIGN_EXAMPLE,
        scores=DESIGN_SCORES, created_at=NOW,
    )
    db.get_participant.return_value = ParticipantRow(
        id=OWNER_ID, nickname="Ali", pin_hash=b"", pin_salt=b"", failed_pins=0, locked_until=None
    )
    db.get_ai_comment.return_value = None
    db.create_participant.return_value = OWNER_ID
    db.create_attempt.return_value = PUBLIC_ID
    db.list_attempts.return_value = [db.get_attempt.return_value]
    db.list_participant_summaries.return_value = []
    return db


@pytest.fixture
def make_web_service(real_content, fake_db):
    def factory(gemini=None) -> TestService:
        return TestService(
            content=real_content,
            scorer=Scorer(real_content.styles, real_content.answer_key),
            db=fake_db,
            hasher=PinHasher(),
            lockout=LockoutPolicy(),
            gemini=gemini,
            gemini_model="model-x" if gemini else None,
            admin_username="ustaoglu",
        admin_password="gizli",
            clock=lambda: NOW,
        )

    return factory
