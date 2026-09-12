"""
============================================================
MARKETPULSE - DJANGO SETTINGS
============================================================

Framework mapping:

This file is the central configuration file for MarketPulse.

It connects:

- Django applications
- PostgreSQL / Neon database
- Local SQLite fallback
- Django REST Framework
- React / CORS configuration
- Bootstrap 5
- Static files and WhiteNoise
- Optional Celery and Redis
- Optional MATLAB execution
- Alpaca market-data integration
- Authentication
- Password recovery email delivery
- Render production deployment
- Security settings


PROJECT ROUTING:

marketpulse/urls.py
        ↓
Django applications


CUSTOM USER MODEL:

accounts/models.py


PASSWORD RECOVERY:

Login
    ↓
Forgot Password
    ↓
Django PasswordResetView
    ↓
Django-Anymail
    ↓
Mailjet HTTPS API
    ↓
Reset Email
    ↓
Secure Django Reset Token
    ↓
New Password


ENVIRONMENT VARIABLES:

Local development:
    .env

Production:
    Render Environment Variables


IMPORTANT SECURITY RULE:

Real credentials must never be stored directly
inside this file or committed to GitHub.

============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

# os is used to read environment variables automatically
# supplied by Render, including RENDER_EXTERNAL_HOSTNAME.
import os

from pathlib import Path

import dj_database_url
from decouple import config


# ============================================================
# 2. BASE DIRECTORY
# ============================================================

# BASE_DIR points to the main MarketPulse project folder.
#
# Example structure:
#
# MarketPulse/
#     manage.py
#     marketpulse/
#     templates/
#     static/
#     accounts/
#     data_management/
#     strategy_builder/
#     risk_management/
#
BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# 3. SECURITY SETTINGS
# ============================================================


# ============================================================
# 3.1 DJANGO SECRET KEY
# ============================================================

# Django uses SECRET_KEY for:
#
# - cryptographic signing
# - sessions
# - CSRF protection
# - password-reset security
# - other security functionality
#
#
# LOCAL:
#
# Store it inside:
#
# .env
#
#
# PRODUCTION:
#
# Store it inside:
#
# Render
#     ↓
# Environment
#     ↓
# Environment Variables
#
#
# IMPORTANT:
#
# This is NOT the Alpaca API secret.
#
# It is also NOT the Mailjet secret key.
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-local-only-change-me",
)


# ============================================================
# 3.2 DEBUG MODE
# ============================================================

# Local development:
#
# DEBUG=True
#
# Render production:
#
# DEBUG=False
#
#
# DEBUG must be False in production because otherwise
# Django can expose detailed application information
# through error pages.
DEBUG = config(
    "DEBUG",
    default=False,
    cast=bool,
)


# ============================================================
# 3.3 ALLOWED HOSTS
# ============================================================

# ALLOWED_HOSTS tells Django which hostnames are allowed
# to send requests to MarketPulse.
#
#
# LOCAL EXAMPLES:
#
# localhost
# 127.0.0.1
#
#
# RENDER EXAMPLE:
#
# marketpulse-is-a-web-platform-that.onrender.com
#
#
# IMPORTANT:
#
# ALLOWED_HOSTS contains hostnames only.
#
# Correct:
#
# marketpulse-is-a-web-platform-that.onrender.com
#
# Incorrect:
#
# https://marketpulse-is-a-web-platform-that.onrender.com
#
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda value: [
        host.strip()
        for host in value.split(",")
        if host.strip()
    ],
)


# ============================================================
# 3.4 CSRF TRUSTED ORIGINS
# ============================================================

# CSRF_TRUSTED_ORIGINS tells Django which web origins are
# trusted when forms send POST requests.
#
#
# Unlike ALLOWED_HOSTS, these values MUST include:
#
# http://
#
# or:
#
# https://
#
#
# LOCAL:
#
# http://localhost:8000
# http://127.0.0.1:8000
#
#
# RENDER:
#
# https://marketpulse-is-a-web-platform-that.onrender.com
#
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default=(
        "http://localhost:8000,"
        "http://127.0.0.1:8000"
    ),
    cast=lambda value: [
        origin.strip()
        for origin in value.split(",")
        if origin.strip()
    ],
)


# ============================================================
# 3.5 RENDER PRODUCTION HOST CONFIGURATION
# ============================================================

# Render automatically provides:
#
# RENDER_EXTERNAL_HOSTNAME
#
# when the application is deployed.
#
#
# Example:
#
# marketpulse-is-a-web-platform-that.onrender.com
#
#
# This section automatically adds that hostname to:
#
# ALLOWED_HOSTS
#
# and automatically adds the HTTPS origin to:
#
# CSRF_TRUSTED_ORIGINS
#
#
# This helps prevent:
#
# Bad Request (400)
#
# caused by Django rejecting the Render hostname.

RENDER_EXTERNAL_HOSTNAME = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME",
    "",
).strip()


if RENDER_EXTERNAL_HOSTNAME:

    # --------------------------------------------------------
    # Add Render hostname to ALLOWED_HOSTS
    # --------------------------------------------------------

    if (
        RENDER_EXTERNAL_HOSTNAME
        not in ALLOWED_HOSTS
    ):

        ALLOWED_HOSTS.append(
            RENDER_EXTERNAL_HOSTNAME
        )


    # --------------------------------------------------------
    # Build HTTPS origin for CSRF protection
    # --------------------------------------------------------

    render_origin = (
        f"https://{RENDER_EXTERNAL_HOSTNAME}"
    )


    # --------------------------------------------------------
    # Add Render origin to trusted CSRF origins
    # --------------------------------------------------------

    if (
        render_origin
        not in CSRF_TRUSTED_ORIGINS
    ):

        CSRF_TRUSTED_ORIGINS.append(
            render_origin
        )


# ============================================================
# 3.6 RENDER HTTPS PROXY
# ============================================================

# Render terminates HTTPS before forwarding the request
# to the Django application.
#
# This setting tells Django to trust Render's
# X-Forwarded-Proto header when determining whether
# the original browser request used HTTPS.
#
# This is also important when Django creates absolute
# password-reset links for email messages.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# 3.7 PRODUCTION COOKIE SECURITY
# ============================================================

# Secure cookies should be enabled in production.
#
# They remain disabled during local DEBUG=True development
# so localhost still works normally.
SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG


# ============================================================
# 3.8 BASIC BROWSER SECURITY
# ============================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"


# ============================================================
# 4. INSTALLED DJANGO APPLICATIONS
# ============================================================

# INSTALLED_APPS tells Django which applications form
# part of MarketPulse.
#
#
# accounts
#     ↓
# Registration
# Login
# Logout
# User profile
# Password recovery
#
#
# core
#     ↓
# Shared MarketData
# Alerts
# Alert rules
# Dashboard data
#
#
# data_management
#     ↓
# Alpaca historical imports
# Historical OHLCV storage
# Market Condition workflow
#
#
# strategy_builder
#     ↓
# Strategy & Model Library
# User strategies
# Backtesting
# Strategy robustness
#
#
# risk_management
#     ↓
# Trade risk planning
# Position sizing
# Stop-loss calculations
#
#
# analysis_tools
#     ↓
# Internal analytics engine
# Market regime analysis
# Robustness / overfitting analysis
#
#
# api
#     ↓
# Django REST Framework API
# Dashboard market information
# Alpaca integration
#
#
# anymail
#     ↓
# Connects Django's email framework to Mailjet
# through an HTTPS API.
#
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

    "django_bootstrap5",

    # Django-Anymail connects Django's normal email system
    # to transactional email providers such as Mailjet.
    "anymail",


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

# Middleware handles requests before they reach a Django view
# and responses before they return to the browser.
MIDDLEWARE = [

    # --------------------------------------------------------
    # Security
    # --------------------------------------------------------

    "django.middleware.security.SecurityMiddleware",


    # --------------------------------------------------------
    # Production static files
    # --------------------------------------------------------

    "whitenoise.middleware.WhiteNoiseMiddleware",


    # --------------------------------------------------------
    # React / API CORS support
    # --------------------------------------------------------

    # Must appear before CommonMiddleware.
    "corsheaders.middleware.CorsMiddleware",


    # --------------------------------------------------------
    # Sessions
    # --------------------------------------------------------

    "django.contrib.sessions.middleware.SessionMiddleware",


    # --------------------------------------------------------
    # General Django request processing
    # --------------------------------------------------------

    "django.middleware.common.CommonMiddleware",


    # --------------------------------------------------------
    # Cross-Site Request Forgery protection
    # --------------------------------------------------------

    "django.middleware.csrf.CsrfViewMiddleware",


    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    "django.contrib.auth.middleware.AuthenticationMiddleware",


    # --------------------------------------------------------
    # Django messages
    # --------------------------------------------------------

    "django.contrib.messages.middleware.MessageMiddleware",


    # --------------------------------------------------------
    # Clickjacking protection
    # --------------------------------------------------------

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# 6. ROOT URL CONFIGURATION
# ============================================================

# All incoming Django URLs begin routing from:
#
# marketpulse/urls.py
ROOT_URLCONF = "marketpulse.urls"


# ============================================================
# 7. TEMPLATE CONFIGURATION
# ============================================================

TEMPLATES = [

    {

        "BACKEND":
            "django.template.backends.django.DjangoTemplates",


        # ----------------------------------------------------
        # Main project templates directory
        # ----------------------------------------------------

        "DIRS": [

            BASE_DIR / "templates",

        ],


        # ----------------------------------------------------
        # Also search application templates directories
        # ----------------------------------------------------

        "APP_DIRS":
            True,


        # ----------------------------------------------------
        # Template context processors
        # ----------------------------------------------------

        "OPTIONS": {

            "context_processors": [

                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",

            ],

        },

    },

]


# ============================================================
# 8. WSGI AND ASGI CONFIGURATION
# ============================================================

# Render / Gunicorn uses WSGI.
WSGI_APPLICATION = "marketpulse.wsgi.application"


# ASGI remains available for future asynchronous
# functionality such as WebSockets.
ASGI_APPLICATION = "marketpulse.asgi.application"


# ============================================================
# 9. DATABASE CONFIGURATION
# ============================================================

# DATABASE_URL is supplied from:
#
# Local:
#     .env
#
# Production:
#     Render Environment Variables
#
#
# When DATABASE_URL exists:
#
#     Neon PostgreSQL
#
#
# When DATABASE_URL does not exist:
#
#     Local SQLite fallback
#
#
# The production database password must never be stored
# directly inside settings.py.

DATABASE_URL = config(
    "DATABASE_URL",
    default="",
).strip()


if DATABASE_URL:

    # ========================================================
    # NEON / POSTGRESQL
    # ========================================================

    DATABASES = {

        "default":
            dj_database_url.parse(

                DATABASE_URL,

                # Reuse database connections.
                conn_max_age=600,

                # Test whether reused connections remain valid.
                conn_health_checks=True,

            )

    }


else:

    # ========================================================
    # LOCAL SQLITE FALLBACK
    # ========================================================

    DATABASES = {

        "default": {

            "ENGINE":
                "django.db.backends.sqlite3",

            "NAME":
                BASE_DIR / "db.sqlite3",

        }

    }


# ============================================================
# 10. CUSTOM USER MODEL
# ============================================================

# MarketPulse's custom user model lives inside:
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

# @login_required sends unauthenticated users here.
LOGIN_URL = "accounts:login"


# Successful login.
LOGIN_REDIRECT_URL = "dashboard"


# Successful logout.
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

# URL used by the browser.
STATIC_URL = "/static/"


# Render collectstatic output directory.
STATIC_ROOT = BASE_DIR / "staticfiles"


# Main development static directory.
STATICFILES_DIRS = [

    BASE_DIR / "static",

]


# ============================================================
# 14.1 STORAGE / WHITENOISE
# ============================================================

STORAGES = {

    # --------------------------------------------------------
    # Normal uploaded/local files
    # --------------------------------------------------------

    "default": {

        "BACKEND":
            "django.core.files.storage.FileSystemStorage",

    },


    # --------------------------------------------------------
    # Production static assets
    # --------------------------------------------------------

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

REST_FRAMEWORK = {

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    "DEFAULT_AUTHENTICATION_CLASSES": [

        "rest_framework.authentication."
        "SessionAuthentication",

        "rest_framework.authentication."
        "BasicAuthentication",

    ],


    # --------------------------------------------------------
    # Permissions
    # --------------------------------------------------------

    "DEFAULT_PERMISSION_CLASSES": [

        "rest_framework.permissions."
        "IsAuthenticatedOrReadOnly",

    ],

}


# ============================================================
# 17. REACT / CORS CONFIGURATION
# ============================================================

# React / Vite normally runs locally on:
#
# http://localhost:5173
#
#
# This configuration allows the React frontend to communicate
# with the Django API during development.
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173",
    cast=lambda value: [
        origin.strip()
        for origin in value.split(",")
        if origin.strip()
    ],
)


# Allows session cookies / authenticated requests.
CORS_ALLOW_CREDENTIALS = True


# ============================================================
# 18. CELERY AND REDIS CONFIGURATION
# ============================================================

# Celery is currently optional.
#
# When:
#
# USE_CELERY=False
#
# MarketPulse performs supported jobs synchronously.
#
#
# Possible future uses:
#
# - automated monitoring
# - long-running market-data jobs
# - scheduled strategy analysis

USE_CELERY = config(
    "USE_CELERY",
    default=False,
    cast=bool,
)


# Redis message broker.
CELERY_BROKER_URL = config(
    "REDIS_URL",
    default="redis://localhost:6379/0",
)


# Celery result backend.
CELERY_RESULT_BACKEND = (
    CELERY_BROKER_URL
)


# JSON task messages.
CELERY_ACCEPT_CONTENT = [
    "json",
]


CELERY_TASK_SERIALIZER = "json"


CELERY_RESULT_SERIALIZER = "json"


CELERY_TIMEZONE = TIME_ZONE


# ============================================================
# 19. CELERY BEAT SCHEDULE
# ============================================================

# This schedule has no effect unless Celery Beat and
# USE_CELERY are enabled.
CELERY_BEAT_SCHEDULE = {

    "monitor-strategies-hourly": {

        "task":
            "strategy_builder.tasks."
            "monitor_active_strategies",

        "schedule":
            3600.0,

    },

}


# ============================================================
# 20. MATLAB CONFIGURATION
# ============================================================

# MATLAB integration remains optional.
MATLAB_ENABLED = config(
    "MATLAB_ENABLED",
    default=False,
    cast=bool,
)


MATLAB_COMMAND = config(
    "MATLAB_COMMAND",
    default="matlab",
)


MATLAB_DIR = BASE_DIR / "matlab"


# ============================================================
# 21. EMAIL / PASSWORD RECOVERY CONFIGURATION
# ============================================================

# ============================================================
# EMAIL ARCHITECTURE
# ============================================================
#
# MarketPulse User
#       ↓
# Forgot Password
#       ↓
# Django PasswordResetView
#       ↓
# Django Email Framework
#       ↓
# Django-Anymail
#       ↓
# Mailjet HTTPS API
#       ↓
# User Email Inbox
#
#
# IMPORTANT:
#
# MarketPulse does NOT store email provider credentials
# directly inside settings.py.
#
#
# LOCAL:
#
# .env
#
#
# PRODUCTION:
#
# Render
#     ↓
# Environment
#     ↓
# Environment Variables
#
#
# REQUIRED PRODUCTION VARIABLES:
#
# MAILJET_API_KEY
# MAILJET_SECRET_KEY
# DEFAULT_FROM_EMAIL
#
#
# Example:
#
# DEFAULT_FROM_EMAIL=MarketPulse <your-email@example.com>
#
#
# The sender email must first be verified in Mailjet.
#
#
# IMPORTANT:
#
# Django's password-reset functionality creates and validates
# the secure reset token.
#
# Mailjet only delivers the email.
#
# Mailjet never receives or changes the user's password.
# ============================================================


# ============================================================
# 21.1 MAILJET API KEY
# ============================================================

MAILJET_API_KEY = config(
    "MAILJET_API_KEY",
    default="",
).strip()


# ============================================================
# 21.2 MAILJET SECRET KEY
# ============================================================

MAILJET_SECRET_KEY = config(
    "MAILJET_SECRET_KEY",
    default="",
).strip()


# ============================================================
# 21.3 MAILJET CONFIGURATION STATUS
# ============================================================

# This boolean tells MarketPulse whether both Mailjet
# credentials are available.
#
# It does not reveal either credential.
MAILJET_CONFIGURED = bool(

    MAILJET_API_KEY

    and

    MAILJET_SECRET_KEY

)


# ============================================================
# 21.4 ANYMAIL CONFIGURATION
# ============================================================

# Django-Anymail acts as the bridge between Django's normal
# email framework and the Mailjet HTTPS API.
#
# This means Django code can continue to use:
#
# django.core.mail
#
# and Django's built-in authentication views can send email
# normally without needing Mailjet-specific code.
ANYMAIL = {

    "MAILJET_API_KEY":
        MAILJET_API_KEY,

    "MAILJET_SECRET_KEY":
        MAILJET_SECRET_KEY,

}


# ============================================================
# 21.5 EMAIL BACKEND
# ============================================================

# ------------------------------------------------------------
# PRODUCTION / CONFIGURED ENVIRONMENT
# ------------------------------------------------------------
#
# If the Mailjet credentials are available:
#
# Django
#     ↓
# Anymail
#     ↓
# Mailjet API
#     ↓
# Real email
#
#
# ------------------------------------------------------------
# LOCAL FALLBACK
# ------------------------------------------------------------
#
# If Mailjet credentials are NOT available:
#
# Django
#     ↓
# Console email backend
#     ↓
# Password-reset email appears in the terminal
#
#
# This makes development easier because the password reset
# flow can still be tested locally before Mailjet is configured.

if MAILJET_CONFIGURED:

    EMAIL_BACKEND = (
        "anymail.backends.mailjet."
        "EmailBackend"
    )


else:

    EMAIL_BACKEND = (
        "django.core.mail.backends."
        "console.EmailBackend"
    )


# ============================================================
# 21.6 DEFAULT SENDER EMAIL
# ============================================================

# This sender should match an email address verified inside
# the Mailjet dashboard.
#
#
# LOCAL EXAMPLE:
#
# DEFAULT_FROM_EMAIL=MarketPulse <example@gmail.com>
#
#
# RENDER:
#
# Store the same value as an Environment Variable.
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="MarketPulse <no-reply@example.com>",
)


# Django-generated administrative email can use the
# same sender.
SERVER_EMAIL = DEFAULT_FROM_EMAIL


# ============================================================
# 21.7 PASSWORD RESET TOKEN LIFETIME
# ============================================================

# Number of seconds that a password-reset token remains valid.
#
# 3600 seconds = 1 hour.
#
# The value can be changed later without modifying the
# password-reset views or templates.
PASSWORD_RESET_TIMEOUT = config(
    "PASSWORD_RESET_TIMEOUT",
    default=3600,
    cast=int,
)


# ============================================================
# 21.8 EMAIL SECURITY NOTES
# ============================================================

# Password reset emails should never contain:
#
# - passwords
# - Django SECRET_KEY
# - Mailjet API credentials
# - Alpaca API credentials
#
#
# Django sends only a temporary secure reset URL containing:
#
# - encoded user identifier
# - reset token
#
#
# The user then creates the new password directly through
# MarketPulse.
#
#
# The actual password is handled by Django's authentication
# framework and stored as a secure password hash.


# ============================================================
# 22. DJANGO-BOOTSTRAP5 CONFIGURATION
# ============================================================

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

# MarketPulse uses Alpaca as the external market-data
# provider.
#
#
# ARCHITECTURE:
#
# Browser
#     ↓
# Django Template / JavaScript
#     ↓
# MarketPulse API
#     ↓
# data_management/services/alpaca.py
#     ↓
# Alpaca REST API
#
#
# The browser NEVER receives Alpaca credentials.
#
#
# Alpaca provides:
#
# - Asset search
# - Company information
# - Exchange information
# - Tradability information
# - Fractional-trading information
# - Shortability information
# - Latest trade information
# - Bid / ask information
# - Daily market snapshot
# - Historical market bars
#
#
# CREDENTIAL LOCATION:
#
# Local:
#     .env
#
# Production:
#     Render Environment Variables
#
#
# NEVER:
#
# - settings.py
# - HTML templates
# - JavaScript
# - React source code
# - GitHub repository
# - API responses


# ============================================================
# 23.1 ALPACA API KEY ID
# ============================================================

ALPACA_API_KEY_ID = config(
    "ALPACA_API_KEY_ID",
    default="",
).strip()


# ============================================================
# 23.2 ALPACA API SECRET KEY
# ============================================================

ALPACA_API_SECRET_KEY = config(
    "ALPACA_API_SECRET_KEY",
    default="",
).strip()


# ============================================================
# 23.3 ALPACA CONFIGURATION STATUS
# ============================================================

# True only when both credentials are available.
#
# The boolean can safely be used by backend code.
#
# It does not expose the credentials.
ALPACA_CONFIGURED = bool(

    ALPACA_API_KEY_ID

    and

    ALPACA_API_SECRET_KEY

)


# ============================================================
# 23.4 ALPACA PAPER TRADING BASE URL
# ============================================================

# Do NOT add /v2 here.
#
# Correct:
#
# https://paper-api.alpaca.markets
#
#
# The service layer adds endpoints such as:
#
# /v2/assets
#
# /v2/account
#
ALPACA_TRADING_BASE_URL = config(
    "ALPACA_TRADING_BASE_URL",
    default="https://paper-api.alpaca.markets",
).rstrip("/")


# ============================================================
# 23.5 ALPACA MARKET DATA BASE URL
# ============================================================

# Historical and current market-data endpoints use:
#
# https://data.alpaca.markets
ALPACA_DATA_BASE_URL = config(
    "ALPACA_DATA_BASE_URL",
    default="https://data.alpaca.markets",
).rstrip("/")


# ============================================================
# 23.6 ALPACA MARKET DATA FEED
# ============================================================

# MarketPulse currently uses IEX by default.
ALPACA_DATA_FEED = config(
    "ALPACA_DATA_FEED",
    default="iex",
).strip().lower()


# ============================================================
# 23.7 ALPACA REQUEST TIMEOUT
# ============================================================

# External requests should not wait indefinitely.
ALPACA_REQUEST_TIMEOUT = config(
    "ALPACA_REQUEST_TIMEOUT",
    default=8,
    cast=int,
)


# ============================================================
# 23.8 ALPACA ASSET CACHE
# ============================================================

# Asset metadata changes relatively slowly.
#
# 1800 seconds = 30 minutes.
ALPACA_ASSET_CACHE_SECONDS = config(
    "ALPACA_ASSET_CACHE_SECONDS",
    default=1800,
    cast=int,
)


# ============================================================
# 23.9 ALPACA SNAPSHOT CACHE
# ============================================================

# Current market snapshots are more time-sensitive.
#
# 15 seconds provides a small cache while still giving the
# Dashboard and Risk workspace reasonably current values.
ALPACA_SNAPSHOT_CACHE_SECONDS = config(
    "ALPACA_SNAPSHOT_CACHE_SECONDS",
    default=15,
    cast=int,
)