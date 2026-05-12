import re
from decimal import Decimal

import pytest

from payments.models import Transaction


@pytest.mark.django_db
def test_initiate_creates_pending_transaction(authed_client, meter, user):
    resp = authed_client.post(
        "/api/transactions/initiate/",
        {"meter_id": str(meter.id), "amount": "5000"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert re.fullmatch(r"99\d{10}", body["control_number"])
    assert body["status"] == "pending"
    assert body["amount"] == "5000.00"
    assert "expires_at" in body

    txn = Transaction.objects.get(id=body["id"])
    assert txn.user == user
    assert txn.meter == meter
    assert txn.amount == Decimal("5000.00")


@pytest.mark.django_db
def test_initiate_rejects_other_users_meter(authed_client, other_meter):
    resp = authed_client.post(
        "/api/transactions/initiate/",
        {"meter_id": str(other_meter.id), "amount": "5000"},
        format="json",
    )
    assert resp.status_code in (400, 404)


@pytest.mark.django_db
def test_initiate_rejects_nonpositive_amount(authed_client, meter):
    resp = authed_client.post(
        "/api/transactions/initiate/",
        {"meter_id": str(meter.id), "amount": "0"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_initiate_requires_auth(api_client, meter):
    resp = api_client.post(
        "/api/transactions/initiate/",
        {"meter_id": str(meter.id), "amount": "5000"},
        format="json",
    )
    assert resp.status_code == 401
