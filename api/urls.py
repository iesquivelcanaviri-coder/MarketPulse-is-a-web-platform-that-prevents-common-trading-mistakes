"""
============================================================
MARKETPULSE - API URL CONFIGURATION
============================================================

PURPOSE:

The MarketPulse API layer provides REST-style endpoints used
by the application's dynamic frontend features.

These endpoints can be consumed by:

- Django JavaScript
- React components
- MarketPulse internal services
- Development/testing tools
- External integrations where appropriate


============================================================
ARCHITECTURE
============================================================

Browser / React / Dashboard JavaScript
        ↓
      /api/
        ↓
     API Views
        ↓
MarketPulse Services
        ↓
 ┌───────────────┬───────────────┬───────────────┐
 ↓               ↓               ↓
PostgreSQL      Alpaca          MATLAB


============================================================
MARKET DATA FLOW
============================================================

Dashboard
    ↓
MarketPulse API
    ↓
Alpaca Service Layer
    ↓
Alpaca API
    ↓
Normalised JSON
    ↓
Search / Watchlist / Charts / Alerts


Current market snapshot:

    /api/alpaca/stocks/AAPL/snapshot/

Historical OHLCV chart data:

    /api/alpaca/stocks/AAPL/history/?period=1M

Asset search:

    /api/alpaca/assets/search/?q=Apple


============================================================
PROFESSIONAL CHART WORKSPACE
============================================================

The new Dashboard chart workspace can use:

Asset Search
    ↓
/api/alpaca/assets/search/

Selected Asset
    ↓
/api/alpaca/stocks/<symbol>/snapshot/

Historical Chart
    ↓
/api/alpaca/stocks/<symbol>/history/

The historical endpoint supplies OHLCV observations suitable
for:

- Candlestick charts
- Line charts
- Heikin-Ashi calculations
- Volume charts
- Future Volume Profile calculations


IMPORTANT:

A Futures Curve requires actual futures-contract market data
and should not be constructed from ordinary stock or ETF
historical bars.


============================================================
SECURITY
============================================================

Alpaca credentials are NEVER sent to the browser.

The secure workflow is:

Browser
    ↓
MarketPulse API
    ↓
Django backend
    ↓
Alpaca service
    ↓
Alpaca API


The following values stay on the server:

ALPACA_API_KEY_ID
ALPACA_API_SECRET_KEY


They must be stored using environment variables and must
never be placed inside:

- HTML
- JavaScript
- React source code
- GitHub
- API responses

============================================================
"""


# ============================================================
# 1. DJANGO URL IMPORTS
# ============================================================

# include() allows automatically generated Django REST
# Framework router URLs to be included with the manually
# defined MarketPulse API routes.
#
# path() connects a URL address to a Django view.
from django.urls import (
    include,
    path,
)


# ============================================================
# 2. DJANGO REST FRAMEWORK IMPORT
# ============================================================

# DefaultRouter automatically generates conventional REST API
# routes for registered ViewSets.
from rest_framework.routers import (
    DefaultRouter,
)


# ============================================================
# 3. MARKETPULSE API VIEWS
# ============================================================

# Imports views.py from the current api Django application.
from . import views


# ============================================================
# 4. DJANGO REST FRAMEWORK ROUTER
# ============================================================

router = (
    DefaultRouter()
)


# ------------------------------------------------------------
# 4.1 STRATEGY API
# ------------------------------------------------------------

# Automatically creates routes including:
#
# /api/strategies/
# /api/strategies/<id>/
#
# These endpoints expose strategy information through
# Django REST Framework.
router.register(
    "strategies",
    views.StrategyViewSet,
    basename="strategy-api",
)


# ------------------------------------------------------------
# 4.2 BACKTEST API
# ------------------------------------------------------------

# Automatically creates routes including:
#
# /api/backtests/
# /api/backtests/<id>/
#
# These endpoints expose backtest information through
# Django REST Framework.
router.register(
    "backtests",
    views.BacktestViewSet,
    basename="backtest-api",
)


# ============================================================
# 5. API URL PATTERNS
# ============================================================

