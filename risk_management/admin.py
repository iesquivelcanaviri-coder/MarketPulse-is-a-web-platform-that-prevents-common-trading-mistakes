"""============================================================ RISK ADMIN ============================================================"""  # Module docstring: identify this administration file.

# ============================================================
# 1. IMPORT DJANGO ADMIN
# ============================================================
from django.contrib import admin  # Import: make Django's administration tools available.

# ============================================================
# 2. IMPORT THE RISK SNAPSHOT MODEL
# ============================================================
from .models import RiskSnapshot  # Relative import: load RiskSnapshot from this application's models module.

# ============================================================
# 3. REGISTER THE MODEL
# ============================================================
admin.site.register(RiskSnapshot)  # Method call: register the model class with Django's default admin site.