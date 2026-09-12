# ============================================================
# MARKETPULSE - PRODUCTION DOCKERFILE
# ============================================================
#
# FRAMEWORK MAPPING:
#
# GitHub Repository
#       ↓
# Render
#       ↓
# Dockerfile
#       ↓
# Python 3.13
#       ↓
# Install requirements.txt
#       ↓
# Copy MarketPulse project
#       ↓
# Collect Django static files
#       ↓
# Gunicorn
#       ↓
# marketpulse/wsgi.py
#       ↓
# Django Web Application
#
#
# IMPORTANT:
#
# Real credentials are NOT stored in this Dockerfile.
#
# Production values such as:
#
# - SECRET_KEY
# - DATABASE_URL
# - ALPACA_API_KEY_ID
# - ALPACA_API_SECRET_KEY
#
# are supplied through Render Environment Variables.
#
# Database migrations are run using Render's:
#
# Pre-Deploy Command:
#
#     python manage.py migrate
#
# ============================================================


# ============================================================
# 1. PYTHON BASE IMAGE
# ============================================================

# MarketPulse currently uses Python 3.13.
FROM python:3.13-slim


# ============================================================
# 2. PYTHON RUNTIME SETTINGS
# ============================================================

# Prevent Python from creating unnecessary .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1


# Send Python output directly to Render logs instead of
# buffering it.
ENV PYTHONUNBUFFERED=1


# ============================================================
# 3. APPLICATION DIRECTORY
# ============================================================

# All MarketPulse files will run from /app inside the
# Docker container.
WORKDIR /app


# ============================================================
# 4. INSTALL PYTHON DEPENDENCIES
# ============================================================

# Copy requirements separately first.
#
# Docker can cache this layer when requirements.txt has not
# changed, which makes later deployments faster.
COPY requirements.txt .


# Upgrade pip and install all MarketPulse dependencies.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ============================================================
# 5. COPY MARKETPULSE PROJECT
# ============================================================

# Copy the Django project into the Docker container.
#
# Files listed inside .dockerignore will not be copied.
COPY . .


# ============================================================
# 6. COLLECT DJANGO STATIC FILES
# ============================================================

# MarketPulse uses WhiteNoise in production.
#
# Django therefore needs to collect:
#
# static/
#     ↓
# staticfiles/
#
# before Gunicorn starts.
#
# A temporary build-only Django SECRET_KEY is used here.
#
# This is NOT the real production SECRET_KEY.
#
# DATABASE_URL is intentionally blank during this build step.
# Django can use the local SQLite fallback because database
# access is not required to collect CSS and JavaScript files.
RUN SECRET_KEY=marketpulse-build-only-secret-key \
    DEBUG=False \
    DATABASE_URL= \
    python manage.py collectstatic --noinput


# ============================================================
# 7. EXPOSE APPLICATION PORT
# ============================================================

# Port 8000 is useful locally.
#
# On Render, the actual port is supplied automatically through
# the PORT environment variable.
EXPOSE 8000


# ============================================================
# 8. START MARKETPULSE WITH GUNICORN
# ============================================================

# Production request flow:
#
# Browser
#     ↓
# Render
#     ↓
# Gunicorn
#     ↓
# marketpulse.wsgi
#     ↓
# Django
#     ↓
# MarketPulse Views / Templates / APIs
#
#
# ${PORT:-8000}
#
# means:
#
# - Use Render's PORT when deployed.
# - Otherwise use port 8000 locally.
#
#
# Two Gunicorn workers are sufficient for the current
# MarketPulse college project and the Render free service.
#
# Access and error logs are sent to Render's log console.
CMD ["sh", "-c", "gunicorn marketpulse.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --access-logfile - --error-logfile -"]