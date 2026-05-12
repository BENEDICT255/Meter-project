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


def get_strategy() -> TokenStrategy:
    name = settings.TOKEN_STRATEGY
    if name == "simple":
        return SimpleTokenStrategy(multiplier=settings.TOKEN_SIMPLE_MULTIPLIER)
    # Task 3 will register HmacTokenStrategy here.
    raise ValueError(f"unknown TOKEN_STRATEGY: {name!r}")
