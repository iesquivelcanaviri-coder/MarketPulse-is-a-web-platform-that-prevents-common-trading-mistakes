"""
============================================================
DATA MANAGEMENT - URL CONFIGURATION
============================================================

This file defines the routes belonging to the MarketPulse
Data section.

============================================================
FRAMEWORK MAPPING
============================================================

Browser / Django Template
        ↓
marketpulse/urls.py
        ↓
data_management/urls.py
        ↓
data_management/views.py
        ↓
core.MarketData / analysis_tools
        ↓
PostgreSQL / Neon
        ↓
templates/data_management/


============================================================
FINAL USER-FACING DATA WORKFLOW
============================================================

Data
    ↓
/data/import/
    ↓
Historical Market Data Workspace
    ↓
Import / Select Dataset
    ↓
Historical Chart + Data Table
    ↓
Detailed Market Condition
    ↓
Run Market Condition Analysis
    ↓
POST /data/market-condition/
    ↓
views.market_condition()
    ↓
analysis_tools.analyzers.identify_market_regime()
    ↓
analysis_tools.models.MarketRegime
    ↓
PostgreSQL
    ↓
Redirect back to:

/data/import/?symbol=SYMBOL#market-condition

    ↓
Updated Market Condition displayed inside the
same Data workspace


============================================================
IMPORTANT ARCHITECTURE CHANGE
============================================================

Market Condition is no longer treated as a separate
user-facing page.

Previously:

Data
    ↓
Open Market Condition
    ↓
Separate Market Condition page
    ↓
Run analysis
    ↓
View result


Current architecture:

Data
    ↓
Detailed Market Condition
    ↓
Run analysis
    ↓
Result displayed inside Data


This produces a simpler and more coherent workflow because
Market Condition is an analysis of the historical dataset
already being viewed inside the Data tab.


============================================================
ROUTE PURPOSES
============================================================

/data/import/

    Main Data workspace.

    Handles:

    - Alpaca historical-data import
    - stored dataset selection
    - historical OHLCV review
    - historical chart
    - dataset statistics
    - latest Market Condition result
    - Detailed Market Condition interface


/data/history/

    Displays historical import jobs and their status.


/data/market-condition/

    Analysis ACTION endpoint.

    This route does not need to render a separate page.

    POST:
        Runs Market Regime Analysis and redirects back
        to the Data workspace.

    GET:
        Older links can safely redirect back to Data.


/data/market-condition/results/

    Legacy compatibility route.

    Older MarketPulse code may still reference this URL.

    It should redirect back to the Data workspace rather
    than render a separate results page.


============================================================
INTERNAL ANALYTICS ARCHITECTURE
============================================================

The user-facing feature belongs to data_management.

The technical analytical implementation remains inside:

analysis_tools/analyzers.py

This separation is intentional:

data_management
    ↓
Owns the Data user workflow

analysis_tools
    ↓
Owns reusable statistical calculations


============================================================
SECURITY
============================================================

All Data views requiring authentication should use
@login_required inside data_management/views.py.

External market-data credentials remain on the Django
backend and must never be exposed through URL configuration,
templates or JavaScript.

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

# Using an application namespace allows templates and Python
# code to reference routes safely.
#
# Examples:
#
# {% url 'data_management:import' %}
#
# {% url 'data_management:history' %}
#
# {% url 'data_management:market_condition' %}
#
# {% url 'data_management:market_condition_results' %}
#
#
# Python example:
#
# reverse("data_management:import")

app_name = "data_management"


# ============================================================
# 3. URL PATTERNS
# ============================================================

urlpatterns = [


    # ========================================================
    # 3.1 MAIN DATA WORKSPACE
    # ========================================================
    #
    # URL:
    #
    # /data/import/
    #
    #
    # VIEW:
    #
    # views.data_import
    #
    #
    # TEMPLATE:
    #
    # data_management/import.html
    #
    #
    # PURPOSE:
    #
    # This is now the primary user-facing workspace for the
    # complete MarketPulse Data workflow.
    #
    #
    # USER WORKFLOW:
    #
    # Data
    #   ↓
    # Import Historical Data
    #   ↓
    # Select Stored Dataset
    #   ↓
    # Review Historical Chart
    #   ↓
    # Review Historical OHLCV Data
    #   ↓
    # Detailed Market Condition
    #
    #
    # DATA PROVIDED BY THIS VIEW:
    #
    # - import form
    # - selected symbol
    # - available symbols
    # - MarketData observations
    # - observation count
    # - earliest record
    # - latest record
    # - recent imports
    # - selected strategy/model information
    # - latest MarketRegime result
    # - market-data provider
    # - market-data feed
    #
    #
    # Template reference:
    #
    # {% url 'data_management:import' %}
    #
    # ========================================================

    path(
        "import/",
        views.data_import,
        name="import",
    ),


    # ========================================================
    # 3.2 IMPORT HISTORY
    # ========================================================
    #
    # URL:
    #
    # /data/history/
    #
    #
    # VIEW:
    #
    # views.import_history
    #
    #
    # TEMPLATE:
    #
    # data_management/history.html
    #
    #
    # PURPOSE:
    #
    # Displays previous historical-data import activity.
    #
    #
    # The user can review:
    #
    # - imported symbol
    # - provider
    # - requested dates
    # - number of imported observations
    # - completion status
    # - error information
    # - import timestamp
    #
    #
    # Template reference:
    #
    # {% url 'data_management:history' %}
    #
    # ========================================================

    path(
        "history/",
        views.import_history,
        name="history",
    ),


    # ========================================================
    # 3.3 MARKET CONDITION ANALYSIS ACTION
    # ========================================================
    #
    # URL:
    #
    # /data/market-condition/
    #
    #
    # VIEW:
    #
    # views.market_condition
    #
    #
    # IMPORTANT:
    #
    # This is no longer intended to be a separate
    # user-facing page.
    #
    #
    # The visible interface now lives inside:
    #
    # data_management/import.html
    #
    # under:
    #
    # Detailed Market Condition
    #
    #
    # ========================================================
    # POST WORKFLOW
    # ========================================================
    #
    # User clicks:
    #
    # Run Market Condition Analysis
    #
    #       ↓
    #
    # POST /data/market-condition/
    #
    #       ↓
    #
    # views.market_condition()
    #
    #       ↓
    #
    # Validate selected symbol
    #
    #       ↓
    #
    # Check at least 20 MarketData observations
    #
    #       ↓
    #
    # identify_market_regime()
    #
    #       ↓
    #
    # MarketRegime saved
    #
    #       ↓
    #
    # Redirect:
    #
    # /data/import/?symbol=SPY#market-condition
    #
    #       ↓
    #
    # Updated result appears inside the same Data workspace
    #
    #
    # ========================================================
    # GET WORKFLOW
    # ========================================================
    #
    # Older bookmarks may still point directly to:
    #
    # /data/market-condition/?symbol=SPY
    #
    # The view can safely redirect those requests back to:
    #
    # /data/import/?symbol=SPY#market-condition
    #
    #
    # Template form action:
    #
    # {% url 'data_management:market_condition' %}
    #
    # ========================================================

    path(
        "market-condition/",
        views.market_condition,
        name="market_condition",
    ),


    # ========================================================
    # 3.4 LEGACY MARKET CONDITION RESULTS ROUTE
    # ========================================================
    #
    # URL:
    #
    # /data/market-condition/results/
    #
    #
    # VIEW:
    #
    # views.market_condition_results
    #
    #
    # STATUS:
    #
    # LEGACY / COMPATIBILITY ROUTE
    #
    #
    # Older versions of MarketPulse used a separate
    # Market Condition results workflow.
    #
    # The final application no longer needs a separate
    # results page.
    #
    #
    # OLD:
    #
    # Data
    #   ↓
    # Market Condition page
    #   ↓
    # Results page
    #
    #
    # NEW:
    #
    # Data
    #   ↓
    # Detailed Market Condition
    #   ↓
    # Analysis + Result
    #
    #
    # Therefore this route should now redirect users back to:
    #
    # /data/import/?symbol=SYMBOL#market-condition
    #
    #
    # WHY KEEP IT?
    #
    # Keeping the route temporarily prevents older:
    #
    # - template links
    # - bookmarks
    # - redirects
    # - demonstration URLs
    #
    # from producing a 404 error.
    #
    #
    # It can be removed later once the project has been
    # completely checked for legacy references.
    #
    # ========================================================

    path(
        "market-condition/results/",
        views.market_condition_results,
        name="market_condition_results",
    ),

]