"""
============================================================
MARKETPULSE - DJANGO SETTINGS
============================================================
PURPOSE:
Configure Django and the services used by MarketPulse.
FRAMEWORK:
Settings → Apps, middleware, URLs, templates and database.
INTEGRATIONS:
Django REST Framework, CORS, Bootstrap, WhiteNoise,
optional Celery/Redis, optional MATLAB, Alpaca and Brevo.
AUTHENTICATION:
Login → Authenticated session → Home or requested next page.
PASSWORD RECOVERY:
Django reset views → Email backend → Reset link → New password.
CONFIGURATION:
Local values can come from .env; deployment values can come
from environment variables.
LECTURE:
Imports, variables, strings, Booleans, lists, dictionaries,
tuples, conditions, comprehensions, lambdas and function calls.
SECURITY:
Keep real credentials outside source code.
============================================================
"""
# ============================================================
# 1. IMPORTS
# ============================================================
import os  # I import operating-system tools for reading process environment variables.
from pathlib import Path  # I import a class for constructing filesystem paths.
import dj_database_url  # I import a package that converts database URLs into Django configuration.
from decouple import config  # I import the configuration reader for environment and file-based values.
# ============================================================
# 2. BASE DIRECTORY
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent  # I find the project directory two levels above this settings file.
# ============================================================
# 3. SECURITY SETTINGS
# ============================================================
# 3.1 DJANGO SECRET KEY
SECRET_KEY = config(  # I read Django's cryptographic signing key.
    "SECRET_KEY",  # I identify the configuration variable.
    default="django-insecure-local-only-change-me",  # I preserve the existing local-only fallback.
)  # I finish reading the secret key.
# 3.2 DEBUG MODE
DEBUG = config(  # I read whether detailed debugging is enabled.
    "DEBUG",  # I identify the configuration variable.
    default=False,  # I default to debugging being disabled.
    cast=bool,  # I ask decouple to convert the configured value into a Boolean.
)  # I finish reading debug mode.
# 3.3 ALLOWED HOSTS
ALLOWED_HOSTS = config(  # I read the hostnames Django may serve.
    "ALLOWED_HOSTS",  # I identify the hostname configuration variable.
    default="localhost,127.0.0.1",  # I preserve the default local hostnames.
    cast=lambda value: [  # I use an anonymous function to convert comma-separated text into a list.
        host.strip()  # I remove spaces around each retained hostname.
        for host in value.split(",")  # I loop over the comma-separated hostname entries.
        if host.strip()  # I exclude entries that become empty after trimming.
    ],  # I finish the list comprehension and cast argument.
)  # I finish reading allowed hosts.
# 3.4 CSRF TRUSTED ORIGINS
CSRF_TRUSTED_ORIGINS = config(  # I read origins trusted for Django's CSRF origin checks.
    "CSRF_TRUSTED_ORIGINS",  # I identify the configuration variable.
    default=(  # I begin the default origin string.
        "http://localhost:8000,"  # I include the localhost origin with its scheme and port.
        "http://127.0.0.1:8000"  # I join this adjacent string to include the loopback origin.
    ),  # I finish the combined default string.
    cast=lambda value: [  # I define a conversion from comma-separated text to a list.
        origin.strip()  # I trim spaces around each retained origin.
        for origin in value.split(",")  # I loop over the configured origins.
        if origin.strip()  # I discard empty entries.
    ],  # I finish the origin list comprehension.
)  # I finish reading trusted origins.
# 3.5 RENDER PRODUCTION HOST CONFIGURATION
RENDER_EXTERNAL_HOSTNAME = os.environ.get(  # I read the hostname directly from the process environment.
    "RENDER_EXTERNAL_HOSTNAME",  # I identify the environment variable.
    "",  # I use an empty string when it is absent.
).strip()  # I remove surrounding spaces from the hostname.
if RENDER_EXTERNAL_HOSTNAME:  # I continue only when the hostname is nonempty.
    if (RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS):  # I check whether the hostname is already allowed.
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)  # I add the hostname without duplicating it.
    render_origin = (f"https://{RENDER_EXTERNAL_HOSTNAME}")  # I use an f-string to build its HTTPS origin.
    if (render_origin not in CSRF_TRUSTED_ORIGINS):  # I check whether the HTTPS origin is already trusted.
        CSRF_TRUSTED_ORIGINS.append(render_origin)  # I add the origin without duplicating it.
