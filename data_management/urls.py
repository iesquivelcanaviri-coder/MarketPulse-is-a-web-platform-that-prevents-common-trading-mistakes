"""
DATA MANAGEMENT - URL CONFIGURATION
Framework: Django URL dispatcher.

The project URL configuration supplies the /data/ prefix.
This module connects Data-section paths to functions in views.py.

Routes:
- /data/import/: main historical market-data workspace.
- /data/history/: authenticated user's import history.
- /data/market-condition/: analysis action handled by the view.
- /data/market-condition/results/: legacy results redirect.

Market Condition POST workflow:
Selected symbol → optional Alpaca refresh → check at least 60 recent observations
→ internal regime analyzer → redirect to the Data workspace's Market Condition panel.

Non-POST analysis requests and legacy results links redirect to the workspace.
Authentication is enforced by decorators in views.py.
External provider credentials remain in backend configuration.
"""
# ============================================================
# 1. IMPORTS
# ============================================================
from django.urls import path  # I import Django's function for creating URL patterns.
from . import views  # I import views.py from the same application package.
# ============================================================
# 2. APPLICATION NAMESPACE
# ============================================================
app_name = "data_management"  # I declare the namespace used in names such as data_management:import.
# Templates can use: {% url 'data_management:import' %}
# Python can use: reverse("data_management:import")
# ============================================================
# 3. URL PATTERNS
# ============================================================
urlpatterns = [  # I create the ordered list of routes Django checks for a matching path.
    # --------------------------------------------------------
    # 3.1 MAIN DATA WORKSPACE
    # --------------------------------------------------------
    # The view handles imports and supplies dataset, model and Market Condition context.
    path(  # I create the main workspace's URL pattern.
        "import/",  # Combined with the project prefix, this becomes /data/import/.
        views.data_import,  # I reference the view Django should call when this route matches.
        name="import",  # I name the route for template links and reverse() calls.
    ),  # I finish this pattern and separate it from the next list item.
    # --------------------------------------------------------
    # 3.2 IMPORT HISTORY
    # --------------------------------------------------------
    # The view displays the authenticated user's previous import jobs.
    path(  # I create the import-history URL pattern.
        "history/",  # Combined with the project prefix, this becomes /data/history/.
        views.import_history,  # I reference the function that renders import history.
        name="history",  # I make this route available as data_management:history.
    ),  # I finish the history pattern.
    # --------------------------------------------------------
    # 3.3 MARKET CONDITION ANALYSIS ACTION
    # --------------------------------------------------------
    # POST runs the analysis workflow; other methods redirect in the supplied view.
    # Results appear at /data/import/?symbol=SYMBOL#market-condition.
    path(  # I create the analysis action's URL pattern.
        "market-condition/",  # Combined with the project prefix, this becomes /data/market-condition/.
        views.market_condition,  # I reference the view that checks the method and handles analysis.
        name="market_condition",  # I name the route used by the analysis form's action.
    ),  # I finish the action pattern.
    # --------------------------------------------------------
    # 3.4 LEGACY MARKET CONDITION RESULTS
    # --------------------------------------------------------
    # Keeping this route allows older results links to reach the redirect view.
    path(  # I create the compatibility URL pattern.
        "market-condition/results/",  # This becomes /data/market-condition/results/.
        views.market_condition_results,  # I reference the view that redirects to the Data workspace.
        name="market_condition_results",  # I preserve the route name used by older links.
    ),  # I finish the compatibility pattern.
]  # I finish the URL-pattern list.