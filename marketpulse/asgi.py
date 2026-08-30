"""============================================================
ASGI ENTRY POINT
Framework mapping: async-capable server entry point and future WebSocket support.
============================================================"""
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE','marketpulse.settings')
application=get_asgi_application()
