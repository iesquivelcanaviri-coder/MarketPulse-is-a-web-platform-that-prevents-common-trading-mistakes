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
    ↓
analysis_tools.analyzers
    ↓
PostgreSQL


============================================================
USER-FACING STRATEGY WORKFLOW
============================================================

/strategy/
    -> Strategy & Model Research workspace

    Shows:
       - Strategy & Model Library
       - 37 quantitative models
       - 7 model categories
       - Search and filtering
       - Model comparison
       - User-created strategies
       - Backtest summaries
       - Strategy validation tools


/strategy/create/
    -> Create a custom trading strategy


/strategy/library/add/
    -> Add another quantitative model or strategy
       to the StrategyLibraryItem catalogue


/strategy/robustness/
    -> Strategy Robustness
    -> User-friendly name for Overfitting Analysis

    Answers the question:

       "Does this strategy continue to behave reasonably
        when tested on different historical periods?"


/strategy/robustness/results/
    -> View Strategy Robustness / Overfitting results


/strategy/<strategy_id>/backtest/
    -> Run a historical backtest for a
       user-created strategy


/strategy/results/<backtest_id>/
    -> View saved backtest results


============================================================
IMPORTANT ARCHITECTURE
============================================================

The old public Analysis tab is being removed.

However:

analysis_tools/
    models.py
    analyzers.py
    migrations/

remain part of MarketPulse internally.

For Strategy Robustness the architecture becomes:

Strategies Tab
    ↓
strategy_builder.views
    ↓
analysis_tools.analyzers.detect_overfitting()
    ↓
analysis_tools.models.OverfittingTest
    ↓
PostgreSQL

This gives the user a simpler interface while keeping
the analytics implementation separated into a reusable
backend analytics layer.

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

# This namespace allows templates and Python code to
# reference routes using descriptive names instead of
# hard-coded URLs.
#
# Examples:
#
# strategy_builder:list
# strategy_builder:create
# strategy_builder:library_add
# strategy_builder:robustness
# strategy_builder:robustness_results
# strategy_builder:backtest
# strategy_builder:results

app_name = "strategy_builder"


# ============================================================
# 3. URL PATTERNS
# ============================================================

urlpatterns = [

    # ========================================================
    # 3.1 STRATEGY & MODEL RESEARCH WORKSPACE
    # ========================================================

    # URL:
    #
    # /strategy/
    #
    # Purpose:
    #
    # Main Strategies page for MarketPulse.
    #
    # This page can contain:
    #
    # - StrategyLibraryItem catalogue
    # - 37 quantitative models
    # - Seven model categories
    # - Search
    # - Filtering
    # - Model comparison
    # - User-created strategies
    # - Backtest summaries
    # - Strategy Robustness access

    path(
        "",
        views.strategy_list,
        name="list",
    ),


    # ========================================================
    # 3.2 CREATE USER STRATEGY
    # ========================================================

    # URL:
    #
    # /strategy/create/
    #
    # Purpose:
    #
    # Allows an authenticated user to create a custom
    # rule-based MarketPulse trading strategy.

    path(
        "create/",
        views.strategy_create,
        name="create",
    ),


    # ========================================================
    # 3.3 ADD MODEL TO STRATEGY LIBRARY
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
    # New entries should normally begin with:
    #
    # implementation_status = "catalogued"
    #
    # until an actual execution engine has been implemented
    # and tested.

    path(
        "library/add/",
        views.library_item_create,
        name="library_add",
    ),


    # ========================================================
    # 3.4 STRATEGY ROBUSTNESS
    # ========================================================

    # URL:
    #
    # /strategy/robustness/
    #
    # User-facing name:
    #
    # Strategy Robustness
    #
    # Technical method:
    #
    # Overfitting Analysis
    #
    # Purpose:
    #
    # Helps the user investigate whether apparently strong
    # historical performance remains reasonably consistent
    # when evaluated over different historical periods.
    #
    # The user should not need to understand the technical
    # term "overfitting" before using this tool.
    #
    # Backend flow:
    #
    # strategy_robustness()
    #       ↓
    # analysis_tools.analyzers.detect_overfitting()
    #       ↓
    # OverfittingTest
    #       ↓
    # PostgreSQL

    path(
        "robustness/",
        views.strategy_robustness,
        name="robustness",
    ),


    # ========================================================
    # 3.5 STRATEGY ROBUSTNESS RESULTS
    # ========================================================

    # URL:
    #
    # /strategy/robustness/results/
    #
    # Purpose:
    #
    # Displays saved Strategy Robustness / Overfitting
    # analysis results in the Strategies area rather than
    # under a separate Analysis navigation tab.

    path(
        "robustness/results/",
        views.strategy_robustness_results,
        name="robustness_results",
    ),


    # ========================================================
    # 3.6 BACKTEST USER STRATEGY
    # ========================================================

    # Example:
    #
    # /strategy/4/backtest/
    #
    # strategy_id identifies the Strategy database record
    # that should be tested using historical market data.

    path(
        "<int:strategy_id>/backtest/",
        views.backtest_strategy,
        name="backtest",
    ),


    # ========================================================
    # 3.7 VIEW BACKTEST RESULTS
    # ========================================================

    # Example:
    #
    # /strategy/results/12/
    #
    # backtest_id identifies the saved Backtest record
    # whose performance metrics should be displayed.

    path(
        "results/<int:backtest_id>/",
        views.backtest_results,
        name="results",
    ),

]