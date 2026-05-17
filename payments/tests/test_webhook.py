import json
from decimal import Decimal

import pytest
from django.test import override_settings
from django.utils import timezone

from payments.models import Token, Transaction


ORDER_ID = "order-id-abc-123"


def _post_webhook(api_client, body: dict):
    return api_client.post(
        "/api/webhooks/payment/",
        data=json.dumps(body),
        content_type="application/json",
    )


@pytest.fixture
def pending_txn(db, user, meter):
    return Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="SLC-REF-001",
        provider_reference=ORDER_ID,
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )


@pytest.mark.django_db
def test_unknown_order_id_returns_404(api_client):
    resp = _post_webhook(
        api_client,
        {"transaction_details": {"order_id": "does-not-exist"}},
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_missing_order_id_returns_400(api_client):
    resp = _post_webhook(api_client, {"transaction_details": {}})
    assert resp.status_code == 400


@override_settings(TOKEN_STRATEGY="simple", TOKEN_SIMPLE_MULTIPLIER=1357, SMS_PROVIDER="console")
@pytest.mark.django_db
def test_callback_marks_paid_and_issues_token(api_client, pending_txn):
    resp = _post_webhook(
        api_client,
        {"transaction_details": {"order_id": ORDER_ID}},
    )
    assert resp.status_code == 200, resp.content
    pending_txn.refresh_from_db()
    assert pending_txn.status == "paid"
    assert pending_txn.paid_at is not None
    token = Token.objects.get(transaction=pending_txn)
    expected_value = str(5000 * 1357 + int(pending_txn.meter.meter_number))
    assert token.value == expected_value
    body = resp.json()
    assert body["token"]["value"] == expected_value


@override_settings(TOKEN_STRATEGY="simple", TOKEN_SIMPLE_MULTIPLIER=1357, SMS_PROVIDER="console")
@pytest.mark.django_db
def test_replay_is_idempotent(api_client, pending_txn):
    payload = {"transaction_details": {"order_id": ORDER_ID}}
    first = _post_webhook(api_client, payload)
    second = _post_webhook(api_client, payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["token"]["value"] == second.json()["token"]["value"]
    assert Token.objects.filter(transaction=pending_txn).count() == 1
