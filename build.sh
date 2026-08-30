#!/usr/bin/env bash
# ============================================================
# RENDER BUILD SCRIPT
# ============================================================
set -o errexit
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