# 3.6 HTTPS PROXY HEADER
SECURE_PROXY_SSL_HEADER = (  # I define the proxy header and value Django uses to recognise HTTPS.
    "HTTP_X_FORWARDED_PROTO",  # I specify the request metadata key for the forwarded protocol.
    "https",  # I specify the value that indicates an HTTPS request.
)  # I finish the two-item tuple.
# 3.7 COOKIE SECURITY
SESSION_COOKIE_SECURE = not DEBUG  # I require HTTPS for session cookies when debugging is disabled.
CSRF_COOKIE_SECURE = not DEBUG  # I require HTTPS for CSRF cookies when debugging is disabled.
# 3.8 BASIC BROWSER SECURITY
SECURE_CONTENT_TYPE_NOSNIFF = True  # I enable the response header that discourages content-type sniffing.
X_FRAME_OPTIONS = "DENY"  # I configure the clickjacking header to prevent framing.
# ============================================================
# 4. INSTALLED DJANGO APPLICATIONS
# ============================================================
INSTALLED_APPS = [  # I begin the ordered list of registered applications.
    # 4.1 DJANGO BUILT-IN APPLICATIONS
    "django.contrib.admin",  # I enable Django's administration application.
    "django.contrib.auth",  # I enable authentication and permissions.
    "django.contrib.contenttypes",  # I enable model content-type records.
    "django.contrib.sessions",  # I enable session support.
    "django.contrib.messages",  # I enable temporary user messages.
    "django.contrib.staticfiles",  # I enable static-file discovery and collection.
    # 4.2 THIRD-PARTY APPLICATIONS
    "rest_framework",  # I register Django REST Framework.
    "corsheaders",  # I register cross-origin request support.
    "django_bootstrap5",  # I register Bootstrap template helpers.
    "anymail",  # I register the transactional email integration.
    # 4.3 MARKETPULSE APPLICATIONS
    "accounts",  # I register the custom account application.
    "core",  # I register shared models and dashboard functionality.
    "community",  # I register community and messaging functionality.
    "data_management",  # I register historical market-data functionality.
    "strategy_builder",  # I register strategy research functionality.
    "risk_management",  # I register risk-planning functionality.
    "analysis_tools",  # I register the internal analytics application.
    "api",  # I register MarketPulse's API application.
]  # I finish the application list.
# ============================================================
# 5. DJANGO MIDDLEWARE
# ============================================================
MIDDLEWARE = [  # I define request middleware in its processing order.
    "django.middleware.security.SecurityMiddleware",  # I enable Django's security-related request and response handling.
    "whitenoise.middleware.WhiteNoiseMiddleware",  # I enable serving collected static files through WhiteNoise.
    "corsheaders.middleware.CorsMiddleware",  # I add CORS handling before CommonMiddleware.
    "django.contrib.sessions.middleware.SessionMiddleware",  # I attach session support to requests.
    "django.middleware.common.CommonMiddleware",  # I enable common URL and request processing.
    "django.middleware.csrf.CsrfViewMiddleware",  # I enable CSRF checks for applicable requests.
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # I associate the session's user with each request.
    "django.contrib.messages.middleware.MessageMiddleware",  # I enable request-based user messages.
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # I apply the configured framing-protection header.
]  # I finish the middleware list.
# ============================================================
# 6. ROOT URL CONFIGURATION
# ============================================================
ROOT_URLCONF = "marketpulse.urls"  # I identify the project's main URL-routing module.
# ============================================================
# 7. TEMPLATE CONFIGURATION
# ============================================================
TEMPLATES = [  # I begin the list of template-engine configurations.
    {  # I begin the Django template engine's dictionary.
        "BACKEND": "django.template.backends.django.DjangoTemplates",  # I select Django's template engine.
        "DIRS": [  # I begin the project-level template search directories.
            BASE_DIR / "templates",  # I use Path's slash operator to construct the templates directory.
        ],  # I finish the directory list.
        "APP_DIRS": True,  # I also search installed applications' template directories.
        "OPTIONS": {  # I begin additional template-engine options.
            "context_processors": [  # I list functions that add shared template context.
                "django.template.context_processors.request",  # I make the request available in templates.
                "django.contrib.auth.context_processors.auth",  # I provide the user and permission helpers.
                "django.contrib.messages.context_processors.messages",  # I provide user messages.
            ],  # I finish the context-processor list.
        },  # I finish the engine options.
    },  # I finish this template-engine configuration.
]  # I finish the template configurations.
# ============================================================
# 8. WSGI AND ASGI CONFIGURATION
# ============================================================
WSGI_APPLICATION = "marketpulse.wsgi.application"  # I identify the callable used by the WSGI server.
ASGI_APPLICATION = "marketpulse.asgi.application"  # I identify the project's ASGI callable.
# ============================================================
# 9. DATABASE CONFIGURATION
# ============================================================
DATABASE_URL = config(  # I read an optional database connection URL.
    "DATABASE_URL",  # I identify its configuration variable.
    default="",  # I default to no external database URL.
).strip()  # I remove surrounding spaces.
if DATABASE_URL:  # I select URL-based database configuration when a URL exists.
    # 9.1 DATABASE CONFIGURED BY URL
    DATABASES = {  # I begin Django's database configuration dictionary.
        "default": dj_database_url.parse(  # I parse the URL into the default database's settings.
            DATABASE_URL,  # I supply the configured connection URL.
            conn_max_age=600,  # I allow persistent connections to be reused for up to 600 seconds.
            conn_health_checks=True,  # I enable health checks when reusing connections.
        )  # I finish parsing the database URL.
    }  # I finish the URL-based database configuration.
