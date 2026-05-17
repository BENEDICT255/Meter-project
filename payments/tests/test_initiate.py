import json
from decimal import Decimal
from unittest.mock import patch

import pytest

from payments.models import Transaction
from payments.providers.swahilies import SwahiliesError, SwahiliesResponse


def _ok_response(reference="SLC-REF-001"):
    return SwahiliesResponse(reference=reference)


@pytest.mark.django_db
def test_initiate_creates_pending_transaction(authed_client, meter, user):
    with patch(
        "payments.views.initiate_push",
        return_value=_ok_response("SLC-REF-ABC"),
    ) as push:
        resp = authed_client.post(
            "/api/transactions/initiate/",
            {
                "meter_id": str(meter.id),
                "amount": "5000",
                "phone_number": "+255700000777",
            },
            format="json",
        )

    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["control_number"] == "SLC-REF-ABC"
    assert body["status"] == "pending"
    assert body["amount"] == "5000.00"
    assert "expires_at" in body

    push.assert_called_once()
    kwargs = push.call_args.kwargs
    assert kwargs["amount"] == Decimal("5000.00")
    assert kwargs["phone_number"] == "+255700000777"
    assert len(kwargs["order_id"]) == 32  # uuid4 hex

    txn = Transaction.objects.get(id=body["id"])
    assert txn.user == user
    assert txn.meter == meter
    assert txn.amount == Decimal("5000.00")
    assert txn.control_number == "SLC-REF-ABC"
    assert txn.provider_reference == kwargs["order_id"]


@pytest.mark.django_db
def test_initiate_marks_failed_and_returns_502_on_provider_error(authed_client, meter):
    with patch(
        "payments.views.initiate_push",
        side_effect=SwahiliesError("provider down"),
    ):
        resp = authed_client.post(
            "/api/transactions/initiate/",
            {
                "meter_id": str(meter.id),
                "amount": "5000",
                "phone_number": "+255700000777",
            },
            format="json",
        )

    assert resp.status_code == 502, resp.content
    body = json.loads(resp.content)
    assert "payment provider unavailable" in body["detail"]
    # Transaction row exists but is marked failed and has no control_number yet.
    txn = Transaction.objects.get(user__phone_number=meter.owner.phone_number)
    assert txn.status == "failed"
    assert not txn.control_number


@pytest.mark.django_db
def test_initiate_requires_phone_number(authed_client, meter):
    resp = authed_client.post(
        "/api/transactions/initiate/",
        {"meter_id": str(meter.id), "amount": "5000"},
        format="json",
    )
    assert resp.status_code == 400
    assert "phone_number" in resp.json()


@pytest.mark.django_db
def test_initiate_rejects_other_users_meter(authed_client, other_meter):
    resp = authed_client.post(
        "/api/transactions/initiate/",
        {
            "meter_id": str(other_meter.id),
            "amount": "5000",
            "phone_number": "+255700000777",
        },
        format="json",
    )
    assert resp.status_code in (400, 404)


@pytest.mark.django_db
def test_initiate_rejects_nonpositive_amount(authed_client, meter):
    resp = authed_client.post(
        "/api/transactions/initiate/",
        {
            "meter_id": str(meter.id),
            "amount": "0",
            "phone_number": "+255700000777",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_initiate_requires_auth(api_client, meter):
    resp = api_client.post(
        "/api/transactions/initiate/",
        {
            "meter_id": str(meter.id),
            "amount": "5000",
            "phone_number": "+255700000777",
        },
        format="json",
    )
    assert resp.status_code == 401
