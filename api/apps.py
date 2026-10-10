"""============================================================ API APP CONFIG: DRF layer between React and Django services. ============================================================"""  # DOCSTRING: A string at the start of the module that explains what this Python file is responsible for.

# ============================================================
# 1. DJANGO IMPORT
# ============================================================
from django.apps import AppConfig  # IMPORT: Brings Django's AppConfig class into this file so our API application can inherit Django's app configuration behaviour.

# ============================================================
# 2. API APPLICATION CONFIGURATION
# ============================================================
class ApiConfig(AppConfig): default_auto_field='django.db.models.BigAutoField'; name='api'  # CLASS + INHERITANCE: Creates ApiConfig from AppConfig; CLASS ATTRIBUTES configure the automatic database ID type and tell Django this application's Python package is named "api".