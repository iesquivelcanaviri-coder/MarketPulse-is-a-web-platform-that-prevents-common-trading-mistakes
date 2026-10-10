"""============================================================
PROJECT PACKAGE
Framework mapping: exposes the Celery application while Django loads settings.
============================================================"""
# ============================================================
# 1. IMPORT AND EXPOSE THE CELERY APPLICATION
# ============================================================
from .celery import app as celery_app  # I import app from this package's celery module and give the same object the name celery_app.
# ============================================================
# 2. DECLARE THE WILDCARD IMPORT EXPORT
# ============================================================
__all__ = ('celery_app',)  # I specify what "from marketpulse import *" exports; the trailing comma makes this a one-item tuple.