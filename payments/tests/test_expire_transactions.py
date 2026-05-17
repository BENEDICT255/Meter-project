from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from payments.models import Transaction


def _make_txn(*, user, meter, control_number, status, expires_at):
    return Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number=control_number,
        status=status,
        expires_at=expires_at,
    )


@pytest.mark.django_db
def test_expires_only_pending_past_expiry(user, meter):
    now = timezone.now()
    past = _make_txn(
        user=user,
        meter=meter,
        control_number="EXP-1",
        status=Transaction.Status.PENDING,
        expires_at=now - timezone.timedelta(minutes=1),
    )
    future = _make_txn(
        user=user,
        meter=meter,
        control_number="EXP-2",
        status=Transaction.Status.PENDING,
        expires_at=now + timezone.timedelta(minutes=30),
    )
    paid = _make_txn(
        user=user,
        meter=meter,
        control_number="EXP-3",
        status=Transaction.Status.PAID,
        expires_at=now - timezone.timedelta(minutes=10),
    )

    out = StringIO()
    call_command("expire_transactions", stdout=out)

    past.refresh_from_db()
    future.refresh_from_db()
    paid.refresh_from_db()
    assert past.status == Transaction.Status.EXPIRED
    assert future.status == Transaction.Status.PENDING
    assert paid.status == Transaction.Status.PAID
    assert "Expired 1" in out.getvalue()


@pytest.mark.django_db
def test_rerun_is_idempotent(user, meter):
    _make_txn(
        user=user,
        meter=meter,
        control_number="EXP-IDEM",
        status=Transaction.Status.PENDING,
        expires_at=timezone.now() - timezone.timedelta(minutes=1),
    )
    call_command("expire_transactions", stdout=StringIO())
    out = StringIO()
    call_command("expire_transactions", stdout=out)
    assert "Expired 0" in out.getvalue()
