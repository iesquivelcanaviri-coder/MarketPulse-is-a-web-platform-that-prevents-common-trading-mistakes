"""
============================================================
MARKETPULSE - STRATEGY BUILDER URLS
============================================================

Framework mapping:

/strategy/
    ↓
strategy_builder/urls.py
    ↓
strategy_builder/views.py
    ↓
templates/strategy_builder/


AVAILABLE ROUTES:

/strategy/
    -> Strategy & Model Research workspace
    -> Shows:
       - 37 library models
       - 7 model categories
       - Search and filtering
       - Model comparison
       - User-created strategies
       - Backtest summaries


/strategy/create/
    -> Create a custom trading strategy


/strategy/library/add/
    -> Add another model or strategy to the
       StrategyLibraryItem catalogue


/strategy/<strategy_id>/backtest/
    -> Run a historical backtest for a
       user-created strategy


/strategy/results/<backtest_id>/
    -> View saved backtest results

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

# This allows templates and views to reference URLs using:
#
# strategy_builder:list
# strategy_builder:create
# strategy_builder:library_add
# strategy_builder:backtest
# strategy_builder:results
app_name = "strategy_builder"


# ============================================================
# 3. URL PATTERNS
# ============================================================

urlpatterns = [

    # ========================================================
    # STRATEGY & MODEL RESEARCH WORKSPACE
    # ========================================================

    # URL:
    #
    # /strategy/
    #
    # Purpose:
    #
    # Displays the complete MarketPulse Strategy & Model
    # Research workspace.
    #
    # This page contains:
    #
    # - StrategyLibraryItem catalogue
    # - 37 quantitative models
    # - Category filtering
    # - Search
    # - Metadata comparison
    # - My Strategies
    # - Backtest summaries
    path(
        "",
        views.strategy_list,
        name="list",
    ),


    # ========================================================
    # CREATE USER STRATEGY
    # ========================================================

    # URL:
    #
    # /strategy/create/
    #
    # Purpose:
    #
    # Allows a logged-in user to create their own
    # rule-based MarketPulse trading strategy.
    path(
        "create/",
        views.strategy_create,
        name="create",
    ),


    # ========================================================
    # ADD MODEL TO STRATEGY LIBRARY
    # ========================================================

    # URL:
    #
    # /strategy/library/add/
    #
    # Purpose:
    #
    # Allows another quantitative model, strategy or
    # analytical method to be added to StrategyLibraryItem.
    #
    # New models should initially be stored as:
    #
    # implementation_status = "catalogued"
    #
    # until their numerical execution engine has actually
    # been implemented and tested.
    path(
        "library/add/",
        views.library_item_create,
        name="library_add",
    ),


    # ========================================================
    # BACKTEST USER STRATEGY
    # ========================================================

    # Example:
    #
    # /strategy/4/backtest/
    #
    # strategy_id identifies the Strategy record that
    # should be tested against historical market data.
    path(
        "<int:strategy_id>/backtest/",
        views.backtest_strategy,
        name="backtest",
    ),


    # ========================================================
    # VIEW BACKTEST RESULTS
    # ========================================================

    # Example:
    #
    # /strategy/results/12/
    #
    # backtest_id identifies the saved Backtest record.
    path(
        "results/<int:backtest_id>/",
        views.backtest_results,
        name="results",
    ),

]