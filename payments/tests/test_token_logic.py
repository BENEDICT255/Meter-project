from decimal import Decimal

import pytest
from django.test import override_settings

from payments.token_logic import SimpleTokenStrategy, get_strategy


def test_simple_strategy_formula():
    strat = SimpleTokenStrategy(multiplier=1357)
    value = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="ignored")
    assert value == str(5000 * 1357 + 100000001)


def test_simple_strategy_deterministic():
    strat = SimpleTokenStrategy(multiplier=1357)
    a = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n1")
    b = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n2")
    assert a == b


def test_simple_strategy_differs_by_inputs():
    strat = SimpleTokenStrategy(multiplier=1357)
    base = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n")
    other_amount = strat.generate(amount=Decimal("6000"), meter_number="0100000001", nonce="n")
    other_meter = strat.generate(amount=Decimal("5000"), meter_number="0100000002", nonce="n")
    assert base != other_amount
    assert base != other_meter


def test_simple_strategy_name():
    assert SimpleTokenStrategy(multiplier=1357).name == "simple"


@override_settings(TOKEN_STRATEGY="simple", TOKEN_SIMPLE_MULTIPLIER=1357)
def test_get_strategy_returns_simple():
    s = get_strategy()
    assert isinstance(s, SimpleTokenStrategy)
    assert s.name == "simple"


@override_settings(TOKEN_STRATEGY="unknown")
def test_get_strategy_unknown_raises():
    with pytest.raises(ValueError):
        get_strategy()
