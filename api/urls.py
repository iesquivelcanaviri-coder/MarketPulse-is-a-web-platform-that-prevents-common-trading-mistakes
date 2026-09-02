"""
============================================================
MARKETPULSE - API URLS
============================================================

Purpose:

The /api/ application provides REST-style endpoints used by:

- Django JavaScript
- React frontend components
- MarketPulse internal services
- External integrations where appropriate

Architecture:

Frontend
    ↓
/api/
    ↓
Django API views
    ↓
Service layer
    ↓
PostgreSQL / Alpaca / MATLAB

Alpaca API credentials are NEVER exposed through these URLs.
All Alpaca communication happens server-side.
============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import views


# ============================================================
# 2. DJANGO REST FRAMEWORK ROUTER
# ============================================================

router = DefaultRouter()


# ------------------------------------------------------------
# Strategy API
# ------------------------------------------------------------

router.register(
    "strategies",
    views.StrategyViewSet,
    basename="strategy-api",
)


# ------------------------------------------------------------
# Backtest API
# ------------------------------------------------------------

router.register(
    "backtests",
    views.BacktestViewSet,
    basename="backtest-api",
)


# ============================================================
# 3. API URL PATTERNS
# ============================================================

urlpatterns = [

    # ========================================================
    # SYSTEM / HEALTH
    # ========================================================

    path(
        "health/",
        views.health,
        name="health",
    ),


    # ========================================================
    # MARKET DATA
    # ========================================================

    path(
        "market/latest/",
        views.market_latest,
        name="market_latest",
    ),


    # ========================================================
    # RISK MANAGEMENT
    # ========================================================

    path(
        "risk/position-size/",
        views.risk_position_size,
        name="risk_position_size",
    ),


    # ========================================================
    # MATLAB INTEGRATION
    # ========================================================

    path(
        "matlab/risk/",
        views.matlab_risk,
        name="matlab_risk",
    ),


    # ========================================================
    # ALPACA - ASSET SEARCH
    # ========================================================

    # Example:
    #
    # /api/alpaca/assets/search/?q=microsoft
    #
    # Returns matching Alpaca assets such as:
    #
    # MSFT
    # Microsoft Corporation
    # NASDAQ
    # Tradable
    #
    # The browser talks to MarketPulse.
    # MarketPulse then talks securely to Alpaca.

    path(
        "alpaca/assets/search/",
        views.alpaca_asset_search,
        name="alpaca_asset_search",
    ),


    # ========================================================
    # ALPACA - ASSET DETAILS
    # ========================================================

    # Example:
    #
    # /api/alpaca/assets/AAPL/
    #
    # Can return:
    #
    # symbol
    # company / asset name
    # exchange
    # active status
    # tradable
    # marginable
    # shortable
    # fractionable

    path(
        "alpaca/assets/<str:symbol>/",
        views.alpaca_asset_detail,
        name="alpaca_asset_detail",
    ),


    # ========================================================
    # ALPACA - STOCK MARKET SNAPSHOT
    # ========================================================

    # Example:
    #
    # /api/alpaca/stocks/AAPL/snapshot/
    #
    # Can return:
    #
    # latest trade price
    # latest bid
    # latest ask
    # spread
    # minute bar
    # current daily OHLCV
    # previous daily OHLCV
    # provider/feed metadata

    path(
        "alpaca/stocks/<str:symbol>/snapshot/",
        views.alpaca_stock_snapshot,
        name="alpaca_stock_snapshot",
    ),


    # ========================================================
    # DJANGO REST FRAMEWORK ROUTES
    # ========================================================

    # Includes automatically generated routes such as:
    #
    # /api/strategies/
    # /api/backtests/

    path(
        "",
        include(
            router.urls
        ),
    ),
]