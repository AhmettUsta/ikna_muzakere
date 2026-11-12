import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scoring import Scorer
from security import LockoutPolicy, PinHasher, normalize_nickname
from service import AccountLocked, LoginError, RegistrationError, TestService, Viewer
from step_content import ContentStep
from step_database import AttemptRow, NicknameTaken, ParticipantRow
from step_gemini import LiveCommentUnavailable

CONTENT_ROOT = Path(__file__).resolve().parent.parent / "src" / "content"
DESIGN_EXAMPLE = "ABBABBBBBBBBBBABAAABBBABABBABB"
DESIGN_SCORES = {"rekabet": 9, "isbirligi": 7, "uzlasma": 6, "kacinma": 3, "iltifat": 5}
NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
OWNER_ID = 7
PUBLIC_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture(scope="module")
def content():
    return ContentStep(CONTENT_ROOT).load()


@pytest.fixture
def db() -> MagicMock:
    db = MagicMock()
    db.get_attempt.return_value = AttemptRow(
        id=3, public_id=PUBLIC_ID, participant_id=OWNER_ID, answers=DESIGN_EXAMPLE,
        scores=DESIGN_SCORES, created_at=NOW,
    )
    db.get_participant.return_value = ParticipantRow(
        id=OWNER_ID, nickname="Ali", pin_hash=b"", pin_salt=b"", failed_pins=0, locked_until=None
    )
    db.get_ai_comment.return_value = None
    return db


@pytest.fixture
def hasher() -> PinHasher:
    return PinHasher()


def make_service(content, db, hasher, gemini=None) -> TestService:
    return TestService(
        content=content,
        scorer=Scorer(content.styles, content.answer_key),
        db=db,
        hasher=hasher,
        lockout=LockoutPolicy(),
        gemini=gemini,
        gemini_model="model-x" if gemini else None,
        admin_username="ustaoglu",
        admin_password="gizli",
        clock=lambda: NOW,
    )


def stored_participant(hasher: PinHasher, failed: int = 0, locked_until=None) -> ParticipantRow:
    digest, salt = hasher.hash("1234")
    return ParticipantRow(
        id=OWNER_ID, nickname="Ali", pin_hash=digest, pin_salt=salt, failed_pins=failed, locked_until=locked_until
    )


def test_register_creates_participant(content, db, hasher) -> None:
    db.create_participant.return_value = OWNER_ID

    assert make_service(content, db, hasher).register(" ALİ ", "1234", "1234") == OWNER_ID
    args = db.create_participant.call_args.args
    assert args[0] == "ALİ" and args[1] == "ali"


def test_register_pin_mismatch(content, db, hasher) -> None:
    with pytest.raises(RegistrationError, match="PIN"):
        make_service(content, db, hasher).register("Ali", "1234", "1235")


def test_register_nickname_taken(content, db, hasher) -> None:
    db.create_participant.side_effect = NicknameTaken("ali")

    with pytest.raises(RegistrationError, match="alınmış"):
        make_service(content, db, hasher).register("Ali", "1234", "1234")


def test_register_invalid_nickname(content, db, hasher) -> None:
    with pytest.raises(RegistrationError):
        make_service(content, db, hasher).register("a", "1234", "1234")


def test_login_success_resets_counter(content, db, hasher) -> None:
    db.reserve_login_attempt.return_value = stored_participant(hasher, failed=4)

    assert make_service(content, db, hasher).login("ali", "1234") == OWNER_ID
    db.reserve_login_attempt.assert_called_once_with("ali", NOW, 5, 15)
    db.update_pin_state.assert_called_once_with(OWNER_ID, 0, None)


def test_login_wrong_pin_counts_reserved_attempt(content, db, hasher) -> None:
    db.reserve_login_attempt.return_value = stored_participant(hasher, failed=4)

    with pytest.raises(LoginError, match="Takma ad veya PIN hatalı"):
        make_service(content, db, hasher).login("Ali", "9999")
    db.update_pin_state.assert_not_called()


