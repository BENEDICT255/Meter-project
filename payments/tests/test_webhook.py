import json
from decimal import Decimal

import pytest
from django.test import override_settings
from django.utils import timezone

from payments.models import Token, Transaction
from payments.signing import compute_hmac


SECRET = b"webhook-test-secret"


def _post_webhook(api_client, body: dict, secret: bytes = SECRET, tamper: bool = False):
    raw = json.dumps(body).encode()
    sig = compute_hmac(raw, secret)
    if tamper:
        sig = "sha256=" + "0" * 64
    return api_client.post(
        "/api/webhooks/payment/",
        data=raw,
        content_type="application/json",
        HTTP_X_SIGNATURE=sig,
    )


@pytest.fixture
def pending_txn(db, user, meter):
    return Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000000010",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )


@override_settings(WEBHOOK_HMAC_SECRET=SECRET.decode())
@pytest.mark.django_db
def test_invalid_signature_returns_401(api_client, pending_txn):
    resp = _post_webhook(
        api_client,
        {
            "control_number": pending_txn.control_number,
            "amount": "5000",
            "provider_reference": "pp-1",
            "status": "paid",
        },
        tamper=True,
    )
    assert resp.status_code == 401
    pending_txn.refresh_from_db()
    assert pending_txn.status == "pending"
    assert not Token.objects.filter(transaction=pending_txn).exists()


@override_settings(WEBHOOK_HMAC_SECRET=SECRET.decode())
@pytest.mark.django_db
def test_unknown_control_number_returns_404(api_client):
    resp = _post_webhook(
        api_client,
        {
            "control_number": "999999999999",
            "amount": "5000",
            "provider_reference": "pp-2",
            "status": "paid",
        },
    )
    assert resp.status_code == 404


@override_settings(
    WEBHOOK_HMAC_SECRET=SECRET.decode(),
    TOKEN_STRATEGY="simple",
    TOKEN_SIMPLE_MULTIPLIER=1357,
    SMS_PROVIDER="console",
)
@pytest.mark.django_db
def test_paid_payload_creates_token(api_client, pending_txn):
    resp = _post_webhook(
        api_client,
        {
            "control_number": pending_txn.control_number,
            "amount": "5000",
            "provider_reference": "pp-3",
            "status": "paid",
        },
    )
    assert resp.status_code == 200, resp.content
    pending_txn.refresh_from_db()
    assert pending_txn.status == "paid"
    assert pending_txn.paid_at is not None
    assert pending_txn.provider_reference == "pp-3"
    token = Token.objects.get(transaction=pending_txn)
    expected_value = str(5000 * 1357 + int(pending_txn.meter.meter_number))
    assert token.value == expected_value
    body = resp.json()
    assert body["token"]["value"] == expected_value


@override_settings(
    WEBHOOK_HMAC_SECRET=SECRET.decode(),
    TOKEN_STRATEGY="simple",
    TOKEN_SIMPLE_MULTIPLIER=1357,
    SMS_PROVIDER="console",
)
@pytest.mark.django_db
def test_replay_is_idempotent(api_client, pending_txn):
    payload = {
        "control_number": pending_txn.control_number,
        "amount": "5000",
        "provider_reference": "pp-4",
        "status": "paid",
    }
    first = _post_webhook(api_client, payload)
    second = _post_webhook(api_client, payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["token"]["value"] == second.json()["token"]["value"]
    assert Token.objects.filter(transaction=pending_txn).count() == 1


@override_settings(WEBHOOK_HMAC_SECRET=SECRET.decode())
@pytest.mark.django_db
def test_failed_payload_marks_failed(api_client, pending_txn):
    resp = _post_webhook(
        api_client,
        {
            "control_number": pending_txn.control_number,
            "amount": "5000",
            "provider_reference": "pp-5",
            "status": "failed",
        },
    )
    assert resp.status_code == 200
    pending_txn.refresh_from_db()
    assert pending_txn.status == "failed"
    assert not Token.objects.filter(transaction=pending_txn).exists()


@override_settings(WEBHOOK_HMAC_SECRET=SECRET.decode())
@pytest.mark.django_db
def test_unknown_status_returns_400(api_client, pending_txn):
    resp = _post_webhook(
        api_client,
        {
            "control_number": pending_txn.control_number,
            "amount": "5000",
            "provider_reference": "pp-6",
            "status": "processing",
        },
    )
    assert resp.status_code == 400
    pending_txn.refresh_from_db()
    assert pending_txn.status == "pending"
    assert not Token.objects.filter(transaction=pending_txn).exists()
