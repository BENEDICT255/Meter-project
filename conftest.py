import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from meters.models import Meter

User = get_user_model()


@pytest.fixture(autouse=True)
def _never_send_real_sms(settings):
    # Safety net: no test should ever hit the live MalipoPay gateway, whatever
    # SMS_PROVIDER the local .env sets. Tests that exercise the real provider
    # build MalipoPaySmsProvider directly and are unaffected by this.
    settings.SMS_PROVIDER = "console"


@pytest.fixture
def user(db):
    return User.objects.create_user(phone_number="+255700000001", password="pw-strong-1")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(phone_number="+255700000002", password="pw-strong-2")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authed_client(user):
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def other_authed_client(other_user):
    client = APIClient()
    token = str(RefreshToken.for_user(other_user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def meter(user):
    return Meter.objects.create(owner=user, meter_number="0100000001", label="Home")


@pytest.fixture
def other_meter(other_user):
    return Meter.objects.create(owner=other_user, meter_number="0200000001", label="Other Home")
