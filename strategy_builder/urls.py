"""
MARKETPULSE - STRATEGY BUILDER URLS

Purpose:
Connect strategy-related URL paths to their Django views.

Framework:
Project URL configuration includes this file under /strategy/.
Django matches a path and calls its view.
The view renders a template, redirects, or calls backend services.

Programming concepts:
Imports, relative imports, variables, strings, lists,
function calls, keyword arguments and integer URL converters.

Note:
This file defines routes, not the number of library models.
The robustness routes use the legacy redirect views.
"""

# ============================================================
# 1. IMPORTS
# ============================================================
from django.urls import path  # Import: I bring in Django's function for defining URL patterns.
from . import views  # Relative import: I import views from this same application package.

# ============================================================
# 2. APPLICATION NAMESPACE
# ============================================================
app_name = "strategy_builder"  # Variable assignment and string: I define the application namespace for named URLs.

# ============================================================
# 3. URL PATTERNS
# ============================================================
urlpatterns = [  # List assignment: I collect the URL patterns Django checks in order.

    # --------------------------------------------------------
    # 3.1 STRATEGY & MODEL RESEARCH WORKSPACE
    # Named URL: strategy_builder:list
    # Full path: /strategy/ when included under that prefix.
    # --------------------------------------------------------
    path(  # Function call: I create the workspace URL pattern.
        "",  # Empty string: I match the application's root path.
        views.strategy_list,  # Function reference: I give Django the view to call without calling it here.
        name="list",  # Keyword argument: I name this route for URL reversing.
    ),  # Closing call and comma: I finish this pattern and separate it from the next list item.

    # --------------------------------------------------------
    # 3.2 CREATE A USER STRATEGY
    # Named URL: strategy_builder:create
    # Full path: /strategy/create/
    # --------------------------------------------------------
    path(  # Function call: I create the strategy-creation URL pattern.
        "create/",  # String literal: I match the create/ path inside this application.
        views.strategy_create,  # Function reference: I connect the route to the strategy-creation view.
        name="create",  # Keyword argument: I assign the route its reusable name.
    ),  # Closing call and comma: I finish the creation pattern.

    # --------------------------------------------------------
    # 3.3 ADD A MODEL TO THE LIBRARY
    # Named URL: strategy_builder:library_add
    # Full path: /strategy/library/add/
    # The view handles the form and the catalogued status.
    # --------------------------------------------------------
    path(  # Function call: I create the library-addition URL pattern.
        "library/add/",  # String literal: I match the nested library/add/ path.
        views.library_item_create,  # Function reference: I connect the route to the library-entry creation view.
        name="library_add",  # Keyword argument: I name the route for templates and Python code.
    ),  # Closing call and comma: I finish the library-addition pattern.

    # --------------------------------------------------------
    # 3.4 LEGACY STRATEGY ROBUSTNESS ROUTE
    # Named URL: strategy_builder:robustness
    # Full path: /strategy/robustness/
    # The supplied view redirects to the workspace section.
    # --------------------------------------------------------
    path(  # Function call: I keep the robustness URL available for existing links.
        "robustness/",  # String literal: I match the robustness/ path.
        views.strategy_robustness,  # Function reference: I connect this route to the legacy redirect view.
        name="robustness",  # Keyword argument: I preserve the existing named route.
    ),  # Closing call and comma: I finish the robustness pattern.

    # --------------------------------------------------------
    # 3.5 LEGACY STRATEGY ROBUSTNESS RESULTS ROUTE
    # Named URL: strategy_builder:robustness_results
    # Full path: /strategy/robustness/results/
    # The supplied view redirects to the workspace section.
    # --------------------------------------------------------
    path(  # Function call: I keep the older robustness-results URL available.
        "robustness/results/",  # String literal: I match the complete results path.
        views.strategy_robustness_results,  # Function reference: I connect the route to its redirect view.
        name="robustness_results",  # Keyword argument: I preserve the results route's name.
    ),  # Closing call and comma: I finish the robustness-results pattern.

    # --------------------------------------------------------
    # 3.6 BACKTEST A USER STRATEGY
    # Named URL: strategy_builder:backtest
    # Example full path: /strategy/4/backtest/
    # --------------------------------------------------------
    path(  # Function call: I create a URL pattern containing a strategy ID.
        "<int:strategy_id>/backtest/",  # Integer converter: I capture a non-negative integer and pass it as strategy_id.
        views.backtest_strategy,  # Function reference: I connect the route to the view that handles backtesting.
        name="backtest",  # Keyword argument: I name the route so links can supply a strategy_id.
    ),  # Closing call and comma: I finish the backtest pattern.

    # --------------------------------------------------------
    # 3.7 VIEW SAVED BACKTEST RESULTS
    # Named URL: strategy_builder:results
    # Example full path: /strategy/results/12/
    # --------------------------------------------------------
    path(  # Function call: I create a URL pattern containing a backtest ID.
        "results/<int:backtest_id>/",  # Integer converter: I capture an integer and pass it to the view as backtest_id.
        views.backtest_results,  # Function reference: I connect the route to the saved-results view.
        name="results",  # Keyword argument: I name the route so links can supply a backtest_id.
    ),  # Closing call and comma: I finish the final URL pattern.
]  # Closing bracket: I finish the urlpatterns list.