else:  # I select SQLite when no database URL exists.
    # 9.2 LOCAL SQLITE FALLBACK
    DATABASES = {  # I begin the fallback database dictionary.
        "default": {  # I configure the default connection.
            "ENGINE": "django.db.backends.sqlite3",  # I select Django's SQLite backend.
            "NAME": BASE_DIR / "db.sqlite3",  # I specify the SQLite database file path.
        }  # I finish the default connection settings.
    }  # I finish the fallback database configuration.
# ============================================================
# 10. CUSTOM USER MODEL
# ============================================================
AUTH_USER_MODEL = "accounts.User"  # I select the User model from the accounts application.
# ============================================================
# 11. PASSWORD VALIDATION
# ============================================================
AUTH_PASSWORD_VALIDATORS = [  # I begin the configured password-validator list.
    {  # I begin the similarity validator configuration.
        "NAME": "django.contrib.auth.password_validation." "UserAttributeSimilarityValidator",  # I join adjacent strings to identify the user-attribute similarity validator.
    },  # I finish the similarity validator configuration.
    {  # I begin the minimum-length validator configuration.
        "NAME": "django.contrib.auth.password_validation." "MinimumLengthValidator",  # I identify the password-length validator.
    },  # I finish the length validator configuration.
    {  # I begin the common-password validator configuration.
        "NAME": "django.contrib.auth.password_validation." "CommonPasswordValidator",  # I identify the validator that rejects common passwords.
    },  # I finish the common-password validator configuration.
    {  # I begin the numeric-password validator configuration.
        "NAME": "django.contrib.auth.password_validation." "NumericPasswordValidator",  # I identify the validator that rejects entirely numeric passwords.
    },  # I finish the numeric-password validator configuration.
]  # I finish the validator list.
# ============================================================
# 12. LOGIN AND LOGOUT CONFIGURATION
# ============================================================
LOGIN_URL = "accounts:login"  # I identify the login route used when authentication is required.
LOGIN_REDIRECT_URL = "home"  # I set the standard successful-login destination when no valid next destination takes priority.
LOGOUT_REDIRECT_URL = "home"  # I set the standard destination after logout.
# ============================================================
# 13. LANGUAGE AND TIMEZONE
# ============================================================
LANGUAGE_CODE = "en-us"  # I select US English as the default language.
TIME_ZONE = "Europe/Zurich"  # I select Zurich as the project's default timezone.
USE_I18N = True  # I enable Django's internationalisation support.
USE_TZ = True  # I enable timezone-aware datetime handling.
# ============================================================
# 14. STATIC FILE CONFIGURATION
# ============================================================
STATIC_URL = "/static/"  # I define the URL prefix for static assets.
STATIC_ROOT = BASE_DIR / "staticfiles"  # I define where collectstatic places deployment assets.
STATICFILES_DIRS = [  # I begin additional development static-file directories.
    BASE_DIR / "static",  # I include the project's static directory.
]  # I finish the directory list.
# 14.1 STORAGE / WHITENOISE
STORAGES = {  # I configure file-storage backends by alias.
    "default": {  # I begin normal file-storage configuration.
        "BACKEND": "django.core.files.storage.FileSystemStorage",  # I select local filesystem storage.
    },  # I finish normal file-storage configuration.
    "staticfiles": {  # I begin collected static-file storage configuration.
        "BACKEND": "whitenoise.storage." "CompressedManifestStaticFilesStorage",  # I select compressed static assets with hashed manifest filenames.
    },  # I finish static-file storage configuration.
}  # I finish the storage dictionary.
# ============================================================
# 15. DEFAULT DATABASE PRIMARY KEY
# ============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # I select automatic 64-bit integer primary keys when models do not specify another type.
# ============================================================
# 16. DJANGO REST FRAMEWORK
# ============================================================
REST_FRAMEWORK = {  # I begin global REST Framework settings.
    "DEFAULT_AUTHENTICATION_CLASSES": [  # I list default API authentication mechanisms in order.
        "rest_framework.authentication." "SessionAuthentication",  # I allow authentication through Django sessions.
        "rest_framework.authentication." "BasicAuthentication",  # I also allow HTTP Basic authentication.
    ],  # I finish the authentication-class list.
    "DEFAULT_PERMISSION_CLASSES": [  # I list default API permission policies.
        "rest_framework.permissions." "IsAuthenticatedOrReadOnly",  # I allow anonymous safe-method requests and require authentication for other methods.
    ],  # I finish the permission-class list.
}  # I finish REST Framework configuration.
# ============================================================
# 17. REACT / CORS CONFIGURATION
# ============================================================
CORS_ALLOWED_ORIGINS = config(  # I read frontend origins allowed by the CORS middleware.
    "CORS_ALLOWED_ORIGINS",  # I identify the configuration variable.
    default="http://localhost:5173",  # I preserve the local frontend origin.
    cast=lambda value: [  # I define a text-to-list conversion.
        origin.strip()  # I trim each retained origin.
        for origin in value.split(",")  # I loop over comma-separated origin entries.
        if origin.strip()  # I discard empty entries.
    ],  # I finish the list comprehension.
)  # I finish reading CORS origins.
CORS_ALLOW_CREDENTIALS = True  # I allow credentialed CORS responses; client and cookie settings still affect cookie delivery.
# ============================================================
# 18. CELERY AND REDIS CONFIGURATION
# ============================================================
USE_CELERY = config(  # I read the project's optional Celery feature flag.
    "USE_CELERY",  # I identify the configuration variable.
    default=False,  # I default the feature flag to disabled.
    cast=bool,  # I convert the configured text into a Boolean.
)  # I finish reading the flag.
CELERY_BROKER_URL = config(  # I read the message-broker connection URL.
    "REDIS_URL",  # I use the Redis configuration variable.
    default="redis://localhost:6379/0",  # I preserve the local Redis database-zero fallback.
)  # I finish reading the broker URL.
CELERY_RESULT_BACKEND = (CELERY_BROKER_URL)  # I use the same URL for storing task results; these parentheses do not create a tuple.
CELERY_ACCEPT_CONTENT = [  # I begin the accepted task-message format list.
    "json",  # I accept JSON task messages.
]  # I finish the accepted-format list.
CELERY_TASK_SERIALIZER = "json"  # I select JSON for serialising task messages.
CELERY_RESULT_SERIALIZER = "json"  # I select JSON for serialising task results.
CELERY_TIMEZONE = TIME_ZONE  # I reuse the project's timezone for Celery.
# ============================================================
# 19. CELERY BEAT SCHEDULE
# ============================================================
# Scheduling requires a running Beat process and worker.
# USE_CELERY is a project flag whose effect depends on calling code.
CELERY_BEAT_SCHEDULE = {  # I begin the periodic-task schedule dictionary.
    "monitor-strategies-hourly": {  # I give this schedule entry a descriptive key.
        "task": "strategy_builder.tasks." "monitor_active_strategies",  # I identify the registered task using adjacent joined strings.
        "schedule": 3600.0,  # I specify an interval of 3600 seconds, or one hour.
    },  # I finish the hourly task entry.
}  # I finish the Beat schedule.
# ============================================================
# 20. MATLAB CONFIGURATION
# ============================================================
MATLAB_ENABLED = config(  # I read the project's optional MATLAB feature flag.
    "MATLAB_ENABLED",  # I identify the configuration variable.
    default=False,  # I default MATLAB integration to disabled.
    cast=bool,  # I convert the configured value into a Boolean.
)  # I finish reading the MATLAB flag.
MATLAB_COMMAND = config(  # I read the command used to invoke MATLAB.
    "MATLAB_COMMAND",  # I identify the configuration variable.
    default="matlab",  # I preserve the default executable name.
)  # I finish reading the MATLAB command.
MATLAB_DIR = BASE_DIR / "matlab"  # I construct the configured directory for MATLAB files.
# ============================================================
# 21. EMAIL / PASSWORD RECOVERY CONFIGURATION
# ============================================================
# Django handles reset tokens and password changes.
# The selected email backend handles delivery or console output.
# 21.1 BREVO API KEY
BREVO_API_KEY = config(  # I read the server-side Brevo API credential.
    "BREVO_API_KEY",  # I identify the configuration variable.
    default="",  # I default to no configured key.
).strip()  # I remove surrounding spaces from the key.
# 21.2 BREVO CONFIGURATION STATUS
BREVO_CONFIGURED = bool(BREVO_API_KEY)  # I record whether a nonempty key exists; this does not verify that the key works.
# 21.3 DJANGO-ANYMAIL CONFIGURATION
ANYMAIL = {  # I begin Anymail's provider configuration dictionary.
    "BREVO_API_KEY": BREVO_API_KEY,  # I pass the configured credential to Anymail.
}  # I finish the Anymail settings.
# 21.4 EMAIL BACKEND
if BREVO_CONFIGURED:  # I select Brevo whenever a nonempty key is configured.
    EMAIL_BACKEND = (  # I begin the provider backend path.
        "anymail.backends.brevo."  # I specify the Brevo backend module.
        "EmailBackend"  # I join this adjacent string to identify its backend class.
    )  # I finish assigning the Brevo backend.
