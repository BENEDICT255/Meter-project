import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_register_creates_user(api_client):
    resp = api_client.post(
        "/api/auth/register/",
        {"phone_number": "+255700000099", "password": "pw-strong-99"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["phone_number"] == "+255700000099"
    assert "password" not in body
    assert User.objects.filter(phone_number="+255700000099").exists()


@pytest.mark.django_db
def test_register_rejects_duplicate_phone(api_client, user):
    resp = api_client.post(
        "/api/auth/register/",
        {"phone_number": user.phone_number, "password": "pw-strong"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_register_requires_phone_and_password(api_client):
    resp = api_client.post("/api/auth/register/", {}, format="json")
    assert resp.status_code == 400
    errors = resp.json()
    assert "phone_number" in errors
    assert "password" in errors