def test_login_wrong_pin_on_fifth_attempt_locks(content, db, hasher) -> None:
    until = NOW + timedelta(minutes=15)
    db.reserve_login_attempt.return_value = stored_participant(hasher, failed=5, locked_until=until)

    with pytest.raises(AccountLocked):
        make_service(content, db, hasher).login("Ali", "9999")


def test_login_while_locked(content, db, hasher) -> None:
    db.reserve_login_attempt.return_value = None
    db.get_participant_by_key.return_value = stored_participant(hasher, locked_until=NOW + timedelta(minutes=5))

    with pytest.raises(AccountLocked):
        make_service(content, db, hasher).login("Ali", "1234")
    db.update_pin_state.assert_not_called()


def test_login_unknown_nickname_same_message(content, db, hasher) -> None:
    db.reserve_login_attempt.return_value = None
    db.get_participant_by_key.return_value = None

    with pytest.raises(LoginError, match="Takma ad veya PIN hatalı"):
        make_service(content, db, hasher).login("Yok", "1234")


def test_submit_scores_and_saves(content, db, hasher) -> None:
    db.create_attempt.return_value = PUBLIC_ID

    assert make_service(content, db, hasher).submit(OWNER_ID, DESIGN_EXAMPLE) == PUBLIC_ID
    db.create_attempt.assert_called_once_with(OWNER_ID, DESIGN_EXAMPLE, DESIGN_SCORES)


def test_submit_rejects_bad_answers(content, db, hasher) -> None:
    with pytest.raises(ValueError):
        make_service(content, db, hasher).submit(OWNER_ID, "A" * 29)
    db.create_attempt.assert_not_called()


def test_result_view_owner(content, db, hasher) -> None:
    view = make_service(content, db, hasher).result_view(PUBLIC_ID, Viewer(OWNER_ID, False))

    assert view.nickname == "Ali"
    assert [r.score for r in view.score.results] == [9, 7, 6, 3, 5]
    assert len(view.answers) == 30
    assert view.answers[0].secilen == "A" and view.answers[0].secilen_tarz == "kacinma"
    assert [card.style for card in view.kartlar_sunum] == ["rekabet", "isbirligi", "uzlasma", "kacinma", "iltifat"]
    assert view.kartlar_sunum[0].tavsiye.maddeler
    assert view.kartlar_sunum[3].tavsiye.maddeler == content.sunum_tavsiye["kacinma"]["dusuk"]
    assert view.kartlar_kaynakli[3].tavsiye == content.blocks[("kacinma", "dusuk")].gelisim
    assert view.kartlar_kaynakli[3].uygun == content.ai_bolumler["kacinma"]["uygun"].metin
    assert view.live_enabled is False and view.can_request_live is False


def test_result_view_uses_profile_of_dominant_least(content, db, hasher) -> None:
    view = make_service(content, db, hasher).result_view(PUBLIC_ID, Viewer(OWNER_ID, False))

    assert view.profile == content.profiles[("rekabet", "kacinma")]


def test_result_view_other_participant_none(content, db, hasher) -> None:
    service = make_service(content, db, hasher)

    assert service.result_view(PUBLIC_ID, Viewer(OWNER_ID + 1, False)) is None
    assert service.result_view(PUBLIC_ID, Viewer(None, False)) is None


def test_result_view_missing_attempt_none(content, db, hasher) -> None:
    db.get_attempt.return_value = None

    assert make_service(content, db, hasher).result_view(PUBLIC_ID, Viewer(OWNER_ID, False)) is None


def test_result_view_admin_sees(content, db, hasher) -> None:
    gemini = MagicMock()
    view = make_service(content, db, hasher, gemini).result_view(PUBLIC_ID, Viewer(None, True))

    assert view is not None
    assert view.live_enabled is True
    assert view.can_request_live is False


def test_live_comment_generates_and_saves(content, db, hasher) -> None:
    gemini = MagicMock()
    gemini.generate.return_value = "Canlı yorum"

    text = make_service(content, db, hasher, gemini).live_comment(PUBLIC_ID, OWNER_ID)

    assert text == "Canlı yorum"
    db.save_ai_comment.assert_called_once_with(3, "model-x", "Canlı yorum")