else:  # I select console output whenever the key is absent, regardless of DEBUG.
    EMAIL_BACKEND = (  # I begin the fallback backend path.
        "django.core.mail.backends."  # I specify Django's email-backend package.
        "console.EmailBackend"  # I select the backend that prints emails to the console.
    )  # I finish assigning the console backend.
# 21.5 DEFAULT SENDER EMAIL
DEFAULT_FROM_EMAIL = config(  # I read the sender used by default for outgoing email.
    "DEFAULT_FROM_EMAIL",  # I identify the configuration variable.
    default="MarketPulse <testforpass7@gmail.com>",  # I preserve the existing sender fallback exactly.
).strip()  # I remove surrounding spaces from the sender value.
SERVER_EMAIL = DEFAULT_FROM_EMAIL  # I use the same address for Django's server-generated email.
# 21.6 PASSWORD RESET TOKEN LIFETIME
PASSWORD_RESET_TIMEOUT = config(  # I read the maximum password-reset token age in seconds.
    "PASSWORD_RESET_TIMEOUT",  # I identify the configuration variable.
    default=3600,  # I preserve the one-hour default.
    cast=int,  # I convert the configured value into an integer.
)  # I finish reading the reset timeout.
# 21.7 EMAIL CONNECTION TIMEOUT
EMAIL_TIMEOUT = config(  # I read Django's email timeout setting; backend support determines how it is used.
    "EMAIL_TIMEOUT",  # I identify the configuration variable.
    default=15,  # I preserve the configured default of 15 seconds.
    cast=int,  # I convert the configured value into an integer.
)  # I finish reading the email timeout.
# 21.8 PASSWORD RESET SECURITY
# Reset emails contain a temporary reset URL, not the password.
# Django validates the reset token and stores passwords as hashes.
# ============================================================
# 22. DJANGO-BOOTSTRAP5 CONFIGURATION
# ============================================================
BOOTSTRAP5 = {  # I begin Bootstrap template-helper configuration.
    "css_url": (  # I begin the Bootstrap stylesheet URL.
        "https://cdn.jsdelivr.net/npm/"  # I specify the CDN package prefix.
        "bootstrap@5.3.3/dist/css/"  # I specify the preserved Bootstrap version and CSS directory.
        "bootstrap.min.css"  # I join the final stylesheet filename.
    ),  # I finish the stylesheet URL.
    "javascript_url": (  # I begin the Bootstrap JavaScript URL.
        "https://cdn.jsdelivr.net/npm/"  # I specify the CDN package prefix.
        "bootstrap@5.3.3/dist/js/"  # I specify the same preserved version and JavaScript directory.
        "bootstrap.bundle.min.js"  # I select the JavaScript bundle.
    ),  # I finish the JavaScript URL.
}  # I finish Bootstrap configuration.
# ============================================================
# 23. ALPACA MARKET DATA CONFIGURATION
# ============================================================
# Intended flow: Browser → MarketPulse API → Alpaca service.
# Credentials are configuration for server-side service code.
# 23.1 ALPACA API KEY ID
ALPACA_API_KEY_ID = config(  # I read the Alpaca API key identifier.
    "ALPACA_API_KEY_ID",  # I identify the configuration variable.
    default="",  # I default to no key identifier.
).strip()  # I remove surrounding spaces.
# 23.2 ALPACA API SECRET KEY
ALPACA_API_SECRET_KEY = config(  # I read the Alpaca API secret.
    "ALPACA_API_SECRET_KEY",  # I identify the configuration variable.
    default="",  # I default to no secret.
).strip()  # I remove surrounding spaces.
# 23.3 ALPACA CONFIGURATION STATUS
ALPACA_CONFIGURED = bool(  # I convert credential presence into a Boolean.
    ALPACA_API_KEY_ID  # I require a nonempty key identifier.
    and  # I use logical AND to require both credentials.
    ALPACA_API_SECRET_KEY  # I also require a nonempty secret; this does not verify authentication.
)  # I finish the configuration-status calculation.
# 23.4 ALPACA PAPER TRADING BASE URL
ALPACA_TRADING_BASE_URL = config(  # I read the trading API's base URL.
    "ALPACA_TRADING_BASE_URL",  # I identify the configuration variable.
    default="https://paper-api.alpaca.markets",  # I preserve the paper-trading endpoint without an added /v2 path.
).rstrip("/")  # I remove trailing slashes before service code adds endpoint paths.
# 23.5 ALPACA MARKET DATA BASE URL
ALPACA_DATA_BASE_URL = config(  # I read the market-data API's base URL.
    "ALPACA_DATA_BASE_URL",  # I identify the configuration variable.
    default="https://data.alpaca.markets",  # I preserve the market-data endpoint.
).rstrip("/")  # I remove trailing slashes.
# 23.6 ALPACA MARKET DATA FEED
ALPACA_DATA_FEED = config(  # I read the selected market-data feed.
    "ALPACA_DATA_FEED",  # I identify the configuration variable.
    default="iex",  # I preserve IEX as the default feed.
).strip().lower()  # I trim spaces and normalise the feed name to lowercase.
# 23.7 ALPACA REQUEST TIMEOUT
ALPACA_REQUEST_TIMEOUT = config(  # I read the timeout value for Alpaca service code to use.
    "ALPACA_REQUEST_TIMEOUT",  # I identify the configuration variable.
    default=8,  # I preserve the eight-second default.
    cast=int,  # I convert the configured value into an integer.
)  # I finish reading the request timeout.
# 23.8 ALPACA ASSET CACHE
ALPACA_ASSET_CACHE_SECONDS = config(  # I read the asset-metadata cache duration for service code.
    "ALPACA_ASSET_CACHE_SECONDS",  # I identify the configuration variable.
    default=1800,  # I preserve the 30-minute default.
    cast=int,  # I convert the configured duration into an integer.
)  # I finish reading the asset cache duration.
# 23.9 ALPACA SNAPSHOT CACHE
ALPACA_SNAPSHOT_CACHE_SECONDS = config(  # I read the snapshot cache duration for service code.
    "ALPACA_SNAPSHOT_CACHE_SECONDS",  # I identify the configuration variable.
    default=15,  # I preserve the 15-second default.
    cast=int,  # I convert the configured duration into an integer.
)  # I finish reading the snapshot cache duration.