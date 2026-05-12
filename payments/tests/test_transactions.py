from decimal import Decimal

import pytest
from django.utils import timezone

from payments.models import Token, Transaction


@pytest.mark.django_db
def test_list_transactions_owner_scoped(authed_client, user, meter, other_user, other_meter):
    Transaction.objects.create(
        user=user, meter=meter, amount=Decimal("5000"),
        control_number="990000000100", expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    Transaction.objects.create(
        user=other_user, meter=other_meter, amount=Decimal("5000"),
        control_number="990000000101", expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    resp = authed_client.get("/api/transactions/")
    assert resp.status_code == 200
    cns = [t["control_number"] for t in resp.json()]
    assert "990000000100" in cns
    assert "990000000101" not in cns


@pytest.mark.django_db
def test_retrieve_transaction_includes_token(authed_client, user, meter):
    txn = Transaction.objects.create(
        user=user, meter=meter, amount=Decimal("5000"),
        control_number="990000000110", expires_at=timezone.now() + timezone.timedelta(minutes=30),
        status=Transaction.Status.PAID,
    )
    Token.objects.create(transaction=txn, value="9999999", strategy="simple")
    resp = authed_client.get(f"/api/transactions/{txn.id}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "paid"
    assert body["token"]["value"] == "9999999"


@pytest.mark.django_db
def test_retrieve_other_users_transaction_404s(authed_client, other_user, other_meter):
    txn = Transaction.objects.create(
        user=other_user, meter=other_meter, amount=Decimal("5000"),
        control_number="990000000111", expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    resp = authed_client.get(f"/api/transactions/{txn.id}/")
    assert resp.status_code == 404