def test_live_comment_cached_no_second_call(content, db, hasher) -> None:
    gemini = MagicMock()
    db.get_ai_comment.return_value = "Kayıtlı yorum"

    text = make_service(content, db, hasher, gemini).live_comment(PUBLIC_ID, OWNER_ID)

    assert text == "Kayıtlı yorum"
    gemini.generate.assert_not_called()


def test_live_comment_not_owner_none(content, db, hasher) -> None:
    gemini = MagicMock()

    assert make_service(content, db, hasher, gemini).live_comment(PUBLIC_ID, OWNER_ID + 1) is None
    gemini.generate.assert_not_called()


def test_live_comment_disabled_when_no_gemini(content, db, hasher) -> None:
    with pytest.raises(LiveCommentUnavailable):
        make_service(content, db, hasher).live_comment(PUBLIC_ID, OWNER_ID)


def test_live_comment_propagates_unavailable(content, db, hasher) -> None:
    gemini = MagicMock()
    gemini.generate.side_effect = LiveCommentUnavailable("kota")

    with pytest.raises(LiveCommentUnavailable):
        make_service(content, db, hasher, gemini).live_comment(PUBLIC_ID, OWNER_ID)
    db.save_ai_comment.assert_not_called()


def test_check_admin(content, db, hasher) -> None:
    service = make_service(content, db, hasher)

    assert service.check_admin("gizli") is True
    assert service.check_admin("yanlis") is False


def test_is_admin_name_ignores_case_and_spaces(content, db, hasher) -> None:
    service = make_service(content, db, hasher)

    assert service.is_admin_name(" UstaOglu ") is True
    assert service.is_admin_name("ali") is False


def test_register_admin_username_rejected(content, db, hasher) -> None:
    with pytest.raises(RegistrationError, match="kullanılamaz"):
        make_service(content, db, hasher).register("Ustaoglu", "1234", "1234")
    db.create_participant.assert_not_called()


def test_history_view(content, db, hasher) -> None:
    db.list_attempts.return_value = [db.get_attempt.return_value]

    view = make_service(content, db, hasher).history_view(OWNER_ID)

    assert view.nickname == "Ali" and len(view.attempts) == 1


def test_admin_rename_normalizes_and_saves(content, db, hasher) -> None:
    db.rename_participant.return_value = True
    display, key = normalize_nickname("  Yeni İsim ")

    assert make_service(content, db, hasher).admin_rename(OWNER_ID, "  Yeni İsim ") == display
    db.rename_participant.assert_called_once_with(OWNER_ID, display, key)


@pytest.mark.parametrize("nickname", ["a", "", "x" * 31, "ad<script>"])
def test_admin_rename_rejects_invalid_nickname(content, db, hasher, nickname: str) -> None:
    with pytest.raises(RegistrationError):
        make_service(content, db, hasher).admin_rename(OWNER_ID, nickname)
    db.rename_participant.assert_not_called()


def test_admin_rename_rejects_admin_name(content, db, hasher) -> None:
    with pytest.raises(RegistrationError, match="kullanılamaz"):
        make_service(content, db, hasher).admin_rename(OWNER_ID, "Ustaoglu")
    db.rename_participant.assert_not_called()


def test_admin_rename_taken_nickname(content, db, hasher) -> None:
    db.rename_participant.side_effect = NicknameTaken("veli")

    with pytest.raises(RegistrationError, match="alınmış"):
        make_service(content, db, hasher).admin_rename(OWNER_ID, "Veli")


def test_admin_rename_unknown_participant(content, db, hasher) -> None:
    db.rename_participant.return_value = False

    with pytest.raises(LookupError):
        make_service(content, db, hasher).admin_rename(OWNER_ID, "Veli")


@pytest.mark.parametrize("found", [True, False])
def test_admin_delete_returns_db_result(content, db, hasher, found: bool) -> None:
    db.delete_participant.return_value = found

    assert make_service(content, db, hasher).admin_delete(OWNER_ID) is found
    db.delete_participant.assert_called_once_with(OWNER_ID)
