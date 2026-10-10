"""============================================================ STRATEGY BUILDER APP CONFIG ============================================================"""

# ============================================================
# 1. IMPORT DJANGO'S APPLICATION CONFIGURATION CLASS
# ============================================================
from django.apps import AppConfig  # Import: I bring in Django's base class for application configuration.

# ============================================================
# 2. DEFINE THE STRATEGY BUILDER APPLICATION CONFIGURATION
# ============================================================
class StrategyBuilderConfig(AppConfig):  # Class inheritance: I create an application configuration using Django's AppConfig.

    # --------------------------------------------------------
    # 2.1 DEFAULT AUTOMATIC PRIMARY-KEY TYPE
    # --------------------------------------------------------
    default_auto_field = 'django.db.models.BigAutoField'  # Class attribute and string: I select a 64-bit automatic integer field for implicitly added primary keys.

    # --------------------------------------------------------
    # 2.2 APPLICATION PACKAGE NAME
    # --------------------------------------------------------
    name = 'strategy_builder'  # Class attribute and string: I identify the Python package containing this application.