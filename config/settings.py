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
    "rest_framework_simplejwt.token_blacklist",
    "accounts",
    "meters",
    "payments",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "login": os.environ.get("LOGIN_RATE_LIMIT", "5/min"),
        "initiate": os.environ.get("INITIATE_RATE_LIMIT", "10/min"),
    },
}

AUTH_USER_MODEL = "accounts.User"

# Daraja config
WEBHOOK_HMAC_SECRET = os.environ["WEBHOOK_HMAC_SECRET"]
TOKEN_STRATEGY = os.environ.get("TOKEN_STRATEGY", "simple")
TOKEN_SIMPLE_MULTIPLIER = int(os.environ.get("TOKEN_SIMPLE_MULTIPLIER", "1357"))
TOKEN_HMAC_SECRET = os.environ.get("TOKEN_HMAC_SECRET", "")
TOKEN_HMAC_DIGITS = int(os.environ.get("TOKEN_HMAC_DIGITS", "12"))
SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "console")
MALIPOPAY_API_URL = os.environ.get("MALIPOPAY_API_URL", "https://core-prod.malipopay.co.tz/api/v1/sms")
MALIPOPAY_API_TOKEN = os.environ.get("MALIPOPAY_API_TOKEN", "")
MALIPOPAY_SENDER = os.environ.get("MALIPOPAY_SENDER", "Daraja")
MALIPOPAY_OPERATOR_ID = os.environ.get("MALIPOPAY_OPERATOR_ID", "")
TRANSACTION_TTL_MINUTES = int(os.environ.get("TRANSACTION_TTL_MINUTES", "30"))

SWAHILIES_API_URL = os.environ.get("SWAHILIES_API_URL", "https://swahiliesapi.invict.site/Api")
SWAHILIES_API_KEY = os.environ.get("SWAHILIES_API_KEY", "")
SWAHILIES_IS_LIVE = os.environ.get("SWAHILIES_IS_LIVE", "False") == "True"
SWAHILIES_WEBHOOK_URL = os.environ.get("SWAHILIES_WEBHOOK_URL", "")

CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
]
