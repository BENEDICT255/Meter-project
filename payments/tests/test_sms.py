import logging
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.test import override_settings
from django.utils import timezone

from payments.models import Token, Transaction
from payments.sms import (
    ConsoleSmsProvider,
    MalipoPaySmsProvider,
    SmsProvider,
    SmsResult,
    _get_provider,
    _normalize_msisdn,
    send_token_sms,
)


# ---- ConsoleSmsProvider ----


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


# ---- _normalize_msisdn ----


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("+255700000001", "255700000001"),
        ("255700000001", "255700000001"),
        ("0700000001", "255700000001"),
        (" +255700000001 ", "255700000001"),
    ],
)
def test_normalize_msisdn(raw, expected):
    assert _normalize_msisdn(raw) == expected


# ---- MalipoPaySmsProvider ----


def _provider():
    return MalipoPaySmsProvider(
        api_url="https://example.test/sms",
        api_token="test-token",
        sender="Daraja",
        operator_id="op-123",
    )


def test_malipopay_requires_token():
    with pytest.raises(ValueError):
        MalipoPaySmsProvider(api_url="x", api_token="", sender="s", operator_id="o")


def test_malipopay_requires_operator_id():
    with pytest.raises(ValueError):
        MalipoPaySmsProvider(api_url="x", api_token="t", sender="s", operator_id="")


def test_malipopay_send_success_first_attempt():
    mock_response = MagicMock(status_code=200, text='{"ok":true}')
    with patch("payments.sms.requests.post", return_value=mock_response) as post, patch(
        "payments.sms.time.sleep"
    ) as sleep:
        result = _provider().send(to="+255700000001", message="hello")

    assert result.ok is True
    assert post.call_count == 1
    assert sleep.call_count == 0

    call = post.call_args
    assert call.args[0] == "https://example.test/sms"
    assert call.kwargs["headers"]["apiToken"] == "test-token"
    body = call.kwargs["json"]
    assert body["phoneNumber"] == "255700000001"
    assert body["phone_number"] == "255700000001"
    assert body["sender"] == "Daraja"
    assert body["operator_id"] == "op-123"
    assert body["message"] == "hello"


def test_malipopay_retries_on_failure_then_succeeds():
    responses = [
        MagicMock(status_code=502, text="bad gateway"),
        MagicMock(status_code=500, text="server error"),
        MagicMock(status_code=200, text='{"ok":true}'),
    ]
    with patch("payments.sms.requests.post", side_effect=responses) as post, patch(
        "payments.sms.time.sleep"
    ) as sleep:
        result = _provider().send(to="+255700000001", message="hello")

    assert result.ok is True
    assert post.call_count == 3
    assert sleep.call_count == 2  # slept between attempts 1→2 and 2→3, not after the last


def test_malipopay_returns_failure_after_all_retries_exhausted():
    with patch(
        "payments.sms.requests.post",
        return_value=MagicMock(status_code=500, text="boom"),
    ) as post, patch("payments.sms.time.sleep") as sleep:
        result = _provider().send(to="+255700000001", message="hello")

    assert result.ok is False
    assert "500" in (result.error or "")
    assert post.call_count == 3
    assert sleep.call_count == 2


def test_malipopay_handles_network_exception_per_attempt():
    with patch(
        "payments.sms.requests.post",
        side_effect=requests.ConnectionError("dns fail"),
    ) as post, patch("payments.sms.time.sleep"):
        result = _provider().send(to="+255700000001", message="hello")

    assert result.ok is False
    assert "network error" in (result.error or "")
    assert post.call_count == 3


@override_settings(
    SMS_PROVIDER="malipopay",
    MALIPOPAY_API_URL="https://example.test/sms",
    MALIPOPAY_API_TOKEN="tok",
    MALIPOPAY_SENDER="Daraja",
    MALIPOPAY_OPERATOR_ID="op-123",
)
def test_get_provider_returns_malipopay():
    p = _get_provider()
    assert isinstance(p, MalipoPaySmsProvider)
    assert p.api_token == "tok"
    assert p.operator_id == "op-123"


# ---- send_token_sms ----


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


@pytest.mark.django_db
@override_settings(
    SMS_PROVIDER="malipopay",
    MALIPOPAY_API_URL="https://example.test/sms",
    MALIPOPAY_API_TOKEN="tok",
    MALIPOPAY_SENDER="Daraja",
    MALIPOPAY_OPERATOR_ID="op-123",
)
def test_send_token_sms_end_to_end_with_malipopay(user, meter):
    txn = Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000099003",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    token = Token.objects.create(transaction=txn, value="1234567", strategy="simple")

    with patch(
        "payments.sms.requests.post",
        return_value=MagicMock(status_code=200, text='{"ok":true}'),
    ) as post:
        send_token_sms(token)

    token.refresh_from_db()
    assert token.delivered_via_sms is True
    assert post.call_count == 1
