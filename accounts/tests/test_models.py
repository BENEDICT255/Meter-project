import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
def test_create_user_with_phone_number():
    user = User.objects.create_user(phone_number="+255711111111", password="pw")
    assert user.phone_number == "+255711111111"
    assert user.check_password("pw")
    assert user.is_active
    assert not user.is_staff


@pytest.mark.django_db
def test_phone_number_is_unique():
    User.objects.create_user(phone_number="+255722222222", password="pw")
    with pytest.raises(IntegrityError):
        User.objects.create_user(phone_number="+255722222222", password="pw")


@pytest.mark.django_db
def test_create_superuser():
    su = User.objects.create_superuser(phone_number="+255733333333", password="pw")
    assert su.is_staff
    assert su.is_superuser


@pytest.mark.django_db
def test_user_has_no_username_field():
    user = User.objects.create_user(phone_number="+255744444444", password="pw")
    assert not hasattr(user, "username") or user.username in (None, "")
