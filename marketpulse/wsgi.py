"""============================================================
WSGI ENTRY POINT
Framework mapping: Gunicorn/Render load this file in production.
============================================================"""
# ============================================================
# 1. IMPORTS
# ============================================================
import os  # I import Python's operating-system tools to access environment variables.
from django.core.wsgi import get_wsgi_application  # I import the function that initialises Django and creates its WSGI application.
# ============================================================
# 2. SELECT THE DJANGO SETTINGS MODULE
# ============================================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketpulse.settings')  # I select marketpulse.settings only if this environment variable is not already set.
# ============================================================
# 3. CREATE THE WSGI APPLICATION
# ============================================================
application=get_wsgi_application()  # I create and store the callable that the WSGI server uses to pass requests to Django.