"""============================================================
PROJECT PACKAGE
Framework mapping: exposes the Celery application while Django loads settings.
============================================================"""
from .celery import app as celery_app
__all__=('celery_app',)
