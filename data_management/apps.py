"""============================================================ DATA MANAGEMENT APP CONFIG ============================================================"""
# ============================================================
# 1. DJANGO IMPORT
# ============================================================
from django.apps import AppConfig  # I import Django's base class for application configuration.
# ============================================================
# 2. DATA MANAGEMENT APPLICATION CONFIGURATION
# ============================================================
class DataManagementConfig(AppConfig):  # I inherit AppConfig to define this application's settings.
    default_auto_field = 'django.db.models.BigAutoField'  # I choose BigAutoField for model primary keys that Django adds automatically.
    name = 'data_management'  # I identify the Python package this configuration belongs to.