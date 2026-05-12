# Daraja Water Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the v1 "walking skeleton" of Daraja Water — a Django + DRF + MySQL JSON API that supports register → add meter → initiate transaction → HMAC-verified webhook → token generation → SMS attempt, with architectural slots ready for tasks 2–5.

**Architecture:** A single Django project (`config`) with three apps: `accounts` (custom User keyed on phone_number + JWT auth), `meters` (owner-scoped CRUD), `payments` (Transaction/Token models, control number generator, HMAC signing, TokenStrategy + SmsProvider seams, webhook view). Public endpoints: register/login/refresh, webhook. Everything else JWT-protected. MySQL via mysqlclient; no Redis, no Channels, no frontend.

**Tech Stack:** Python 3.12, Django 5, DRF, djangorestframework-simplejwt, mysqlclient, python-dotenv, pytest, pytest-django, uv for env management.

---

## File Structure

**Project root:**
- `pyproject.toml` — uv-managed deps, pytest config
- `.env.example` — every config knob (copied to `.env` by developer)
- `.gitignore` — already exists, extend if needed
- `README.md` — setup steps + curl sanity-check snippet
- `conftest.py` — repo-root pytest fixtures (`user`, `api_client`, `authed_client`, `meter`)
- `manage.py` — Django entrypoint

**`config/`** (the Django project):
- `__init__.py`, `settings.py`, `urls.py`, `wsgi.py`

**`accounts/`:**
- `models.py` — `User(AbstractUser)` keyed on `phone_number`
- `serializers.py` — `RegisterSerializer`, `UserSerializer`
- `views.py` — `RegisterView`, `MeView`, `LogoutView` (stub)
- `urls.py` — wires SimpleJWT's login/refresh + the above
- `admin.py`
- `tests/test_auth.py`

**`meters/`:**
- `models.py` — `Meter` with `meter_number` (digits-only validator)
- `serializers.py` — `MeterSerializer`
- `views.py` — `MeterViewSet` (owner-scoped)
- `urls.py`
- `admin.py`
- `tests/test_meters.py`

**`payments/`:**
- `models.py` — `Transaction`, `Token`
- `serializers.py` — `TransactionSerializer`, `TokenSerializer`, `InitiateSerializer`
- `control_numbers.py` — `generate_control_number()` (12-digit `"99"` prefix, collision retry)
- `signing.py` — `verify_hmac(body, header, secret)`
- `token_logic.py` — `TokenStrategy` ABC, `SimpleTokenStrategy`, `get_strategy()`
- `sms.py` — `SmsResult`, `SmsProvider` ABC, `ConsoleSmsProvider`, `_get_provider()`, `send_token_sms()`
- `views.py` — `InitiatePaymentView`, `TransactionViewSet`, `PaymentWebhookView`
- `urls.py`
- `admin.py`
- `tests/test_control_numbers.py`, `tests/test_signing.py`, `tests/test_token_logic.py`, `tests/test_sms.py`, `tests/test_initiate.py`, `tests/test_webhook.py`

---

## Prerequisites

The implementer needs MySQL running locally with a `daraja` database and a user that can create/drop tables (so pytest-django can manage the test DB).

**Install on macOS:**
```bash
brew install mysql
brew services start mysql
mysql -uroot -e "CREATE DATABASE daraja; CREATE DATABASE test_daraja; CREATE USER 'daraja'@'localhost' IDENTIFIED BY 'daraja'; GRANT ALL PRIVILEGES ON daraja.* TO 'daraja'@'localhost'; GRANT ALL PRIVILEGES ON test_daraja.* TO 'daraja'@'localhost'; FLUSH PRIVILEGES;"
```

`mysqlclient` needs the MySQL client lib headers: `brew install pkg-config mysql-client` and `export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"` before `uv sync`.

**Install uv (if not already):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Task 1: Project bootstrap

Boot a Django project that runs `manage.py check` cleanly against MySQL. No apps, no models, no endpoints — just proof the wiring works.

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.env` (developer step, gitignored)
- Create: `manage.py`
- Create: `config/__init__.py`
- Create: `config/settings.py`
- Create: `config/urls.py`
- Create: `config/wsgi.py`
- Modify: `.gitignore` (add `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.venv/`)

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "mnyama"
version = "0.1.0"
description = "Daraja Water — prepaid water meter top-up platform"
requires-python = ">=3.12"
dependencies = [
    "django>=5.0,<5.2",
    "djangorestframework>=3.15",
    "djangorestframework-simplejwt>=5.3",
    "mysqlclient>=2.2",
    "python-dotenv>=1.0",
    "requests>=2.31",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-django>=4.8",
]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py"]
addopts = "-ra --strict-markers"
```

- [ ] **Step 2: Write `.env.example`**

```
SECRET_KEY=change-me-in-real-deploys
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=daraja
DB_USER=daraja
DB_PASSWORD=daraja
DB_HOST=127.0.0.1
DB_PORT=3306

WEBHOOK_HMAC_SECRET=dev-webhook-secret-change-me

TOKEN_STRATEGY=simple
TOKEN_SIMPLE_MULTIPLIER=1357
TOKEN_HMAC_SECRET=dev-token-secret-change-me

SMS_PROVIDER=console
TRANSACTION_TTL_MINUTES=30
```

Then copy locally: `cp .env.example .env`.

- [ ] **Step 3: Write `manage.py`**

```python
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Write `config/__init__.py`**

Empty file.

- [ ] **Step 5: Write `config/settings.py`**

```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ["DB_PORT"],
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Dar_es_Salaam"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# Daraja config
WEBHOOK_HMAC_SECRET = os.environ["WEBHOOK_HMAC_SECRET"]
TOKEN_STRATEGY = os.environ.get("TOKEN_STRATEGY", "simple")
TOKEN_SIMPLE_MULTIPLIER = int(os.environ.get("TOKEN_SIMPLE_MULTIPLIER", "1357"))
TOKEN_HMAC_SECRET = os.environ.get("TOKEN_HMAC_SECRET", "")
SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "console")
TRANSACTION_TTL_MINUTES = int(os.environ.get("TRANSACTION_TTL_MINUTES", "30"))
```

- [ ] **Step 6: Write `config/urls.py`**

```python
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
```

- [ ] **Step 7: Write `config/wsgi.py`**

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
```

- [ ] **Step 8: Extend `.gitignore`**

Append to existing `.gitignore`:

