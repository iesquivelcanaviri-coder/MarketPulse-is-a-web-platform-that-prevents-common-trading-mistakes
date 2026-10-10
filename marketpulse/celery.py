"""============================================================
CELERY CONFIGURATION
Framework mapping: discovers tasks.py modules from Django apps; Redis is optional locally.
============================================================"""
# ============================================================
# 1. IMPORTS
# ============================================================
import os  # I import operating-system tools to access environment variables.
from celery import Celery  # I import the class used to create a Celery application.
# ============================================================
# 2. SELECT THE DJANGO SETTINGS MODULE
# ============================================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketpulse.settings')  # I select the project's settings only if this environment variable is not already set.
# ============================================================
# 3. CREATE THE CELERY APPLICATION
# ============================================================
app=Celery('marketpulse')  # I create a Celery application named marketpulse and store the object in app.
# ============================================================
# 4. LOAD CELERY CONFIGURATION FROM DJANGO
# ============================================================
app.config_from_object('django.conf:settings', namespace='CELERY')  # I use Django settings as the configuration source, with CELERY_ prefixed setting names.
# ============================================================
# 5. DISCOVER APPLICATION TASK MODULES
# ============================================================
app.autodiscover_tasks()  # I enable automatic discovery of tasks.py modules in installed Django applications.