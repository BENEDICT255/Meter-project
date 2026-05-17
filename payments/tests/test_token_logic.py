from decimal import Decimal

import pytest
from django.test import override_settings

from payments.token_logic import (
    HmacTokenStrategy,
    SimpleTokenStrategy,
    get_strategy,
)


# ---- SimpleTokenStrategy ----


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


# ---- HmacTokenStrategy ----


SECRET_A = b"server-secret-A"
SECRET_B = b"server-secret-B"


def test_hmac_strategy_name():
    assert HmacTokenStrategy(secret=SECRET_A).name == "hmac"


def test_hmac_strategy_requires_secret():
    with pytest.raises(ValueError):
        HmacTokenStrategy(secret=b"")


def test_hmac_strategy_rejects_bad_digits():
    with pytest.raises(ValueError):
        HmacTokenStrategy(secret=SECRET_A, digits=5)
    with pytest.raises(ValueError):
        HmacTokenStrategy(secret=SECRET_A, digits=19)


def test_hmac_strategy_output_shape():
    strat = HmacTokenStrategy(secret=SECRET_A, digits=12)
    token = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n1")
    assert len(token) == 12
    assert token.isdigit()


def test_hmac_strategy_respects_digits():
    strat = HmacTokenStrategy(secret=SECRET_A, digits=10)
    token = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n1")
    assert len(token) == 10
    assert token.isdigit()


def test_hmac_strategy_deterministic():
    strat = HmacTokenStrategy(secret=SECRET_A)
    a = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n1")
    b = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n1")
    assert a == b


def test_hmac_strategy_changing_amount_changes_token():
    strat = HmacTokenStrategy(secret=SECRET_A)
    a = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n1")
    b = strat.generate(amount=Decimal("5001"), meter_number="0100000001", nonce="n1")
    assert a != b


def test_hmac_strategy_changing_meter_changes_token():
    strat = HmacTokenStrategy(secret=SECRET_A)
    a = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n1")
    b = strat.generate(amount=Decimal("5000"), meter_number="0100000002", nonce="n1")
    assert a != b


def test_hmac_strategy_changing_nonce_changes_token():
    strat = HmacTokenStrategy(secret=SECRET_A)
    a = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n1")
    b = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n2")
    assert a != b


def test_hmac_strategy_changing_secret_changes_token():
    a = HmacTokenStrategy(secret=SECRET_A).generate(
        amount=Decimal("5000"), meter_number="0100000001", nonce="n1"
    )
    b = HmacTokenStrategy(secret=SECRET_B).generate(
        amount=Decimal("5000"), meter_number="0100000001", nonce="n1"
    )
    assert a != b


def test_hmac_strategy_resists_message_boundary_collision():
    # Without a separator, (amount=10, meter=01) and (amount=1, meter=001) would
    # produce the same concatenated message. The pipe separator must prevent this.
    strat = HmacTokenStrategy(secret=SECRET_A)
    a = strat.generate(amount=Decimal("10"), meter_number="01", nonce="n")
    b = strat.generate(amount=Decimal("1"), meter_number="001", nonce="n")
    assert a != b


# ---- get_strategy() ----


@override_settings(TOKEN_STRATEGY="simple", TOKEN_SIMPLE_MULTIPLIER=1357)
def test_get_strategy_returns_simple():
    s = get_strategy()
    assert isinstance(s, SimpleTokenStrategy)
    assert s.name == "simple"


@override_settings(
    TOKEN_STRATEGY="hmac",
    TOKEN_HMAC_SECRET="some-real-secret",
    TOKEN_HMAC_DIGITS=12,
)
def test_get_strategy_returns_hmac():
    s = get_strategy()
    assert isinstance(s, HmacTokenStrategy)
    assert s.name == "hmac"
    assert s.digits == 12


@override_settings(TOKEN_STRATEGY="hmac", TOKEN_HMAC_SECRET="", TOKEN_HMAC_DIGITS=12)
def test_get_strategy_hmac_empty_secret_raises():
    with pytest.raises(ValueError):
        get_strategy()


@override_settings(TOKEN_STRATEGY="unknown")
def test_get_strategy_unknown_raises():
    with pytest.raises(ValueError):
        get_strategy()