```
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

(Some entries may already exist from the design commit — keep deduplicated.)

- [ ] **Step 9: Sync deps and verify Django boots**

```bash
uv sync
uv run python manage.py check
```

Expected output: `System check identified no issues (0 silenced).`

- [ ] **Step 10: Run pytest with no tests (sanity check the harness)**

```bash
uv run pytest
```

Expected: `no tests ran` (exits 5 or 0 depending on pytest version) — not an import error.

- [ ] **Step 11: Commit**

```bash
git add pyproject.toml uv.lock .env.example manage.py config/ .gitignore
git commit -m "feat: bootstrap Django project + MySQL settings"
```

---

## Task 2: Custom User model

A `User` keyed on `phone_number` with the default `username` field removed. Migration applied to MySQL.

**Files:**
- Create: `accounts/__init__.py`
- Create: `accounts/apps.py`
- Create: `accounts/models.py`
- Create: `accounts/admin.py`
- Create: `accounts/migrations/__init__.py`
- Create: `accounts/tests/__init__.py`
- Create: `accounts/tests/test_models.py`
- Create: `conftest.py` (repo root)
- Modify: `config/settings.py` (add `accounts` to `INSTALLED_APPS`, set `AUTH_USER_MODEL`)

- [ ] **Step 1: Write `accounts/__init__.py` (empty) and `accounts/apps.py`**

`accounts/apps.py`:

```python
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
```

- [ ] **Step 2: Write `accounts/migrations/__init__.py`**

Empty file.

- [ ] **Step 3: Wire app into settings**

In `config/settings.py`, append `"accounts"` to `INSTALLED_APPS` and add `AUTH_USER_MODEL = "accounts.User"` at the bottom of the file (above the Daraja config block is fine).

- [ ] **Step 4: Write `conftest.py` (repo root)**

```python
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
```

- [ ] **Step 5: Write failing test `accounts/tests/__init__.py` (empty) and `accounts/tests/test_models.py`**

```python
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
```

- [ ] **Step 6: Run tests, watch them fail with "no such table" or model-not-found**

```bash
uv run pytest accounts/tests/test_models.py -v
```

Expected: ERRORS (no migrations yet, no model).

- [ ] **Step 7: Write `accounts/models.py`**

```python
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError("phone_number is required")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields["is_staff"] is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields["is_superuser"] is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    username = None
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone_number
```

- [ ] **Step 8: Write `accounts/admin.py`**

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("phone_number", "email", "is_staff", "is_active")
    search_fields = ("phone_number", "email")
    ordering = ("phone_number",)

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Personal info", {"fields": ("email",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("phone_number", "password1", "password2")}),
    )
```

- [ ] **Step 9: Generate migration**

```bash
uv run python manage.py makemigrations accounts
```

Expected: `Migrations for 'accounts': 0001_initial.py - Create model User`.

- [ ] **Step 10: Apply migrations and re-run tests**

```bash
uv run python manage.py migrate
uv run pytest accounts/tests/test_models.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 11: Commit**

```bash
git add accounts/ conftest.py config/settings.py
git commit -m "feat: custom User model keyed on phone_number"
```

---

## Task 3: Register endpoint

POST `/api/auth/register/` creates a user; returns the user (no token — login is a separate call).

**Files:**
- Create: `accounts/serializers.py`
- Create: `accounts/views.py`
- Create: `accounts/urls.py`
- Create: `accounts/tests/test_auth.py`
- Modify: `config/urls.py` (mount `/api/auth/`)

- [ ] **Step 1: Write failing test `accounts/tests/test_auth.py`**

```python
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
```

- [ ] **Step 2: Run test, expect 404**

```bash
uv run pytest accounts/tests/test_auth.py -v
```

Expected: FAIL (404, route not wired).

- [ ] **Step 3: Write `accounts/serializers.py`**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "phone_number", "email", "date_joined")
        read_only_fields = ("id", "date_joined")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    class Meta:
        model = User
        fields = ("phone_number", "password", "email")

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)
```

- [ ] **Step 4: Write `accounts/views.py`**

```python
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    def post(self, request):
        # Task 5 will blacklist the refresh token here.
        return Response(status=status.HTTP_205_RESET_CONTENT)
```

- [ ] **Step 5: Write `accounts/urls.py`**

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import LogoutView, MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
]
```

- [ ] **Step 6: Mount in `config/urls.py`**

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
]
```

- [ ] **Step 7: Run tests and confirm pass**

```bash
uv run pytest accounts/tests/test_auth.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add accounts/serializers.py accounts/views.py accounts/urls.py accounts/tests/test_auth.py config/urls.py
git commit -m "feat: /api/auth/register/ endpoint"
```

---

## Task 4: Login, refresh, /me, logout stub

