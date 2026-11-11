import hashlib
import hmac
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final

NICKNAME_MIN: Final[int] = 2
NICKNAME_MAX: Final[int] = 30
# \w Unicode harfleri (Türkçe dahil), rakamları ve alt çizgiyi kapsar.
NICKNAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"[\w .\-]+")
# PIN: yalnızca İngilizce harf ve rakam, tam 4 karakter.
PIN_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9]{4}")

SCRYPT_N: Final[int] = 2**14
SCRYPT_R: Final[int] = 8
SCRYPT_P: Final[int] = 1
SCRYPT_DKLEN: Final[int] = 32
SALT_BYTES: Final[int] = 16


def normalize_nickname(raw: str) -> tuple[str, str]:
    """Takma adı gösterim biçimine ve benzersizlik anahtarına çevirir."""
    display = " ".join(unicodedata.normalize("NFC", raw).split())
    if not NICKNAME_MIN <= len(display) <= NICKNAME_MAX:
        raise ValueError(f"Takma ad {NICKNAME_MIN}-{NICKNAME_MAX} karakter olmalı.")
    if not NICKNAME_PATTERN.fullmatch(display):
        raise ValueError("Takma adda yalnızca harf, rakam, boşluk, nokta, tire ve alt çizgi kullanılabilir.")
    # str.lower() Türkçe I/İ harflerini yanlış küçültür ("İ" -> "i̇"); önce elle eşlenir.
    key = display.replace("I", "ı").replace("İ", "i").lower()
    return display, key


def validate_pin(pin: str) -> None:
    if not PIN_PATTERN.fullmatch(pin):
        raise ValueError("PIN tam 4 karakter olmalı; yalnızca İngilizce harf ve rakam kullanılabilir.")


class PinHasher:
    """PIN'i tuzlanmış scrypt özeti olarak saklamak ve doğrulamak için."""

    def hash(self, pin: str) -> tuple[bytes, bytes]:
        salt = os.urandom(SALT_BYTES)
        return self._derive(pin, salt), salt

    def verify(self, pin: str, digest: bytes, salt: bytes) -> bool:
        return hmac.compare_digest(self._derive(pin, salt), digest)

    @staticmethod
    def _derive(pin: str, salt: bytes) -> bytes:
        return hashlib.scrypt(
            pin.encode("utf-8"),
            salt=salt,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            dklen=SCRYPT_DKLEN,
        )


@dataclass(frozen=True)
class LockoutPolicy:
    max_failures: int = 5
    lock_minutes: int = 15

    def is_locked(self, locked_until: datetime | None, now: datetime) -> bool:
        return locked_until is not None and now < locked_until

    def after_failure(self, failed: int, now: datetime) -> tuple[int, datetime | None]:
        failed += 1
        if failed >= self.max_failures:
            return 0, now + timedelta(minutes=self.lock_minutes)
        return failed, None
