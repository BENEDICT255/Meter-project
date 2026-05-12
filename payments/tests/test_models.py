from decimal import Decimal

import pytest
from django.utils import timezone

from payments.models import Token, Transaction


@pytest.mark.django_db
def test_create_pending_transaction(user, meter):
    txn = Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000000001",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    assert txn.id is not None
    assert txn.status == Transaction.Status.PENDING
    assert txn.paid_at is None


@pytest.mark.django_db
def test_control_number_unique(user, meter):
    Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000000002",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    from django.db import IntegrityError

    with pytest.raises(IntegrityError):
        Transaction.objects.create(
            user=user,
            meter=meter,
            amount=Decimal("5000"),
            control_number="990000000002",
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
        )


@pytest.mark.django_db
def test_one_token_per_transaction(user, meter):
    txn = Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000000003",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    Token.objects.create(transaction=txn, value="123456789", strategy="simple")
    from django.db import IntegrityError

    with pytest.raises(IntegrityError):
        Token.objects.create(transaction=txn, value="987654321", strategy="simple")
