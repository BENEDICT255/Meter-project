import hashlib
import hmac
from abc import ABC, abstractmethod
from decimal import Decimal

from django.conf import settings


class TokenStrategy(ABC):
    name: str

    @abstractmethod
    def generate(self, *, amount: Decimal, meter_number: str, nonce: str) -> str:
        ...


class SimpleTokenStrategy(TokenStrategy):
    name = "simple"

    def __init__(self, *, multiplier: int):
        self.multiplier = multiplier

    def generate(self, *, amount: Decimal, meter_number: str, nonce: str) -> str:
        # Brief formula: (amount × 1357) + meter_id.
        # nonce is accepted for interface uniformity (HmacTokenStrategy will use it).
        return str(int(amount) * self.multiplier + int(meter_number))


class HmacTokenStrategy(TokenStrategy):
    name = "hmac"

    def __init__(self, *, secret: bytes, digits: int = 12):
        if not secret:
            raise ValueError("HmacTokenStrategy requires a non-empty secret")
        if not 6 <= digits <= 18:
            raise ValueError(f"digits must be in [6, 18], got {digits}")
        self.secret = secret
        self.digits = digits

    def generate(self, *, amount: Decimal, meter_number: str, nonce: str) -> str:
        # Canonical message: pipe-separated to avoid ambiguity between
        # (amount=10, meter=01) and (amount=1, meter=001).
        message = f"{amount}|{meter_number}|{nonce}".encode()
        digest = hmac.new(self.secret, message, hashlib.sha256).digest()
        # HOTP-style dynamic truncation (RFC 4226 §5.3).
        offset = digest[-1] & 0x0F
        truncated = (
            ((digest[offset] & 0x7F) << 24)
            | (digest[offset + 1] << 16)
            | (digest[offset + 2] << 8)
            | digest[offset + 3]
        )
        code = truncated % (10**self.digits)
        return str(code).zfill(self.digits)


def get_strategy() -> TokenStrategy:
    name = settings.TOKEN_STRATEGY
    if name == "simple":
        return SimpleTokenStrategy(multiplier=settings.TOKEN_SIMPLE_MULTIPLIER)
    if name == "hmac":
        return HmacTokenStrategy(
            secret=settings.TOKEN_HMAC_SECRET.encode(),
            digits=settings.TOKEN_HMAC_DIGITS,
        )
    raise ValueError(f"unknown TOKEN_STRATEGY: {name!r}")
