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

Browser / React
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
from django.urls import include, path


# ============================================================
# 2. DJANGO REST FRAMEWORK IMPORT
# ============================================================

# DefaultRouter automatically generates conventional REST API
# routes for registered ViewSets.
from rest_framework.routers import DefaultRouter


# ============================================================
# 3. MARKETPULSE API VIEWS
# ============================================================

# Imports views.py from the current api Django application.
from . import views


# ============================================================
# 4. DJANGO REST FRAMEWORK ROUTER
# ============================================================

router = DefaultRouter()


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

    # Browser/API URL:
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

    # Browser/API URL:
    #
    # /api/dashboard/market-overview/
    #
    #
    # PURPOSE:
    #
    # This is the main dynamic-data endpoint for the upgraded
    # MarketPulse Dashboard.
    #
    # It should provide the information needed by the live
    # Dashboard Market Pulse component.
    #
    #
    # EXPECTED INFORMATION:
    #
    # MARKET STATUS
    #
    # - Whether the US equity market is open or closed
    # - Next market open
    # - Next market close
    #
    #
    # MARKET BENCHMARKS
    #
    # - SPY
    # - QQQ
    # - DIA
    # - IWM
    #
    #
    # For each benchmark the response can include:
    #
    # - Latest price
    # - Previous close
    # - Daily change
    # - Daily percentage change
    # - Day open
    # - Day high
    # - Day low
    # - Day volume
    #
    #
    # DASHBOARD CHART
    #
    # The endpoint can also provide historical/recent bars
    # for the Dashboard chart.
    #
    # Example:
    #
    # SPY
    #     ↓
    # Timestamp
    # Open
    # High
    # Low
    # Close
    # Volume
    #
    #
    # DATA PROVENANCE
    #
    # The response should identify:
    #
    # - Provider: Alpaca
    # - Feed: IEX
    # - Last-updated timestamp
    #
    #
    # FRONTEND WORKFLOW:
    #
    # Dashboard JavaScript / React
    #         ↓
    # GET /api/dashboard/market-overview/
    #         ↓
    # dashboard_market_overview()
    #         ↓
    # data_management.services.alpaca
    #         ↓
    # Alpaca Market Data API
    #
    #
    # AUTOMATIC REFRESH:
    #
    # The frontend can call this endpoint periodically,
    # for example every 60 seconds, without reloading the
    # entire Dashboard page.
    #
    #
    # SECURITY:
    #
    # No Alpaca credentials are returned in the JSON.
    path(
        "dashboard/market-overview/",
        views.dashboard_market_overview,
        name="dashboard_market_overview",
    ),


    # ========================================================
    # 5.3 STORED MARKET DATA
    # ========================================================

    # Browser/API URL:
    #
    # /api/market/latest/
    #
    #
    # PURPOSE:
    #
    # Returns the latest historical market observations that
    # have already been persisted inside MarketPulse.
    #
    #
    # IMPORTANT DISTINCTION:
    #
    # /api/dashboard/market-overview/
    #
    #     = current/recent external market information
    #       obtained through Alpaca.
    #
    #
    # /api/market/latest/
    #
    #     = persisted MarketData records stored in
    #       PostgreSQL.
    #
    #
    # Keeping those responsibilities separate makes the data
    # architecture easier to understand and maintain.
    path(
        "market/latest/",
        views.market_latest,
        name="market_latest",
    ),


    # ========================================================
    # 5.4 RISK MANAGEMENT - POSITION SIZE
    # ========================================================

    # Browser/API URL:
    #
    # /api/risk/position-size/
    #
    #
    # PURPOSE:
    #
    # Provides a REST-style endpoint for MarketPulse
    # position-sizing calculations.
    #
    # This can be consumed by:
    #
    # - Risk page JavaScript
    # - React components
    # - Other MarketPulse interfaces
    path(
        "risk/position-size/",
        views.risk_position_size,
        name="risk_position_size",
    ),


    # ========================================================
    # 5.5 MATLAB RISK INTEGRATION
    # ========================================================

    # Browser/API URL:
    #
    # /api/matlab/risk/
    #
    #
    # PURPOSE:
    #
    # Provides the API integration point for MATLAB-based
    # quantitative calculations when MATLAB support is
    # enabled in MarketPulse.
    path(
        "matlab/risk/",
        views.matlab_risk,
        name="matlab_risk",
    ),


    # ========================================================
    # 5.6 ALPACA - ASSET SEARCH
    # ========================================================

    # Browser/API URL examples:
    #
    # /api/alpaca/assets/search/?q=AAPL
    #
    # /api/alpaca/assets/search/?q=Microsoft
    #
    # /api/alpaca/assets/search/?q=NVIDIA
    #
    #
    # PURPOSE:
    #
    # Searches Alpaca's active US-equity asset universe.
    #
    #
    # RETURNED INFORMATION CAN INCLUDE:
    #
    # - Symbol
    # - Company / asset name
    # - Exchange
    # - Trading status
    # - Tradability
    # - Marginability
    # - Shortability
    # - Fractional-trading availability
    # - Borrow information where available
    #
    #
    # ARCHITECTURE:
    #
    # Browser
    #     ↓
    # MarketPulse API
    #     ↓
    # Alpaca service
    #     ↓
    # Alpaca
    #
    # The browser never communicates directly with Alpaca.
    path(
        "alpaca/assets/search/",
        views.alpaca_asset_search,
        name="alpaca_asset_search",
    ),


    # ========================================================
    # 5.7 ALPACA - ASSET DETAILS
    # ========================================================

    # Browser/API URL:
    #
    # /api/alpaca/assets/AAPL/
    #
    #
    # PURPOSE:
    #
    # Retrieves metadata for one Alpaca asset.
    #
    #
    # INFORMATION CAN INCLUDE:
    #
    # - Symbol
    # - Asset name
    # - Exchange
    # - Asset status
    # - Tradability
    # - Marginability
    # - Shortability
    # - Fractionability
    # - Borrow information where available
    path(
        "alpaca/assets/<str:symbol>/",
        views.alpaca_asset_detail,
        name="alpaca_asset_detail",
    ),


    # ========================================================
    # 5.8 ALPACA - STOCK MARKET SNAPSHOT
    # ========================================================

    # Browser/API URL:
    #
    # /api/alpaca/stocks/AAPL/snapshot/
    #
    #
    # PURPOSE:
    #
    # Retrieves current/latest market information for a single
    # stock through the MarketPulse backend.
    #
    #
    # INFORMATION CAN INCLUDE:
    #
    # LATEST TRADE
    #
    # - Price
    # - Timestamp
    #
    #
    # LATEST QUOTE
    #
    # - Bid price
    # - Ask price
    # - Bid/ask spread
    #
    #
    # CURRENT MARKET BAR
    #
    # - Open
    # - High
    # - Low
    # - Close
    # - Volume
    #
    #
    # PREVIOUS MARKET BAR
    #
    # - Previous open
    # - Previous high
    # - Previous low
    # - Previous close
    # - Previous volume
    #
    #
    # DERIVED INFORMATION
    #
    # - Daily price change
    # - Daily percentage change
    #
    #
    # PROVIDER INFORMATION
    #
    # - Alpaca
    # - Market-data feed
    path(
        "alpaca/stocks/<str:symbol>/snapshot/",
        views.alpaca_stock_snapshot,
        name="alpaca_stock_snapshot",
    ),


    # ========================================================
    # 5.9 DJANGO REST FRAMEWORK ROUTES
    # ========================================================

    # The REST Framework router is deliberately placed after
    # the explicit MarketPulse API routes.
    #
    # This keeps specific API paths easy to identify before
    # the more general ViewSet routes are included.
    #
    #
    # Automatically generated examples:
    #
    # /api/strategies/
    #
    # /api/strategies/<id>/
    #
    # /api/backtests/
    #
    # /api/backtests/<id>/
    path(
        "",
        include(
            router.urls
        ),
    ),

]