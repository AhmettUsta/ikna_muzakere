from datetime import datetime, timedelta, timezone

import pytest

from security import LockoutPolicy, PinHasher, normalize_nickname, validate_pin

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


def test_normalize_nickname_same_key() -> None:
    keys = {normalize_nickname(raw)[1] for raw in ["Ali", " ali ", "ALİ", "ali"]}

    assert keys == {"ali"}
    assert normalize_nickname("Işık") == ("Işık", "ışık")
    assert normalize_nickname("  Ayşe   Nur ") == ("Ayşe Nur", "ayşe nur")


@pytest.mark.parametrize("raw", ["", "   ", "a", "x" * 31, "ali<script>", "ali@mail"])
def test_normalize_nickname_rejects(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_nickname(raw)


@pytest.mark.parametrize(
    "pin", ["123", "12345", "", " 123", "ab c", "çiğö", "ab1ş", "abc\n", "aB3$", "!@#%", "ab-1"]
)
def test_validate_pin_rejects(pin: str) -> None:
    with pytest.raises(ValueError):
        validate_pin(pin)


@pytest.mark.parametrize("pin", ["0042", "zzzz", "A1b2", "QWER"])
def test_validate_pin_accepts_four_english_letters_or_digits(pin: str) -> None:
    validate_pin(pin)


def test_pin_hash_verify() -> None:
    hasher = PinHasher()

    digest, salt = hasher.hash("1234")
    other_digest, other_salt = hasher.hash("1234")

    assert hasher.verify("1234", digest, salt) is True
    assert hasher.verify("4321", digest, salt) is False
    assert salt != other_salt
    assert digest != other_digest


def test_lockout_after_five_failures() -> None:
    policy = LockoutPolicy()

    failed, locked_until = 0, None
    for _ in range(4):
        failed, locked_until = policy.after_failure(failed, NOW)
        assert locked_until is None
    failed, locked_until = policy.after_failure(failed, NOW)

    assert failed == 0
    assert locked_until == NOW + timedelta(minutes=15)
    assert policy.is_locked(locked_until, NOW + timedelta(minutes=14)) is True


def test_lock_expires() -> None:
    policy = LockoutPolicy()
    locked_until = NOW + timedelta(minutes=15)

    assert policy.is_locked(locked_until, NOW + timedelta(minutes=15)) is False
    assert policy.is_locked(None, NOW) is False