urlpatterns = [


    # ========================================================
    # 5.1 APPLICATION HEALTH
    # ========================================================

    # Browser / API URL:
    #
    # /api/health/
    #
    # Purpose:
    #
    # Provides a lightweight endpoint for checking whether
    # the Django API application is responding.
    #
    # This can be useful during:
    #
    # - Local development
    # - Render deployment
    # - Basic service monitoring
    path(
        "health/",
        views.health,
        name="health",
    ),


    # ========================================================
    # 5.2 DASHBOARD - LIVE MARKET OVERVIEW
    # ========================================================

    # Browser / API URL:
    #
    # /api/dashboard/market-overview/
    #
    # Examples:
    #
    # /api/dashboard/market-overview/?symbol=SPY
    #
    # /api/dashboard/market-overview/?symbol=QQQ&period=1M
    #
    # Purpose:
    #
    # Provides:
    #
    # - US market clock
    # - SPY snapshot
    # - QQQ snapshot
    # - DIA snapshot
    # - IWM snapshot
    # - benchmark comparison
    # - historical benchmark graph information
    # - Dashboard market condition
    # - notices
    # - data-health information
    #
    # Alpaca credentials remain on the Django server.
    path(
        "dashboard/market-overview/",
        views.dashboard_market_overview,
        name="dashboard_market_overview",
    ),


    # ========================================================
    # 5.3 STORED MARKET DATA
    # ========================================================

    # Browser / API URL:
    #
    # /api/market/latest/
    #
    # Example:
    #
    # /api/market/latest/?symbol=AAPL&limit=60
    #
    # Purpose:
    #
    # Returns MarketData observations already persisted inside
    # MarketPulse PostgreSQL storage.
    path(
        "market/latest/",
        views.market_latest,
        name="market_latest",
    ),


    # ========================================================
    # 5.4 RISK MANAGEMENT - POSITION SIZE
    # ========================================================

    # Browser / API URL:
    #
    # /api/risk/position-size/
    #
    # Purpose:
    #
    # Accepts risk-calculation inputs and returns position-size
    # and stop-loss information.
    path(
        "risk/position-size/",
        views.risk_position_size,
        name="risk_position_size",
    ),


    # ========================================================
    # 5.5 MATLAB RISK INTEGRATION
    # ========================================================

    # Browser / API URL:
    #
    # /api/matlab/risk/
    #
    # Purpose:
    #
    # Provides access to the optional MATLAB risk bridge.
    path(
        "matlab/risk/",
        views.matlab_risk,
        name="matlab_risk",
    ),


    # ========================================================
    # 5.6 ALPACA - ASSET SEARCH
    # ========================================================

    # Browser / API examples:
    #
    # /api/alpaca/assets/search/?q=AAPL
    #
    # /api/alpaca/assets/search/?q=Microsoft
    #
    # /api/alpaca/assets/search/?q=Tesla
    #
    # Purpose:
    #
    # Powers the Dashboard stock/ETF search box and future
    # watchlist interface.
    path(
        "alpaca/assets/search/",
        views.alpaca_asset_search,
        name="alpaca_asset_search",
    ),


    # ========================================================
    # 5.7 ALPACA - ASSET DETAILS
    # ========================================================

    # Browser / API URL example:
    #
    # /api/alpaca/assets/AAPL/
    #
    # Purpose:
    #
    # Returns descriptive information about an Alpaca asset,
    # including:
    #
    # - symbol
    # - name
    # - exchange
    # - asset class
    # - tradability
    # - shortability
    # - fractionability
    path(
        "alpaca/assets/<str:symbol>/",
        views.alpaca_asset_detail,
        name="alpaca_asset_detail",
    ),


    # ========================================================
    # 5.8 ALPACA - CURRENT STOCK SNAPSHOT
    # ========================================================

    # Browser / API URL example:
    #
    # /api/alpaca/stocks/AAPL/snapshot/
    #
    # Purpose:
    #
    # Returns current/latest information including:
    #
    # - latest price
    # - bid
    # - ask
    # - spread
    # - daily OHLC
    # - previous close
    # - daily change
    #
    # This endpoint supplies the selected-asset information
    # shown above the professional chart.
    path(
        "alpaca/stocks/<str:symbol>/snapshot/",
        views.alpaca_stock_snapshot,
        name="alpaca_stock_snapshot",
    ),


    # ========================================================
    # 5.9 ALPACA - HISTORICAL STOCK OHLCV
    # ========================================================

    # Browser / API examples:
    #
    # /api/alpaca/stocks/AAPL/history/?period=1M
    #
    # /api/alpaca/stocks/MSFT/history/?period=3M
    #
    # /api/alpaca/stocks/NVDA/history/?period=5D
    #
    # /api/alpaca/stocks/SPY/history/?period=1D
    #
    #
    # Purpose:
    #
    # Returns historical Alpaca OHLCV observations for the
    # selected stock or ETF.
    #
    # Framework mapping:
    #
    # Search / Watchlist
    #       ↓
    # Selected Symbol
    #       ↓
    # /api/alpaca/stocks/<symbol>/history/
    #       ↓
    # api.views.alpaca_stock_history
    #       ↓
    # get_chart_history()
    #       ↓
    # Alpaca Historical Market Data API
    #       ↓
    # JSON OHLCV
    #       ↓
    # Professional Dashboard Chart
    #
    #
    # This endpoint will support:
    #
    # - Candlestick chart
    # - Line chart
    # - Heikin-Ashi chart
    # - Volume chart
    #
    # Volume Profile can later be calculated from the returned
    # price and volume observations.
    #
    # Futures Curve is deliberately NOT handled by this route
    # because that requires actual futures-contract data.
    path(
        "alpaca/stocks/<str:symbol>/history/",
        views.alpaca_stock_history,
        name="alpaca_stock_history",
    ),


    # ========================================================
    # 5.10 DJANGO REST FRAMEWORK ROUTES
    # ========================================================

    # The router is deliberately placed AFTER the explicit
    # MarketPulse API routes.
    #
    # This prevents automatically generated router patterns
    # from making the API layout harder to reason about.
    #
    # Automatically exposes:
    #
    # /api/strategies/
    # /api/strategies/<id>/
    #
    # /api/backtests/
    # /api/backtests/<id>/
    path(
        "",
        include(
            router.urls
        ),
    ),

]