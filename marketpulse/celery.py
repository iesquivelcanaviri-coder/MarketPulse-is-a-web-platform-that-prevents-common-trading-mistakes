"""============================================================
CELERY CONFIGURATION
Framework mapping: discovers tasks.py modules from Django apps; Redis is optional locally.
============================================================"""
import os
from celery import Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE','marketpulse.settings')
app=Celery('marketpulse')
app.config_from_object('django.conf:settings',namespace='CELERY')
app.autodiscover_tasks()
