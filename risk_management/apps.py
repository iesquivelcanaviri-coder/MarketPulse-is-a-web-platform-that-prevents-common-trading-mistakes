"""============================================================ RISK MANAGEMENT APP CONFIG ============================================================"""  # Module docstring: describe this configuration file.

# ============================================================
# 1. IMPORT — REUSE DJANGO'S APP CONFIGURATION CLASS
# ============================================================
from django.apps import AppConfig  # Import: make Django's AppConfig class available here.

# ============================================================
# 2. CLASS — DEFINE THE RISK MANAGEMENT CONFIGURATION
# ============================================================
class RiskManagementConfig(AppConfig):  # Inheritance: extend AppConfig with settings for this application.

    # --------------------------------------------------------
    # 2.1 DEFAULT AUTOMATIC PRIMARY KEY
    # --------------------------------------------------------
    default_auto_field = 'django.db.models.BigAutoField'  # Class attribute: choose BigAutoField for implicit model primary keys.

    # --------------------------------------------------------
    # 2.2 APPLICATION NAME
    # --------------------------------------------------------
    name = 'risk_management'  # String assignment: identify this application's Python package.