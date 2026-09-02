"""
============================================================
MARKETPULSE - DJANGO SETTINGS
============================================================

Framework mapping:
This file is the central configuration file for the MarketPulse project.

It connects:
- Django applications
- PostgreSQL / Neon database
- Local SQLite fallback
- Django REST Framework API
- React CORS configuration
- Bootstrap 5
- Static files and WhiteNoise
- Celery and Redis
- Optional MATLAB execution
- Alpaca market-data integration
- Authentication and security settings

The main URL configuration is located in:
marketpulse/urls.py

The custom user model is located in:
accounts/models.py

Environment variables are loaded from:
.env
============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

from pathlib import Path

import dj_database_url
from decouple import config


# ============================================================
# 2. BASE DIRECTORY
# ============================================================

# BASE_DIR points to the root MarketPulse project folder.
# Other paths such as templates, static files and MATLAB scripts
# are built relative to this location.
BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# 3. SECURITY SETTINGS
# ============================================================

# SECRET_KEY is used by Django for cryptographic signing,
# sessions, CSRF protection and other security functionality.
#
# The real production value should be stored in .env locally
# and in Render Environment Variables when deployed.
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-local-only-change-me",
)


# DEBUG controls whether detailed Django error pages are displayed.
#
# Local .env:
# DEBUG=True
#
# Render:
# DEBUG=False
DEBUG = config(
    "DEBUG",
    default=False,
    cast=bool,
)


# ALLOWED_HOSTS controls which hostnames Django is allowed to serve.
#
# Local:
# localhost
# 127.0.0.1
#
# Render:
# your-project-name.onrender.com
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda value: [
        host.strip()
        for host in value.split(",")
        if host.strip()
    ],
)


# CSRF_TRUSTED_ORIGINS tells Django which origins are trusted
# when processing secure POST requests.
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8000,http://127.0.0.1:8000",
    cast=lambda value: [
        origin.strip()
        for origin in value.split(",")
        if origin.strip()
    ],
)


# ============================================================
# 4. INSTALLED DJANGO APPLICATIONS
# ============================================================

# INSTALLED_APPS tells Django which applications are part
# of the MarketPulse project.
#
# Framework interaction:
#
# accounts
#     -> authentication and profiles
#
# core
#     -> shared market data and alerts
#
# data_management
#     -> Yahoo Finance historical imports
#     -> Alpaca market-data service
#
# strategy_builder
#     -> strategies, IF/THEN rules and backtesting
#
# risk_management
#     -> risk calculations
#
# analysis_tools
#     -> overfitting, regime and stress analysis
#
# api
#     -> REST API endpoints for React and Alpaca integration
INSTALLED_APPS = [

    # --------------------------------------------------------
    # Django built-in applications
    # --------------------------------------------------------

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # --------------------------------------------------------
    # Third-party applications
    # --------------------------------------------------------

    "rest_framework",

    "corsheaders",

    # IMPORTANT:
    # django-bootstrap5 installs the Python module
    # called django_bootstrap5, NOT bootstrap5.
    "django_bootstrap5",

    # --------------------------------------------------------
    # MarketPulse applications
    # --------------------------------------------------------

    "accounts",
    "core",
    "data_management",
    "strategy_builder",
    "risk_management",
    "analysis_tools",
    "api",
]


# ============================================================
# 5. DJANGO MIDDLEWARE
# ============================================================

# Middleware processes requests before they reach views
# and processes responses before they return to the browser.
MIDDLEWARE = [

    # Django security middleware
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise serves static files in production.
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # CORS middleware allows the React frontend to communicate
    # with the Django REST API.
    #
    # It should appear before CommonMiddleware.
    "corsheaders.middleware.CorsMiddleware",

    # Session management
    "django.contrib.sessions.middleware.SessionMiddleware",

    # General request/response handling
    "django.middleware.common.CommonMiddleware",

    # CSRF protection
    "django.middleware.csrf.CsrfViewMiddleware",

    # Authentication
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # Django messages
    "django.contrib.messages.middleware.MessageMiddleware",

    # Protection against clickjacking
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# 6. ROOT URL CONFIGURATION
# ============================================================

# Django starts URL routing from marketpulse/urls.py.
ROOT_URLCONF = "marketpulse.urls"


# ============================================================
# 7. TEMPLATE CONFIGURATION
# ============================================================

# Django searches the main templates/ directory as well
# as templates stored inside individual Django applications.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [

                # Gives templates access to request.
                "django.template.context_processors.request",

                # Gives templates access to user authentication.
                "django.contrib.auth.context_processors.auth",

                # Gives templates access to Django messages.
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================================================
# 8. WSGI AND ASGI CONFIGURATION
# ============================================================

# WSGI is used by Gunicorn when MarketPulse is deployed
# to Render.
WSGI_APPLICATION = "marketpulse.wsgi.application"


# ASGI is available for future asynchronous functionality,
# such as WebSockets.
ASGI_APPLICATION = "marketpulse.asgi.application"


# ============================================================
# 9. DATABASE CONFIGURATION
# ============================================================

# DATABASE_URL is read from .env locally or from Render.
#
# Production example:
#
# DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
#
# When DATABASE_URL exists:
#     MarketPulse uses PostgreSQL / Neon.
#
# When DATABASE_URL is blank:
#     MarketPulse uses local SQLite so the project can still
#     run immediately for development and lecturer demonstrations.
DATABASE_URL = config(
    "DATABASE_URL",
    default="",
).strip()


if DATABASE_URL:

    # --------------------------------------------------------
    # PostgreSQL / Neon Database
    # --------------------------------------------------------

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,

            # Keeps database connections available for reuse.
            conn_max_age=600,

            # Checks that reused connections are still healthy.
            conn_health_checks=True,
        )
    }

else:

    # --------------------------------------------------------
    # Local SQLite Development Database
    # --------------------------------------------------------

    # This fallback allows MarketPulse to run locally even
    # when PostgreSQL or Neon has not yet been configured.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ============================================================
# 10. CUSTOM USER MODEL
# ============================================================

# MarketPulse uses the custom User model defined inside:
#
# accounts/models.py
AUTH_USER_MODEL = "accounts.User"


# ============================================================
# 11. PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        "NAME":
        "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },

    {
        "NAME":
        "django.contrib.auth.password_validation."
        "MinimumLengthValidator",
    },

    {
        "NAME":
        "django.contrib.auth.password_validation."
        "CommonPasswordValidator",
    },

    {
        "NAME":
        "django.contrib.auth.password_validation."
        "NumericPasswordValidator",
    },
]


# ============================================================
# 12. LOGIN AND LOGOUT CONFIGURATION
# ============================================================

# Unauthenticated users are redirected here when
# @login_required is used.
LOGIN_URL = "accounts:login"


# Successful login redirects users to the MarketPulse dashboard.
LOGIN_REDIRECT_URL = "dashboard"


# Successful logout redirects users to the public homepage.
LOGOUT_REDIRECT_URL = "home"


# ============================================================
# 13. LANGUAGE AND TIMEZONE
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Zurich"

USE_I18N = True

USE_TZ = True


# ============================================================
# 14. STATIC FILE CONFIGURATION
# ============================================================

# URL used by browsers to request CSS, JavaScript and images.
STATIC_URL = "/static/"


# collectstatic places production assets here.
STATIC_ROOT = BASE_DIR / "staticfiles"


# Django also looks inside the main static/ directory.
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# WhiteNoise serves static assets when deployed.
STORAGES = {

    "default": {
        "BACKEND":
        "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND":
        "whitenoise.storage."
        "CompressedManifestStaticFilesStorage",
    },
}


# ============================================================
# 15. DEFAULT DATABASE PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# 16. DJANGO REST FRAMEWORK
# ============================================================

# Django REST Framework supplies API endpoints used
# by the React frontend.
REST_FRAMEWORK = {

    "DEFAULT_AUTHENTICATION_CLASSES": [

        "rest_framework.authentication."
        "SessionAuthentication",

        "rest_framework.authentication."
        "BasicAuthentication",
    ],

    "DEFAULT_PERMISSION_CLASSES": [

        "rest_framework.permissions."
        "IsAuthenticatedOrReadOnly",
    ],
}


# ============================================================
# 17. REACT / CORS CONFIGURATION
# ============================================================

# During React development, Vite normally runs on:
#
# http://localhost:5173
#
# django-cors-headers allows that frontend to call
# the Django REST API.
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173",
    cast=lambda value: [
        origin.strip()
        for origin in value.split(",")
        if origin.strip()
    ],
)


# Allows authenticated requests to include cookies/session data.
CORS_ALLOW_CREDENTIALS = True


# ============================================================
# 18. CELERY AND REDIS CONFIGURATION
# ============================================================

# Celery handles background jobs such as:
#
# - market-data imports
# - long-running analysis
# - future automated strategy monitoring
#
# For normal local testing it can remain disabled.
USE_CELERY = config(
    "USE_CELERY",
    default=False,
    cast=bool,
)


# Redis acts as the Celery message broker.
CELERY_BROKER_URL = config(
    "REDIS_URL",
    default="redis://localhost:6379/0",
)


# Celery stores task results in the same Redis service.
CELERY_RESULT_BACKEND = CELERY_BROKER_URL


# Celery uses JSON for task messages.
CELERY_ACCEPT_CONTENT = [
    "json",
]

CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = TIME_ZONE


# ============================================================
# 19. CELERY BEAT SCHEDULE
# ============================================================

# This configuration is used only when Celery Beat is started.
#
# It expects this task to exist:
#
# strategy_builder/tasks.py
# -> monitor_active_strategies
#
# If you have not created that task yet, this setting does not
# affect normal `python manage.py runserver`.
CELERY_BEAT_SCHEDULE = {

    "monitor-strategies-hourly": {

        "task":
        "strategy_builder.tasks."
        "monitor_active_strategies",

        # Run once per hour.
        "schedule": 3600.0,
    },
}


# ============================================================
# 20. MATLAB CONFIGURATION
# ============================================================

# MATLAB is optional.
#
# Django does not need MATLAB in order to start.
MATLAB_ENABLED = config(
    "MATLAB_ENABLED",
    default=False,
    cast=bool,
)


# Command used to launch MATLAB if MATLAB integration is enabled.
MATLAB_COMMAND = config(
    "MATLAB_COMMAND",
    default="matlab",
)


# Directory containing MarketPulse MATLAB scripts.
MATLAB_DIR = BASE_DIR / "matlab"


# ============================================================
# 21. EMAIL CONFIGURATION
# ============================================================

# Development emails are printed to the terminal instead
# of being sent externally.
EMAIL_BACKEND = (
    "django.core.mail.backends."
    "console.EmailBackend"
)


# ============================================================
# 22. DJANGO-BOOTSTRAP5 CONFIGURATION
# ============================================================

# The installed Python package is:
#
# django-bootstrap5
#
# The Django application/module name is:
#
# django_bootstrap5
#
# Templates should therefore use:
#
# {% load django_bootstrap5 %}
BOOTSTRAP5 = {

    "css_url":
    "https://cdn.jsdelivr.net/npm/"
    "bootstrap@5.3.3/dist/css/"
    "bootstrap.min.css",

    "javascript_url":
    "https://cdn.jsdelivr.net/npm/"
    "bootstrap@5.3.3/dist/js/"
    "bootstrap.bundle.min.js",
}


# ============================================================
# 23. ALPACA MARKET DATA CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# PURPOSE
# ------------------------------------------------------------
#
# MarketPulse uses Alpaca as an external market-data provider.
#
# Planned architecture:
#
# Browser / React / Django Template
#           ↓
# MarketPulse API
#           ↓
# Django Alpaca Service Layer
#           ↓
# Alpaca REST API
#
#
# Alpaca will provide:
#
# - searchable US-equity asset universe
# - stock names
# - exchange information
# - tradability information
# - fractional-trading information
# - shortability information
# - latest trade
# - latest bid
# - latest ask
# - bid/ask spread
# - current daily market information
#
#
# IMPORTANT SECURITY RULE:
#
# The API key and API secret must NEVER be placed directly
# inside this settings.py file.
#
# They are read from:
#
# .env
#
# locally, and from Render Environment Variables in production.
#
# They must never be sent to:
#
# - templates
# - JavaScript
# - React
# - GitHub
# - API responses
#
# Only the Django backend communicates directly with Alpaca.
# ------------------------------------------------------------


# ============================================================
# 23.1 ALPACA API KEY ID
# ============================================================

ALPACA_API_KEY_ID = config(
    "ALPACA_API_KEY_ID",
    default="PKNUISCSVQQPNLFD07NDPVGT4",
).strip()


# ============================================================
# 23.2 ALPACA API SECRET KEY
# ============================================================

ALPACA_API_SECRET_KEY = config(
    "ALPACA_API_SECRET_KEY",
    default="DGHo6depce7e8xXCGBnJfo8pDnoNzzfFi9oivWhm6bDW",
).strip()


# ============================================================
# 23.3 ALPACA PAPER TRADING BASE URL
# ============================================================

# IMPORTANT:
#
# Do NOT add "/v2" here.
#
# Correct:
#
# https://paper-api.alpaca.markets
#
# The MarketPulse service layer will add paths such as:
#
# /v2/assets
#
# /v2/assets/AAPL
#
# This produces:
#
# https://paper-api.alpaca.markets/v2/assets
#
# instead of accidentally producing:
#
# https://paper-api.alpaca.markets/v2/v2/assets
ALPACA_TRADING_BASE_URL = config(
    "ALPACA_TRADING_BASE_URL",
    default="https://paper-api.alpaca.markets",
).rstrip("/")


# ============================================================
# 23.4 ALPACA MARKET DATA BASE URL
# ============================================================

# Market-data endpoints use a separate Alpaca hostname.
#
# Example endpoint:
#
# https://data.alpaca.markets/v2/stocks/AAPL/snapshot
ALPACA_DATA_BASE_URL = config(
    "ALPACA_DATA_BASE_URL",
    default="https://data.alpaca.markets",
).rstrip("/")


# ============================================================
# 23.5 ALPACA STOCK DATA FEED
# ============================================================

# IEX is used as the default MarketPulse stock feed.
#
# Alpaca's free market-data access generally provides the
# IEX exchange feed.
#
# If the account later has the appropriate consolidated
# market-data entitlement, this can be changed in .env.
#
# Example:
#
# ALPACA_DATA_FEED=sip
ALPACA_DATA_FEED = config(
    "ALPACA_DATA_FEED",
    default="iex",
).strip().lower()


# ============================================================
# 23.6 ALPACA REQUEST TIMEOUT
# ============================================================

# External API calls should never be allowed to wait forever.
#
# The Alpaca service layer can use this setting when performing
# requests.
ALPACA_REQUEST_TIMEOUT = config(
    "ALPACA_REQUEST_TIMEOUT",
    default=8,
    cast=int,
)


# ============================================================
# 23.7 ALPACA ASSET CACHE
# ============================================================

# Alpaca contains thousands of assets.
#
# MarketPulse should NOT download the complete asset list every
# time somebody enters one character into the Risk search box.
#
# The asset catalogue can therefore be cached for 30 minutes.
ALPACA_ASSET_CACHE_SECONDS = config(
    "ALPACA_ASSET_CACHE_SECONDS",
    default=1800,
    cast=int,
)


# ============================================================
# 23.8 ALPACA SNAPSHOT CACHE
# ============================================================

# Latest stock snapshots are much more time-sensitive than
# the asset catalogue.
#
# A short cache reduces unnecessary API calls while keeping
# the Risk interface reasonably current.
ALPACA_SNAPSHOT_CACHE_SECONDS = config(
    "ALPACA_SNAPSHOT_CACHE_SECONDS",
    default=15,
    cast=int,
)