Wire SimpleJWT for login + refresh; verify `/me` requires auth; logout returns 205 (stub for task 5's blacklist).

**Files:**
- Modify: `accounts/tests/test_auth.py` (append tests)

- [ ] **Step 1: Append failing tests to `accounts/tests/test_auth.py`**

```python
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
```

- [ ] **Step 2: Run tests and confirm pass**

The login/refresh routes and the views were wired in task 3, so these should pass without further code changes.

```bash
uv run pytest accounts/tests/test_auth.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add accounts/tests/test_auth.py
git commit -m "test: cover login, refresh, /me, logout-stub endpoints"
```

---

## Task 5: Meter model

`Meter` owned by a User, with a digits-only `meter_number`.

**Files:**
- Create: `meters/__init__.py`
- Create: `meters/apps.py`
- Create: `meters/models.py`
- Create: `meters/admin.py`
- Create: `meters/migrations/__init__.py`
- Create: `meters/tests/__init__.py`
- Create: `meters/tests/test_models.py`
- Modify: `config/settings.py` (add `meters` to `INSTALLED_APPS`)
- Modify: `conftest.py` (add `meter` and `other_meter` fixtures)

- [ ] **Step 1: Write `meters/__init__.py` (empty), `meters/migrations/__init__.py` (empty), and `meters/apps.py`**

`meters/apps.py`:

```python
from django.apps import AppConfig

class MetersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "meters"
```

- [ ] **Step 2: Add `"meters"` to `INSTALLED_APPS` in `config/settings.py`**

- [ ] **Step 3: Write failing test `meters/tests/__init__.py` (empty) and `meters/tests/test_models.py`**

```python
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
```

- [ ] **Step 4: Run tests, expect import error**

```bash
uv run pytest meters/tests/test_models.py -v
```

Expected: FAIL (no `meters.models.Meter`).

- [ ] **Step 5: Write `meters/models.py`**

```python
import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class Meter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meters",
    )
    meter_number = models.CharField(
        max_length=14,
        unique=True,
        validators=[RegexValidator(regex=r"^\d{10,14}$", message="meter_number must be 10-14 digits")],
    )
    label = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["owner"])]

    def __str__(self):
        return self.meter_number
```

- [ ] **Step 6: Write `meters/admin.py`**

```python
from django.contrib import admin

from .models import Meter


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ("meter_number", "owner", "label", "created_at")
    search_fields = ("meter_number", "owner__phone_number")
    list_filter = ("created_at",)
```

- [ ] **Step 7: Generate + apply migration**

```bash
uv run python manage.py makemigrations meters
uv run python manage.py migrate
```

- [ ] **Step 8: Append fixtures to `conftest.py`**

```python
import pytest
from meters.models import Meter


@pytest.fixture
def meter(user):
    return Meter.objects.create(owner=user, meter_number="0100000001", label="Home")


@pytest.fixture
def other_meter(other_user):
    return Meter.objects.create(owner=other_user, meter_number="0200000001", label="Other Home")
```

(Merge imports with what's already at the top.)

- [ ] **Step 9: Re-run tests and confirm pass**

```bash
uv run pytest meters/tests/test_models.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 10: Commit**

```bash
git add meters/ config/settings.py conftest.py
git commit -m "feat: Meter model owned by User"
```

---

## Task 6: Meter viewset (owner-scoped CRUD)

GET/POST/DELETE on `/api/meters/`, filtered to `request.user`.

**Files:**
- Create: `meters/serializers.py`
- Create: `meters/views.py`
- Create: `meters/urls.py`
- Create: `meters/tests/test_views.py`
- Modify: `config/urls.py` (mount `/api/meters/`)

- [ ] **Step 1: Write failing test `meters/tests/test_views.py`**

```python
import pytest

from meters.models import Meter


@pytest.mark.django_db
def test_list_meters_owner_scoped(authed_client, meter, other_meter):
    resp = authed_client.get("/api/meters/")
    assert resp.status_code == 200
    body = resp.json()
    numbers = [m["meter_number"] for m in body]
    assert meter.meter_number in numbers
    assert other_meter.meter_number not in numbers


@pytest.mark.django_db
def test_create_meter(authed_client, user):
    resp = authed_client.post(
        "/api/meters/",
        {"meter_number": "0900000001", "label": "Shop"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["meter_number"] == "0900000001"
    assert Meter.objects.filter(meter_number="0900000001", owner=user).exists()


@pytest.mark.django_db
def test_create_meter_rejects_non_digit(authed_client):
    resp = authed_client.post(
        "/api/meters/",
        {"meter_number": "ABC1234567"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_retrieve_other_users_meter_404s(authed_client, other_meter):
    resp = authed_client.get(f"/api/meters/{other_meter.id}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_delete_meter(authed_client, meter):
    resp = authed_client.delete(f"/api/meters/{meter.id}/")
    assert resp.status_code == 204
    assert not Meter.objects.filter(id=meter.id).exists()


@pytest.mark.django_db
def test_unauthed_list_rejected(api_client):
    resp = api_client.get("/api/meters/")
    assert resp.status_code == 401
```

- [ ] **Step 2: Run tests, expect 404s**

```bash
uv run pytest meters/tests/test_views.py -v
```

Expected: FAIL (no routes wired).

- [ ] **Step 3: Write `meters/serializers.py`**

```python
from rest_framework import serializers

from .models import Meter


class MeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meter
        fields = ("id", "meter_number", "label", "created_at")
        read_only_fields = ("id", "created_at")
```

- [ ] **Step 4: Write `meters/views.py`**

```python
from rest_framework import mixins, viewsets

from .models import Meter
from .serializers import MeterSerializer


class MeterViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MeterSerializer

    def get_queryset(self):
        return Meter.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
```

- [ ] **Step 5: Write `meters/urls.py`**

```python
from rest_framework.routers import DefaultRouter

from .views import MeterViewSet

router = DefaultRouter()
router.register(r"", MeterViewSet, basename="meter")
urlpatterns = router.urls
```

- [ ] **Step 6: Mount in `config/urls.py`**

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/meters/", include("meters.urls")),
]
```

- [ ] **Step 7: Run tests and confirm pass**

```bash
uv run pytest meters/tests/test_views.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add meters/serializers.py meters/views.py meters/urls.py meters/tests/test_views.py config/urls.py
git commit -m "feat: owner-scoped Meter CRUD viewset"
```

---

## Task 7: Control number generator

`payments/control_numbers.py` produces unique 12-digit strings starting with `"99"`. Collisions retried up to N times.

**Files:**
- Create: `payments/__init__.py`
- Create: `payments/apps.py`
- Create: `payments/migrations/__init__.py`
- Create: `payments/control_numbers.py`
- Create: `payments/tests/__init__.py`
- Create: `payments/tests/test_control_numbers.py`
- Modify: `config/settings.py` (add `payments` to `INSTALLED_APPS`)

- [ ] **Step 1: Write `payments/__init__.py` (empty), `payments/migrations/__init__.py` (empty), and `payments/apps.py`**

`payments/apps.py`:

```python
from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payments"
```

Add `"payments"` to `INSTALLED_APPS`.

- [ ] **Step 2: Write failing test `payments/tests/__init__.py` (empty) and `payments/tests/test_control_numbers.py`**

```python
import re

from payments.control_numbers import generate_control_number


def test_format_is_12_digits_with_99_prefix():
    cn = generate_control_number(existing=set())
    assert re.fullmatch(r"99\d{10}", cn), cn


def test_avoids_collisions():
    existing = {"99" + "0" * 10}
    cn = generate_control_number(existing=existing)
    assert cn not in existing
    assert re.fullmatch(r"99\d{10}", cn)


def test_raises_when_space_exhausted(monkeypatch):
    import payments.control_numbers as cn_mod

    # Force the candidate generator to always return the same value
    monkeypatch.setattr(cn_mod, "_random_suffix", lambda: "0000000000")

    existing = {"990000000000"}
    try:
        cn_mod.generate_control_number(existing=existing, max_attempts=5)
    except cn_mod.ControlNumberCollisionError:
        return
    raise AssertionError("expected ControlNumberCollisionError")
```

- [ ] **Step 3: Run test, expect import error**

```bash
uv run pytest payments/tests/test_control_numbers.py -v
```

Expected: FAIL.

- [ ] **Step 4: Write `payments/control_numbers.py`**

```python
import secrets


class ControlNumberCollisionError(RuntimeError):
    pass


def _random_suffix() -> str:
    # 10 random digits
    return "".join(str(secrets.randbelow(10)) for _ in range(10))


def generate_control_number(*, existing: set[str], max_attempts: int = 10) -> str:
    """Return a 12-digit string starting with '99' that is not in `existing`.

    Raises ControlNumberCollisionError if no unique value is found in max_attempts tries.
    The caller is responsible for passing the current set of in-use control numbers
    (typically by querying the Transaction table).
    """
    for _ in range(max_attempts):
        candidate = "99" + _random_suffix()
        if candidate not in existing:
            return candidate
    raise ControlNumberCollisionError(
        f"could not generate unique control number after {max_attempts} attempts"
    )
```

- [ ] **Step 5: Run tests and confirm pass**

```bash
uv run pytest payments/tests/test_control_numbers.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add payments/__init__.py payments/apps.py payments/migrations/__init__.py payments/control_numbers.py payments/tests/__init__.py payments/tests/test_control_numbers.py config/settings.py
git commit -m "feat: 12-digit 99-prefix control number generator"
```

---

## Task 8: Transaction + Token models

Two models with their migration. No views yet.

**Files:**
- Create: `payments/models.py`
- Create: `payments/admin.py`
- Create: `payments/tests/test_models.py`

- [ ] **Step 1: Write failing test `payments/tests/test_models.py`**

```python
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
```

- [ ] **Step 2: Run, expect import error**

```bash
uv run pytest payments/tests/test_models.py -v
```

- [ ] **Step 3: Write `payments/models.py`**

```python
import uuid

from django.conf import settings
from django.db import models


class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        EXPIRED = "expired", "Expired"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    meter = models.ForeignKey(
        "meters.Meter",
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    control_number = models.CharField(max_length=12, unique=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    provider_reference = models.CharField(max_length=64, blank=True, default="")
    paid_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["control_number"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return self.control_number


class Token(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name="token",
    )
    value = models.CharField(max_length=32)
    strategy = models.CharField(max_length=16)
    delivered_via_sms = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.value
```

- [ ] **Step 4: Write `payments/admin.py`**

```python
from django.contrib import admin

from .models import Token, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("control_number", "user", "meter", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("control_number", "user__phone_number", "meter__meter_number")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("value", "transaction", "strategy", "delivered_via_sms", "created_at")
    search_fields = ("value", "transaction__control_number")
    readonly_fields = ("id", "created_at")
```

- [ ] **Step 5: Generate + apply migration**

```bash
uv run python manage.py makemigrations payments
uv run python manage.py migrate
```

- [ ] **Step 6: Run tests and confirm pass**

```bash
uv run pytest payments/tests/test_models.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add payments/models.py payments/admin.py payments/migrations/0001_initial.py payments/tests/test_models.py
git commit -m "feat: Transaction and Token models"
```

---

## Task 9: HMAC signing helper

`payments/signing.py` with `verify_hmac(body, header, secret)`. Constant-time compare. Header format: `sha256=<hex>`.

**Files:**
- Create: `payments/signing.py`
- Create: `payments/tests/test_signing.py`

- [ ] **Step 1: Write failing test `payments/tests/test_signing.py`**

```python
import hashlib
import hmac as stdlib_hmac

from payments.signing import compute_hmac, verify_hmac


SECRET = b"super-secret-test-key"
BODY = b'{"control_number":"990000000001","amount":"5000","status":"paid"}'


def _expected_header(body, secret):
    return "sha256=" + stdlib_hmac.new(secret, body, hashlib.sha256).hexdigest()


def test_compute_hmac_format():
    h = compute_hmac(BODY, SECRET)
    assert h.startswith("sha256=")
    assert len(h) == len("sha256=") + 64  # 32 bytes hex


def test_verify_correct_signature():
    header = _expected_header(BODY, SECRET)
    assert verify_hmac(BODY, header, SECRET) is True


def test_verify_wrong_signature():
    assert verify_hmac(BODY, "sha256=" + "0" * 64, SECRET) is False


def test_verify_rejects_missing_prefix():
    naked = stdlib_hmac.new(SECRET, BODY, hashlib.sha256).hexdigest()
    assert verify_hmac(BODY, naked, SECRET) is False


def test_verify_rejects_empty_header():
    assert verify_hmac(BODY, "", SECRET) is False


def test_verify_rejects_wrong_algorithm():
    assert verify_hmac(BODY, "sha1=" + "a" * 40, SECRET) is False
```

- [ ] **Step 2: Run tests, expect import error**

```bash
uv run pytest payments/tests/test_signing.py -v
```

- [ ] **Step 3: Write `payments/signing.py`**

```python
import hashlib
import hmac


PREFIX = "sha256="


def compute_hmac(body: bytes, secret: bytes) -> str:
    digest = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return PREFIX + digest


def verify_hmac(body: bytes, header: str, secret: bytes) -> bool:
    """Return True iff `header` is a valid sha256 HMAC of `body` under `secret`.

    Header format: 'sha256=<hex>'. Comparison is constant-time.
    """
    if not header or not header.startswith(PREFIX):
        return False
    expected = compute_hmac(body, secret)
    return hmac.compare_digest(expected, header)
```

- [ ] **Step 4: Run tests and confirm pass**

```bash
uv run pytest payments/tests/test_signing.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add payments/signing.py payments/tests/test_signing.py
git commit -m "feat: HMAC-SHA256 signing helper for webhooks"
```

---

## Task 10: Token strategy ABC + SimpleTokenStrategy

The `TokenStrategy` seam. `SimpleTokenStrategy` matches the brief's `(amount × 1357) + meter_number`. Factory reads `settings.TOKEN_STRATEGY`.

**Files:**
- Create: `payments/token_logic.py`
- Create: `payments/tests/test_token_logic.py`

- [ ] **Step 1: Write failing test `payments/tests/test_token_logic.py`**

```python
from decimal import Decimal

import pytest
from django.test import override_settings

from payments.token_logic import SimpleTokenStrategy, get_strategy


def test_simple_strategy_formula():
    strat = SimpleTokenStrategy(multiplier=1357)
    value = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="ignored")
    assert value == str(5000 * 1357 + 100000001)


def test_simple_strategy_deterministic():
    strat = SimpleTokenStrategy(multiplier=1357)
    a = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n1")
    b = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n2")
    assert a == b


def test_simple_strategy_differs_by_inputs():
    strat = SimpleTokenStrategy(multiplier=1357)
    base = strat.generate(amount=Decimal("5000"), meter_number="0100000001", nonce="n")
    other_amount = strat.generate(amount=Decimal("6000"), meter_number="0100000001", nonce="n")
    other_meter = strat.generate(amount=Decimal("5000"), meter_number="0100000002", nonce="n")
    assert base != other_amount
    assert base != other_meter


def test_simple_strategy_name():
    assert SimpleTokenStrategy(multiplier=1357).name == "simple"


@override_settings(TOKEN_STRATEGY="simple", TOKEN_SIMPLE_MULTIPLIER=1357)
def test_get_strategy_returns_simple():
    s = get_strategy()
    assert isinstance(s, SimpleTokenStrategy)
    assert s.name == "simple"


@override_settings(TOKEN_STRATEGY="unknown")
def test_get_strategy_unknown_raises():
    with pytest.raises(ValueError):
        get_strategy()
```

- [ ] **Step 2: Run, expect import error**

```bash
uv run pytest payments/tests/test_token_logic.py -v
```

- [ ] **Step 3: Write `payments/token_logic.py`**

```python
from abc import ABC, abstractmethod
from decimal import Decimal

from django.conf import settings


class TokenStrategy(ABC):
    name: str

    @abstractmethod
    def generate(self, *, amount: Decimal, meter_number: str, nonce: str) -> str:
        ...


class SimpleTokenStrategy(TokenStrategy):
    name = "simple"

    def __init__(self, *, multiplier: int):
        self.multiplier = multiplier

    def generate(self, *, amount: Decimal, meter_number: str, nonce: str) -> str:
        # Brief formula: (amount × 1357) + meter_id.
        # nonce is accepted for interface uniformity (HmacTokenStrategy will use it).
        return str(int(amount) * self.multiplier + int(meter_number))


def get_strategy() -> TokenStrategy:
    name = settings.TOKEN_STRATEGY
    if name == "simple":
        return SimpleTokenStrategy(multiplier=settings.TOKEN_SIMPLE_MULTIPLIER)
    # Task 3 will register HmacTokenStrategy here.
    raise ValueError(f"unknown TOKEN_STRATEGY: {name!r}")
```

- [ ] **Step 4: Run tests and confirm pass**

```bash
uv run pytest payments/tests/test_token_logic.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add payments/token_logic.py payments/tests/test_token_logic.py
git commit -m "feat: TokenStrategy seam + SimpleTokenStrategy"
```

---

## Task 11: SMS provider seam + ConsoleSmsProvider + send_token_sms

The `SmsProvider` interface, a logging-only `ConsoleSmsProvider`, and the `send_token_sms(token)` helper that the webhook calls.

**Files:**
- Create: `payments/sms.py`
- Create: `payments/tests/test_sms.py`

- [ ] **Step 1: Write failing test `payments/tests/test_sms.py`**

```python
import logging
from decimal import Decimal

import pytest
from django.test import override_settings
from django.utils import timezone

from payments.models import Token, Transaction
from payments.sms import (
    ConsoleSmsProvider,
    SmsProvider,
    SmsResult,
    _get_provider,
    send_token_sms,
)


def test_console_provider_returns_ok(caplog):
    p = ConsoleSmsProvider()
    with caplog.at_level(logging.INFO, logger="payments.sms"):
        result = p.send(to="+255700000099", message="Your token is 1234")
    assert isinstance(result, SmsResult)
    assert result.ok is True
    assert "1234" in caplog.text


@override_settings(SMS_PROVIDER="console")
def test_get_provider_returns_console():
    assert isinstance(_get_provider(), ConsoleSmsProvider)


@override_settings(SMS_PROVIDER="unknown")
def test_get_provider_unknown_raises():
    with pytest.raises(ValueError):
        _get_provider()


@pytest.mark.django_db
@override_settings(SMS_PROVIDER="console")
def test_send_token_sms_marks_delivered(user, meter):
    txn = Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000099001",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    token = Token.objects.create(transaction=txn, value="1234567", strategy="simple")
    send_token_sms(token)
    token.refresh_from_db()
    assert token.delivered_via_sms is True
    assert token.delivered_at is not None


class FailingProvider(SmsProvider):
    name = "failing"

    def send(self, *, to, message):
        return SmsResult(ok=False, error="boom")


@pytest.mark.django_db
def test_send_token_sms_does_not_mark_delivered_on_failure(user, meter, monkeypatch):
    txn = Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000099002",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )
    token = Token.objects.create(transaction=txn, value="1234567", strategy="simple")

    import payments.sms as sms_mod

    monkeypatch.setattr(sms_mod, "_get_provider", lambda: FailingProvider())
    send_token_sms(token)
    token.refresh_from_db()
    assert token.delivered_via_sms is False
    assert token.delivered_at is None
```

- [ ] **Step 2: Run, expect import error**

```bash
uv run pytest payments/tests/test_sms.py -v
```

- [ ] **Step 3: Write `payments/sms.py`**

```python
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from .models import Token


logger = logging.getLogger(__name__)


@dataclass
class SmsResult:
    ok: bool
    provider_message_id: str | None = None
    error: str | None = None


class SmsProvider(ABC):
    name: str

    @abstractmethod
    def send(self, *, to: str, message: str) -> SmsResult:
        ...


class ConsoleSmsProvider(SmsProvider):
    name = "console"

    def send(self, *, to: str, message: str) -> SmsResult:
        logger.info("SMS to %s: %s", to, message)
        return SmsResult(ok=True, provider_message_id=f"console-{to}")


def _get_provider() -> SmsProvider:
    name = settings.SMS_PROVIDER
    if name == "console":
        return ConsoleSmsProvider()
    # Task 4 will register the real provider (Beem / Twilio / AT) here.
    raise ValueError(f"unknown SMS_PROVIDER: {name!r}")


def _compose_message(token: Token) -> str:
    txn = token.transaction
    return (
        f"Daraja Water: your token for meter {txn.meter.meter_number} "
        f"(amount {txn.amount}) is {token.value}."
    )


def send_token_sms(token: Token) -> None:
    """Best-effort SMS dispatch. Marks the token delivered on success.

    Failures are logged but never raised — the caller (webhook) must not
    roll back the paid Transaction just because SMS flaked.
    """
    try:
        provider = _get_provider()
        result = provider.send(
            to=token.transaction.user.phone_number,
            message=_compose_message(token),
        )
    except Exception:  # noqa: BLE001 — best-effort
        logger.exception("SMS provider raised; not marking delivered")
        return

    if result.ok:
        token.delivered_via_sms = True
        token.delivered_at = timezone.now()
        token.save(update_fields=["delivered_via_sms", "delivered_at"])
    else:
        logger.warning("SMS send failed: %s", result.error)
```

- [ ] **Step 4: Run tests and confirm pass**

```bash
uv run pytest payments/tests/test_sms.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add payments/sms.py payments/tests/test_sms.py
git commit -m "feat: SmsProvider seam + ConsoleSmsProvider + send_token_sms"
```

---

## Task 12: InitiatePaymentView

`POST /api/transactions/initiate/` — validates meter ownership + amount, mints a control number, creates a pending `Transaction`.

**Files:**
- Create: `payments/serializers.py`
- Create: `payments/views.py` (will add the webhook view in task 13)
- Create: `payments/urls.py`
- Create: `payments/tests/test_initiate.py`
- Modify: `config/urls.py` (mount `/api/transactions/`)

- [ ] **Step 1: Write failing test `payments/tests/test_initiate.py`**

```python
import re
from decimal import Decimal

import pytest

from payments.models import Transaction


@pytest.mark.django_db
def test_initiate_creates_pending_transaction(authed_client, meter, user):
    resp = authed_client.post(
        "/api/transactions/initiate/",
        {"meter_id": str(meter.id), "amount": "5000"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert re.fullmatch(r"99\d{10}", body["control_number"])
    assert body["status"] == "pending"
    assert body["amount"] == "5000.00"
    assert "expires_at" in body

    txn = Transaction.objects.get(id=body["id"])
    assert txn.user == user
    assert txn.meter == meter
    assert txn.amount == Decimal("5000.00")


@pytest.mark.django_db
def test_initiate_rejects_other_users_meter(authed_client, other_meter):
    resp = authed_client.post(
        "/api/transactions/initiate/",
        {"meter_id": str(other_meter.id), "amount": "5000"},
        format="json",
    )
    assert resp.status_code in (400, 404)


@pytest.mark.django_db
def test_initiate_rejects_nonpositive_amount(authed_client, meter):
    resp = authed_client.post(
        "/api/transactions/initiate/",
        {"meter_id": str(meter.id), "amount": "0"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_initiate_requires_auth(api_client, meter):
    resp = api_client.post(
        "/api/transactions/initiate/",
        {"meter_id": str(meter.id), "amount": "5000"},
        format="json",
    )
    assert resp.status_code == 401
```

- [ ] **Step 2: Run, expect 404**

```bash
uv run pytest payments/tests/test_initiate.py -v
```

- [ ] **Step 3: Write `payments/serializers.py`**

```python
from decimal import Decimal

from rest_framework import serializers

from meters.models import Meter

from .models import Token, Transaction


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ("id", "value", "strategy", "delivered_via_sms", "delivered_at", "created_at")


class TransactionSerializer(serializers.ModelSerializer):
    token = TokenSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "meter",
            "amount",
            "control_number",
            "status",
            "provider_reference",
            "paid_at",
            "expires_at",
            "created_at",
            "token",
        )
        read_only_fields = fields


class InitiateSerializer(serializers.Serializer):
    meter_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    def validate_meter_id(self, value):
        user = self.context["request"].user
        try:
            self.context["meter"] = Meter.objects.get(id=value, owner=user)
        except Meter.DoesNotExist:
            raise serializers.ValidationError("meter not found")
        return value
```

- [ ] **Step 4: Write `payments/views.py`**

```python
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .control_numbers import generate_control_number
from .models import Transaction
from .serializers import InitiateSerializer, TransactionSerializer


class InitiatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InitiateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        meter = serializer.context["meter"]
        amount = serializer.validated_data["amount"]

        existing = set(Transaction.objects.values_list("control_number", flat=True))
        control_number = generate_control_number(existing=existing)

        txn = Transaction.objects.create(
            user=request.user,
            meter=meter,
            amount=amount,
            control_number=control_number,
            expires_at=timezone.now() + timedelta(minutes=settings.TRANSACTION_TTL_MINUTES),
        )
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)
```

- [ ] **Step 5: Write `payments/urls.py`**

```python
from django.urls import path

from .views import InitiatePaymentView


urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view(), name="transactions-initiate"),
]
```

- [ ] **Step 6: Mount in `config/urls.py`**

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/meters/", include("meters.urls")),
    path("api/transactions/", include("payments.urls")),
]
```

- [ ] **Step 7: Run tests and confirm pass**

```bash
uv run pytest payments/tests/test_initiate.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add payments/serializers.py payments/views.py payments/urls.py payments/tests/test_initiate.py config/urls.py
git commit -m "feat: POST /api/transactions/initiate/"
```

---

## Task 13: PaymentWebhookView

`POST /api/webhooks/payment/` — public, HMAC-verified, idempotent. Mints a Token on first `paid` delivery; returns the same Token on replay.

**Files:**
- Modify: `payments/views.py` (add `PaymentWebhookView`)
- Modify: `payments/urls.py` (route under `/webhooks/payment/`)
- Create: `payments/tests/test_webhook.py`
- Modify: `config/urls.py` (mount `/api/webhooks/`)

- [ ] **Step 1: Write failing test `payments/tests/test_webhook.py`**

```python
import json
from decimal import Decimal

import pytest
from django.test import override_settings
from django.utils import timezone

from payments.models import Token, Transaction
from payments.signing import compute_hmac


SECRET = b"webhook-test-secret"


def _post_webhook(api_client, body: dict, secret: bytes = SECRET, tamper: bool = False):
    raw = json.dumps(body).encode()
    sig = compute_hmac(raw, secret)
    if tamper:
        sig = "sha256=" + "0" * 64
    return api_client.post(
        "/api/webhooks/payment/",
        data=raw,
        content_type="application/json",
        HTTP_X_SIGNATURE=sig,
    )


@pytest.fixture
def pending_txn(db, user, meter):
    return Transaction.objects.create(
        user=user,
        meter=meter,
        amount=Decimal("5000"),
        control_number="990000000010",
        expires_at=timezone.now() + timezone.timedelta(minutes=30),
    )


@override_settings(WEBHOOK_HMAC_SECRET=SECRET.decode())
@pytest.mark.django_db
def test_invalid_signature_returns_401(api_client, pending_txn):
    resp = _post_webhook(
        api_client,
        {
            "control_number": pending_txn.control_number,
            "amount": "5000",
            "provider_reference": "pp-1",
            "status": "paid",
        },
        tamper=True,
    )
    assert resp.status_code == 401
    pending_txn.refresh_from_db()
    assert pending_txn.status == "pending"
    assert not Token.objects.filter(transaction=pending_txn).exists()


@override_settings(WEBHOOK_HMAC_SECRET=SECRET.decode())
@pytest.mark.django_db
def test_unknown_control_number_returns_404(api_client):
    resp = _post_webhook(
        api_client,
        {
            "control_number": "999999999999",
            "amount": "5000",
            "provider_reference": "pp-2",
            "status": "paid",
        },
    )
    assert resp.status_code == 404


@override_settings(
    WEBHOOK_HMAC_SECRET=SECRET.decode(),
    TOKEN_STRATEGY="simple",
    TOKEN_SIMPLE_MULTIPLIER=1357,
    SMS_PROVIDER="console",
)
@pytest.mark.django_db
def test_paid_payload_creates_token(api_client, pending_txn):
    resp = _post_webhook(
        api_client,
        {
            "control_number": pending_txn.control_number,
            "amount": "5000",
            "provider_reference": "pp-3",
            "status": "paid",
        },
    )
    assert resp.status_code == 200, resp.content
    pending_txn.refresh_from_db()
    assert pending_txn.status == "paid"
    assert pending_txn.paid_at is not None
    assert pending_txn.provider_reference == "pp-3"
    token = Token.objects.get(transaction=pending_txn)
    expected_value = str(5000 * 1357 + int(pending_txn.meter.meter_number))
    assert token.value == expected_value
    body = resp.json()
    assert body["token"]["value"] == expected_value


@override_settings(
    WEBHOOK_HMAC_SECRET=SECRET.decode(),
    TOKEN_STRATEGY="simple",
    TOKEN_SIMPLE_MULTIPLIER=1357,
    SMS_PROVIDER="console",
)
@pytest.mark.django_db
def test_replay_is_idempotent(api_client, pending_txn):
    payload = {
        "control_number": pending_txn.control_number,
        "amount": "5000",
        "provider_reference": "pp-4",
        "status": "paid",
    }
    first = _post_webhook(api_client, payload)
    second = _post_webhook(api_client, payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["token"]["value"] == second.json()["token"]["value"]
    assert Token.objects.filter(transaction=pending_txn).count() == 1


@override_settings(WEBHOOK_HMAC_SECRET=SECRET.decode())
@pytest.mark.django_db
def test_failed_payload_marks_failed(api_client, pending_txn):
    resp = _post_webhook(
        api_client,
        {
            "control_number": pending_txn.control_number,
            "amount": "5000",
            "provider_reference": "pp-5",
            "status": "failed",
        },
    )
    assert resp.status_code == 200
    pending_txn.refresh_from_db()
    assert pending_txn.status == "failed"
    assert not Token.objects.filter(transaction=pending_txn).exists()
```

- [ ] **Step 2: Run, expect 404**

```bash
uv run pytest payments/tests/test_webhook.py -v
```

- [ ] **Step 3: Extend `payments/views.py` with `PaymentWebhookView`**

Append to `payments/views.py`:

```python
import json

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone

from .models import Token
from .serializers import TokenSerializer
from .signing import verify_hmac
from .sms import send_token_sms
from .token_logic import get_strategy


class PaymentWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        body = request.body
        signature = request.headers.get("X-Signature", "")
        secret = settings.WEBHOOK_HMAC_SECRET.encode()
        if not verify_hmac(body, signature, secret):
            return Response(
                {"detail": "invalid signature"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError:
            return Response({"detail": "invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

        control_number = payload.get("control_number")
        if not control_number:
            return Response(
                {"detail": "control_number required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with db_transaction.atomic():
            try:
                txn = Transaction.objects.select_for_update().get(control_number=control_number)
            except Transaction.DoesNotExist:
                return Response(
                    {"detail": "transaction not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if txn.status == Transaction.Status.PAID:
                return Response(
                    {
                        "transaction": TransactionSerializer(txn).data,
                        "token": TokenSerializer(txn.token).data,
                    },
                    status=status.HTTP_200_OK,
                )

            provider_status = payload.get("status")

            if provider_status == "paid":
                txn.status = Transaction.Status.PAID
                txn.paid_at = timezone.now()
                txn.provider_reference = payload.get("provider_reference", "")
                txn.save(update_fields=["status", "paid_at", "provider_reference", "updated_at"])

                strategy = get_strategy()
                value = strategy.generate(
                    amount=txn.amount,
                    meter_number=txn.meter.meter_number,
                    nonce=str(txn.id),
                )
                token = Token.objects.create(
                    transaction=txn,
                    value=value,
                    strategy=strategy.name,
                )
            else:
                txn.status = Transaction.Status.FAILED
                txn.save(update_fields=["status", "updated_at"])
                return Response(
                    {"transaction": TransactionSerializer(txn).data, "token": None},
                    status=status.HTTP_200_OK,
                )

        # SMS dispatch outside the DB transaction; failures must not roll back.
        send_token_sms(token)

        return Response(
            {
                "transaction": TransactionSerializer(txn).data,
                "token": TokenSerializer(token).data,
            },
            status=status.HTTP_200_OK,
        )
```

(Note: `from .models import Transaction` is already in scope from the existing imports in `payments/views.py`.)

- [ ] **Step 4: Update `payments/urls.py`**

```python
from django.urls import path

from .views import InitiatePaymentView, PaymentWebhookView


urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view(), name="transactions-initiate"),
]

webhook_urlpatterns = [
    path("payment/", PaymentWebhookView.as_view(), name="webhook-payment"),
]
```

- [ ] **Step 5: Mount webhook in `config/urls.py`**

```python
from payments.urls import webhook_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/meters/", include("meters.urls")),
    path("api/transactions/", include("payments.urls")),
    path("api/webhooks/", include((webhook_urlpatterns, "webhooks"), namespace="webhooks")),
]
```

- [ ] **Step 6: Run tests and confirm pass**

```bash
uv run pytest payments/tests/test_webhook.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 7: Run the whole suite**

```bash
uv run pytest -v
```

Expected: all tests across all apps PASS.

- [ ] **Step 8: Commit**

```bash
git add payments/views.py payments/urls.py payments/tests/test_webhook.py config/urls.py
git commit -m "feat: HMAC-verified, idempotent payment webhook"
```

---

## Task 14: TransactionViewSet — list + detail

`GET /api/transactions/` and `GET /api/transactions/{id}/` for the authenticated user. Detail includes the token if present.

**Files:**
- Modify: `payments/views.py` (add `TransactionViewSet`)
- Modify: `payments/urls.py` (router)
- Create: `payments/tests/test_transactions.py`

- [ ] **Step 1: Write failing test `payments/tests/test_transactions.py`**

```python
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
```

- [ ] **Step 2: Run, expect 404**

- [ ] **Step 3: Extend `payments/views.py`**

Append:

```python
from rest_framework import mixins, viewsets


class TransactionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return (
            Transaction.objects.filter(user=self.request.user)
            .select_related("meter", "token")
            .order_by("-created_at")
        )
```

- [ ] **Step 4: Update `payments/urls.py`**

```python
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import InitiatePaymentView, PaymentWebhookView, TransactionViewSet


router = DefaultRouter()
router.register(r"", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view(), name="transactions-initiate"),
    *router.urls,
]

webhook_urlpatterns = [
    path("payment/", PaymentWebhookView.as_view(), name="webhook-payment"),
]
```

(The router's `r""` registration produces `/api/transactions/` and `/api/transactions/{id}/`; the `initiate/` path is mounted before the router so it takes precedence.)

- [ ] **Step 5: Run tests and confirm pass**

```bash
uv run pytest payments/tests/test_transactions.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 6: Run the full suite**

```bash
uv run pytest -v
```

Expected: every test across the project passes (~35+ tests).

- [ ] **Step 7: Commit**

```bash
git add payments/views.py payments/urls.py payments/tests/test_transactions.py
git commit -m "feat: GET /api/transactions/ list + detail (owner-scoped)"
```

---

## Task 15: README + manual sanity check

Document setup and a copy-paste shell snippet that runs the end-to-end flow against a live server.

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# Daraja Water

Prepaid water meter top-up platform. Django + DRF + MySQL JSON API.

## Setup (macOS)

```bash
# 1. System deps
brew install mysql pkg-config mysql-client
brew services start mysql
export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"

# 2. Create databases
mysql -uroot <<'SQL'
CREATE DATABASE IF NOT EXISTS daraja;
CREATE DATABASE IF NOT EXISTS test_daraja;
CREATE USER IF NOT EXISTS 'daraja'@'localhost' IDENTIFIED BY 'daraja';
GRANT ALL PRIVILEGES ON daraja.* TO 'daraja'@'localhost';
GRANT ALL PRIVILEGES ON test_daraja.* TO 'daraja'@'localhost';
FLUSH PRIVILEGES;
SQL

# 3. Python deps via uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # if not installed
uv sync

# 4. App config
cp .env.example .env
# Edit .env: at minimum set SECRET_KEY and WEBHOOK_HMAC_SECRET to real values.

# 5. Migrations + superuser
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

## Run

```bash
uv run python manage.py runserver
```

API is at `http://127.0.0.1:8000/api/`. Admin at `http://127.0.0.1:8000/admin/`.

## Tests

```bash
uv run pytest
```

## End-to-end sanity check

This bash snippet exercises the full happy path. Run with the dev server on port 8000.

```bash
set -e

API=http://127.0.0.1:8000/api
PHONE="+255700000777"
PASSWORD="pw-sanity-1234"
WEBHOOK_SECRET="dev-webhook-secret-change-me"  # match your .env

# 1. Register
curl -s -X POST "$API/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\":\"$PHONE\",\"password\":\"$PASSWORD\"}" > /dev/null

# 2. Login → JWT
ACCESS=$(curl -s -X POST "$API/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\":\"$PHONE\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access'])")

# 3. Add meter
METER_ID=$(curl -s -X POST "$API/meters/" \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d '{"meter_number":"0100007777","label":"Sanity"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 4. Initiate
INIT=$(curl -s -X POST "$API/transactions/initiate/" \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d "{\"meter_id\":\"$METER_ID\",\"amount\":\"5000\"}")
CN=$(echo "$INIT" | python3 -c "import sys,json;print(json.load(sys.stdin)['control_number'])")
TXN_ID=$(echo "$INIT" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "Control number: $CN"

# 5. Webhook with HMAC
BODY=$(printf '{"control_number":"%s","amount":"5000","provider_reference":"sanity-ref","status":"paid"}' "$CN")
SIG=$(python3 -c "import hmac,hashlib,sys;print('sha256='+hmac.new(b'$WEBHOOK_SECRET', b'''$BODY''', hashlib.sha256).hexdigest())")

curl -s -X POST "$API/webhooks/payment/" \
  -H "Content-Type: application/json" -H "X-Signature: $SIG" \
  -d "$BODY"
echo

# 6. Confirm token visible to owner
curl -s "$API/transactions/$TXN_ID/" -H "Authorization: Bearer $ACCESS"
echo
```

You should see `status: "paid"` and a non-empty `token.value`. The `runserver` console will log the SMS line from `ConsoleSmsProvider`.

## Architecture seams (for upcoming work)

- `payments/token_logic.py` — `TokenStrategy` interface. Task 3 adds `HmacTokenStrategy`.
- `payments/sms.py` — `SmsProvider` interface. Task 4 adds Beem / Twilio / Africa's Talking.
- `payments/views.py:PaymentWebhookView` — task 2 updates the payload schema parsing to match the real provider.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README with setup and end-to-end sanity check"
```

- [ ] **Step 3: Final whole-suite run**

```bash
uv run pytest -v
```

Confirm green. Now the scaffold is ready for the user's tasks 2–5.

---

## Verification gate (run before claiming the scaffold is done)

- [ ] `uv run python manage.py check` — clean
- [ ] `uv run python manage.py makemigrations --check --dry-run` — no missing migrations
- [ ] `uv run pytest -v` — all green
- [ ] Manual sanity check from README runs end-to-end against `runserver`
- [ ] `git log --oneline` shows one commit per task (15 commits + the design-doc commit)
