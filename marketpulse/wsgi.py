"""============================================================
WSGI ENTRY POINT
Framework mapping: Gunicorn/Render load this file in production.
============================================================"""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE','marketpulse.settings')
application=get_wsgi_application()
