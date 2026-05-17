import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    # DRF stores throttle hits in the cache; isolate tests from each other.
    cache.clear()
    yield
    cache.clear()


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
def test_logout_requires_refresh(authed_client):
    resp = authed_client.post("/api/auth/logout/", {}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_logout_rejects_invalid_refresh(authed_client):
    resp = authed_client.post("/api/auth/logout/", {"refresh": "garbage"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_logout_blacklists_refresh_so_refresh_fails(api_client, user):
    login = api_client.post(
        "/api/auth/login/",
        {"phone_number": user.phone_number, "password": "pw-strong-1"},
        format="json",
    )
    tokens = login.json()
    access, refresh = tokens["access"], tokens["refresh"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    resp = api_client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
    assert resp.status_code == 205

    # The same refresh token should no longer be usable.
    api_client.credentials()  # drop bearer
    refresh_resp = api_client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
    assert refresh_resp.status_code == 401


# ---- throttling ----


@pytest.mark.django_db
def test_login_is_rate_limited(api_client, user):
    # Default rate is 5/min; the 6th attempt within the window must be 429.
    payload = {"phone_number": user.phone_number, "password": "wrong"}
    statuses = [
        api_client.post("/api/auth/login/", payload, format="json").status_code
        for _ in range(6)
    ]
    assert statuses[-1] == 429
    assert statuses.count(429) >= 1
