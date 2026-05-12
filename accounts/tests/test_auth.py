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


@pytest.mark.django_db
def test_login_returns_jwt_pair(api_client, user):
    resp = api_client.post(
        "/api/auth/login/",
        {"phone_number": user.phone_number, "password": "pw-strong-1"},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert "access" in body
    assert "refresh" in body


@pytest.mark.django_db
def test_login_wrong_password_rejected(api_client, user):
    resp = api_client.post(
        "/api/auth/login/",
        {"phone_number": user.phone_number, "password": "wrong"},
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_refresh_returns_new_access(api_client, user):
    login = api_client.post(
        "/api/auth/login/",
        {"phone_number": user.phone_number, "password": "pw-strong-1"},
        format="json",
    )
    refresh = login.json()["refresh"]
    resp = api_client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
    assert resp.status_code == 200
    assert "access" in resp.json()


@pytest.mark.django_db
def test_me_requires_auth(api_client):
    resp = api_client.get("/api/auth/me/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_me_returns_self(authed_client, user):
    resp = authed_client.get("/api/auth/me/")
    assert resp.status_code == 200
    assert resp.json()["phone_number"] == user.phone_number


@pytest.mark.django_db
def test_logout_stub_returns_205(authed_client):
    resp = authed_client.post("/api/auth/logout/", {"refresh": "anything"}, format="json")
    assert resp.status_code == 205
