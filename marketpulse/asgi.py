"""============================================================
ASGI ENTRY POINT
Framework mapping: async-capable server entry point and future WebSocket support.
============================================================"""
# ============================================================
# 1. IMPORTS
# ============================================================
import os  # I import operating-system tools to access environment variables.
from django.core.asgi import get_asgi_application  # I import the function that initialises Django and creates its ASGI application.
# ============================================================
# 2. SELECT THE DJANGO SETTINGS MODULE
# ============================================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketpulse.settings')  # I select the project's settings only if this environment variable is not already set.
# ============================================================
# 3. CREATE THE ASGI APPLICATION
# ============================================================
application=get_asgi_application()  # I create and store the callable that an ASGI server uses to communicate with Django.