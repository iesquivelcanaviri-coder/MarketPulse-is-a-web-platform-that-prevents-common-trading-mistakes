"""
Django settings for marketpulse project.

This file contains all the configuration settings for your Django project.
It's like the control center that tells Django how to behave, what databases
to connect to, what apps are installed, and many other important settings.
"""

import os
from pathlib import Path
from decouple import config  # This library helps us read environment variables safely

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR is the absolute path to your project folder.
# It's used to locate other files and directories relative to your project.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY is used for cryptographic signing in Django (like for sessions and CSRF tokens).
# In production, this should be a long, random, and secret value.
# We're using decouple to read it from environment variables for security.
SECRET_KEY = config('SECRET_KEY', default='django-insecure-8Kr9rHFmKC1QLfy7iKdoKAsKLQVKfGdhX4a3Y5aCYsrNYa50L3KiJT42NKu_CggCd6k')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG controls whether Django shows detailed error pages.
# In development (DEBUG=True), you get helpful error pages with debugging info.
# In production (DEBUG=False), you get generic error pages for security.
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS defines which hostnames this Django site can serve.
# This is a security measure to prevent HTTP Host header attacks.
# In development, we allow localhost and 127.0.0.1.
# In production, you'd set this to your actual domain(s).
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
# INSTALLED_APPS tells Django which apps are installed in this project.
# Django apps are like modules that provide specific functionality.
INSTALLED_APPS = [
    # These are Django's built-in apps:
    'django.contrib.admin',       # Admin interface for managing your data
    'django.contrib.auth',        # Authentication system (users, groups, permissions)
    'django.contrib.contenttypes', # Content type framework (for model permissions)
    'django.contrib.sessions',    # Session framework (for storing user session data)
    'django.contrib.messages',    # Message framework (for flash messages)
    'django.contrib.staticfiles', # Static files handling (CSS, JavaScript, images)
    
    # Third-party apps:
    'django_extensions',          # Additional Django management commands and shell_plus
    'bootstrap5',                 # Bootstrap 5 integration for Django
    
    # Our custom apps:
    'accounts',                   # User management and authentication
    'data_management',            # Data import and validation
    'strategy_builder',           # Trading strategy creation and backtesting
    'risk_management',            # Risk calculation and management tools
    'analysis_tools',             # Market analysis and overfitting detection
    'core',                       # Shared models and utilities
]

# MIDDLEWARE is a list of middleware classes that process requests and responses.
# Middleware is like a series of hooks that process requests before they reach views
# and process responses before they're sent to the browser.
# The order is important - middleware is applied in the order listed here.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',      # Security-related middleware
    'whitenoise.middleware.WhiteNoiseMiddleware',         # For serving static files in production
    'django.contrib.sessions.middleware.SessionMiddleware', # Session management
    'django.middleware.common.CommonMiddleware',          # Common middleware (e.g., handling trailing slashes)
    'django.middleware.csrf.CsrfViewMiddleware',         # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware', # User authentication
    'django.contrib.messages.middleware.MessageMiddleware', # Message framework
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Clickjacking protection
]

# ROOT_URLCONF tells Django where to find the main URL configuration file.
# This is the entry point for URL routing in your project.
ROOT_URLCONF = 'marketpulse.urls'

# TEMPLATES configures how Django renders templates.
# Templates are HTML files with Django template tags that can display dynamic data.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Use Django's template engine
        'DIRS': [BASE_DIR / 'templates'],  # Look for templates in the project's templates directory
        'APP_DIRS': True,  # Also look for templates in each app's templates directory
        'OPTIONS': {
            'context_processors': [
                # Context processors add variables to the template context for all templates
                'django.template.context_processors.debug',     # Debug information
                'django.template.context_processors.request',   # Request object
                'django.contrib.auth.context_processors.auth',  # User authentication info
                'django.contrib.messages.context_processors.messages',  # Messages
            ],
        },
    },
]

# WSGI_APPLICATION tells Django where to find the WSGI application.
# WSGI is the interface between Django and the web server.
WSGI_APPLICATION = 'marketpulse.wsgi.application'

# Database configuration
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
# DATABASES tells Django how to connect to your database.
# We're using PostgreSQL, which is a robust database suitable for production.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Use PostgreSQL backend
        'NAME': config('DB_NAME', default='marketpulse'),  # Database name
        'USER': config('DB_USER', default='postgres'),      # Database username
        'PASSWORD': config('DB_PASSWORD', default=''),     # Database password
        'HOST': config('DB_HOST', default='localhost'),    # Database host
        'PORT': config('DB_PORT', default='5432'),         # Database port
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
# These validators ensure user passwords meet certain security requirements.
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        # Prevents passwords that are too similar to user attributes (like username)
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        # Enforces minimum password length
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        # Prevents commonly used passwords
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        # Prevents passwords that are entirely numeric
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
# These settings control how Django handles different languages and time zones.
LANGUAGE_CODE = 'en-us'  # Default language code
TIME_ZONE = 'UTC'       # Default time zone
USE_I18N = True         # Enable internationalization (translation system)
USE_TZ = True          # Enable time zone support

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
# Static files are assets that don't change, like CSS, JavaScript, and images.
STATIC_URL = '/static/'                    # URL prefix for static files
STATIC_ROOT = BASE_DIR / 'staticfiles'     # Directory where collected static files will be stored
STATICFILES_DIRS = [                        # Additional directories to look for static files
    BASE_DIR / 'static',
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
# This tells Django what type of primary key to use for models that don't specify one.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
# This tells Django to use our custom User model instead of the default one.
# Our custom User model is defined in the accounts app.
AUTH_USER_MODEL = 'accounts.User'

# Celery Configuration
# Celery is a task queue system for running background tasks.
# It's useful for long-running tasks like data imports or backtesting.
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')  # Redis server URL
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')  # Where to store task results
CELERY_ACCEPT_CONTENT = ['json']  # Only accept JSON content
CELERY_TASK_SERIALIZER = 'json'   # Serialize tasks as JSON
CELERY_RESULT_SERIALIZER = 'json'  # Serialize results as JSON
CELERY_TIMEZONE = TIME_ZONE        # Use the same timezone as the project

# Email Configuration
# These settings control how Django sends emails.
# They're used for things like password reset emails.
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
# In development, emails are printed to the console. In production, you'd use a real email backend.
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')  # SMTP server
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)    # SMTP port
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)  # Use TLS encryption
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')     # SMTP username
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')  # SMTP password

# Yahoo Finance API
# This is where you'd store your API key for accessing Yahoo Finance data.
YAHOO_FINANCE_API_KEY = config('YAHOO_FINANCE_API_KEY', default='')

# Bootstrap 5 Configuration
# These settings configure the django-bootstrap5 package.
BOOTSTRAP5 = {
    'css_url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'js_url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
    'theme_url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'javascript_url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
}

# Login/Logout URLs
# These settings tell Django where to redirect users after login, logout, etc.
LOGIN_URL = 'accounts:login'           # Where to redirect for login
LOGIN_REDIRECT_URL = 'dashboard'        # Where to redirect after successful login
LOGOUT_REDIRECT_URL = 'home'            # Where to redirect after logout