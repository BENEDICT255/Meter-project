import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from meters.models import Meter


@pytest.mark.django_db
def test_create_meter(user):
    m = Meter.objects.create(owner=user, meter_number="0123456789", label="Home")
    assert m.id is not None
    assert m.owner == user
    assert m.meter_number == "0123456789"
    assert m.label == "Home"


@pytest.mark.django_db
def test_meter_number_unique(user, other_user):
    Meter.objects.create(owner=user, meter_number="0123456789")
    with pytest.raises(IntegrityError):
        Meter.objects.create(owner=other_user, meter_number="0123456789")


@pytest.mark.django_db
def test_meter_number_must_be_digits(user):
    m = Meter(owner=user, meter_number="ABC1234567")
    with pytest.raises(ValidationError):
        m.full_clean()


@pytest.mark.django_db
def test_meter_number_length_bounds(user):
    too_short = Meter(owner=user, meter_number="123")
    with pytest.raises(ValidationError):
        too_short.full_clean()

    too_long = Meter(owner=user, meter_number="1" * 20)
    with pytest.raises(ValidationError):
        too_long.full_clean()
