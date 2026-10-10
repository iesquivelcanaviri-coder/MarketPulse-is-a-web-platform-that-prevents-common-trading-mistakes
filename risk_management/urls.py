"""
============================================================
RISK MANAGEMENT - URL CONFIGURATION
============================================================
FRAMEWORK MAPPING:
MarketPulse
    ↓
/risk/
    ↓
risk_management/urls.py
    ↓
risk_management/views.py
    ↓
Risk templates
RISK WORKFLOW:
Risk
    ↓
Trade & Portfolio Risk Calculator
    ↓
Position sizing
    ↓
Stop-loss calculation
    ↓
Reward / Risk analysis
    ↓
Historical risk context
    ↓
Alpaca market information
STRESS TEST WORKFLOW:
Risk
    ↓
Stress Testing
    ↓
Select strategy
    ↓
Select asset
    ↓
Select severe market scenario
    ↓
analysis_tools/analyzers.py
    ↓
StressTest database result
IMPORTANT:
The old separate Analysis tab is no longer exposed
through the application's main navigation.
Stress Testing now belongs inside Risk because it answers:
"What could happen if market conditions become much worse?"
The old Risk Dashboard route has also been removed because
MarketPulse already has one main application Dashboard.
This keeps the Risk section focused on:
1. Trade risk planning
2. Position sizing
3. Stop-loss analysis
4. Reward-to-risk analysis
5. Stress testing
============================================================
"""  # Module docstring: describe this file's purpose and architecture.

# ============================================================
# 1. IMPORTS — REUSE DJANGO AND APPLICATION CODE
# ============================================================
from django.urls import path  # Import: reuse Django's function for defining URL routes.
from . import views  # Relative import: load views from this same application package.

# ============================================================
# 2. APPLICATION NAMESPACE — IDENTIFY THIS APP'S ROUTE NAMES
# ============================================================
app_name = "risk_management"  # Assignment: store the application namespace as a string.
# Named references include "risk_management:calculator".
# The namespace helps distinguish route names across applications.

# ============================================================
# 3. URL PATTERNS — CONNECT ROUTES TO VIEW FUNCTIONS
# ============================================================
urlpatterns = [  # List: store the route definitions Django checks in order.

    # --------------------------------------------------------
    # 3.1 TRADE & PORTFOLIO RISK CALCULATOR
    # --------------------------------------------------------
    # With the /risk/ prefix, this route is /risk/calculator/.
    # The view handles position sizing, stops, and reward-to-risk.
    path(  # Function call: create this route definition.
        "calculator/",  # String argument: the path relative to the project's include prefix.
        views.calculator,  # Function reference: give Django the view without calling it here.
        name="calculator",  # Keyword argument: name this route for links and redirects.
    ),  # Close the call; the comma separates this list item from the next.

    # --------------------------------------------------------
    # 3.2 STRESS TEST
    # --------------------------------------------------------
    # With the /risk/ prefix, this route is /risk/stress-test/.
    # The view handles strategy, asset, and scenario selection.
    # It calls the internal analysis engine to perform the test.
    path(  # Function call: create the stress-test route definition.
        "stress-test/",  # String argument: match this relative URL path.
        views.stress_test,  # Attribute access: reference the stress_test function in views.
        name="stress_test",  # Keyword argument: allow references such as risk_management:stress_test.
    ),  # Finish this route and separate it from the next list item.

    # --------------------------------------------------------
    # 3.3 STRESS TEST RESULTS
    # --------------------------------------------------------
    # With the /risk/ prefix, this route is /risk/stress-test/results/.
    # The view retrieves stored results and renders the results page.
    path(  # Function call: create the results route definition.
        "stress-test/results/",  # String argument: match the results page's relative path.
        views.stress_test_results,  # Function reference: select the results view.
        name="stress_test_results",  # Keyword argument: give this route its reusable name.
    ),  # Finish the final route definition.
]  # Close the urlpatterns list.