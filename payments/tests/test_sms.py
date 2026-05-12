import logging
from decimal import Decimal

import pytest
from django.test import override_settings
from django.utils import timezone

from payments.models import Token, Transaction
from payments.sms import (
    ConsoleSmsProvider,
    SmsProvider,
    SmsResult,
    _get_provider,
    send_token_sms,
)


def test_console_provider_returns_ok(caplog):
    p = ConsoleSmsProvider()
    with caplog.at_level(logging.INFO, logger="payments.sms"):
        result = p.send(to="+255700000099", message="Your token is 1234")
    assert isinstance(result, SmsResult)
    assert result.ok is True
    assert "1234" in caplog.text


@override_settings(SMS_PROVIDER="console")
def test_get_provider_returns_console():
    assert isinstance(_get_provider(), ConsoleSmsProvider)


@override_settings(SMS_PROVIDER="unknown")
def test_get_provider_unknown_raises():
    with pytest.raises(ValueError):
        _get_provider()


@pytest.mark.django_db
@override_settings(SMS_PROVIDER="console")
def test_send_token_sms_marks_delivered(user, meter):
    txn = Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000099001",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    token = Token.objects.create(transaction=txn, value="1234567", strategy="simple")
    send_token_sms(token)
    token.refresh_from_db()
    assert token.delivered_via_sms is True
    assert token.delivered_at is not None


class FailingProvider(SmsProvider):
    name = "failing"

    def send(self, *, to, message):
        return SmsResult(ok=False, error="boom")


@pytest.mark.django_db
def test_send_token_sms_does_not_mark_delivered_on_failure(user, meter, monkeypatch):
    txn = Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000099002",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    token = Token.objects.create(transaction=txn, value="1234567", strategy="simple")

    import payments.sms as sms_mod

    monkeypatch.setattr(sms_mod, "_get_provider", lambda: FailingProvider())
    send_token_sms(token)
    token.refresh_from_db()
    assert token.delivered_via_sms is False
    assert token.delivered_at is None
