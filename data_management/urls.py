"""
============================================================
DATA MANAGEMENT - URL CONFIGURATION
============================================================

Framework mapping:

marketpulse/urls.py
    ↓
data_management/urls.py
    ↓
data_management/views.py
    ↓
templates/data_management/

Routes:

/data/import/
    -> Historical market-data import

/data/history/
    -> Previous import history
============================================================
"""

# ============================================================
# 1. IMPORTS
# ============================================================

from django.urls import path

from . import views


# ============================================================
# 2. APPLICATION NAMESPACE
# ============================================================

app_name = "data_management"


# ============================================================
# 3. URL PATTERNS
# ============================================================

urlpatterns = [

    # --------------------------------------------------------
    # Historical Market Data Import
    # --------------------------------------------------------

    path(
        "import/",
        views.data_import,
        name="import",
    ),


    # --------------------------------------------------------
    # Historical Import History
    # --------------------------------------------------------

    path(
        "history/",
        views.import_history,
        name="history",
    ),

]