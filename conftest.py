import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


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
