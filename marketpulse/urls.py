"""
============================================================
MARKETPULSE - ROOT URL ROUTER
============================================================

Framework mapping:

Browser Request
        ↓
marketpulse/urls.py
        ↓
Individual Django Apps

Visible application areas:

Home
Dashboard
Accounts
Data
Strategies
Risk
API

The old public /analysis/ route has been removed.

The analysis_tools app remains installed internally because
its models and analytical functions are still used by:

Data
    → Market Condition / Regime Analysis

Strategies
    → Strategy Robustness / Overfitting Analysis

Risk
    → Stress Testing
============================================================
"""

from django.contrib import admin
from django.urls import include, path

from core import views as core_views


# ============================================================
# ROOT URL PATTERNS
# ============================================================

urlpatterns = [

    # --------------------------------------------------------
    # Django Administration
    # --------------------------------------------------------

    path(
        "admin/",
        admin.site.urls,
    ),


    # --------------------------------------------------------
    # Public Home Page
    # --------------------------------------------------------

    path(
        "",
        core_views.home,
        name="home",
    ),


    # --------------------------------------------------------
    # Main Dashboard
    # --------------------------------------------------------

    path(
        "dashboard/",
        core_views.dashboard,
        name="dashboard",
    ),


    # --------------------------------------------------------
    # Accounts
    # --------------------------------------------------------

    path(
        "accounts/",
        include("accounts.urls"),
    ),


    # --------------------------------------------------------
    # Data Management
    #
    # Includes:
    #
    # - Historical market data
    # - Data imports
    # - Market condition / regime analysis
    # --------------------------------------------------------

    path(
        "data/",
        include("data_management.urls"),
    ),


    # --------------------------------------------------------
    # Strategy Builder
    #
    # Includes:
    #
    # - Strategy & model library
    # - User-created strategies
    # - Backtesting
    # - Strategy robustness / overfitting analysis
    # --------------------------------------------------------

    path(
        "strategy/",
        include("strategy_builder.urls"),
    ),


    # --------------------------------------------------------
    # Risk Management
    #
    # Includes:
    #
    # - Trade Risk Planner
    # - Position sizing
    # - Stop-loss analysis
    # - Stress testing
    # --------------------------------------------------------

    path(
        "risk/",
        include("risk_management.urls"),
    ),


    # --------------------------------------------------------
    # REST API
    #
    # Includes:
    #
    # - Alpaca market-data integration
    # - Other MarketPulse API endpoints
    # --------------------------------------------------------

    path(
        "api/",
        include("api.urls"),
    ),

]