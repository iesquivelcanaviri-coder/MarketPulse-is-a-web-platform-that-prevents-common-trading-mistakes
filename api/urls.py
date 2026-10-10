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
# PROGRAMMING LANGUAGE FEATURES / CONCEPTS USED IN THIS FILE
# ============================================================
#
# This file demonstrates several programming-language
# building blocks from the lecture:
#
# MODULES / IMPORTS
#     Reuse code supplied by Django, Django REST Framework
#     and the local MarketPulse api application.
#
# VARIABLES
#     router and urlpatterns store objects/data for later use.
#
# OBJECTS / CLASSES
#     DefaultRouter is a class and DefaultRouter() creates
#     an object (instance) from that class.
#
# FUNCTION / METHOD CALLS
#     path(), include() and router.register() perform actions.
#
# STRINGS
#     URL patterns such as "health/" and route names such as
#     "health" are Python string values.
#
# LISTS
#     urlpatterns is a Python list containing URL patterns.
#
# ATTRIBUTES
#     views.health and router.urls access members of objects
#     or modules using dot notation.
#
# ARGUMENTS
#     Functions receive positional and keyword arguments.
#
# DYNAMIC PARAMETERS
#     <str:symbol> captures part of a URL and supplies that
#     value to the corresponding Django view.
#
# ABSTRACTION
#     DefaultRouter hides repetitive REST URL-generation work.
#
# SEPARATION OF CONCERNS
#     urls.py decides WHERE a request goes.
#     views.py decides WHAT happens when the request arrives.
#
# ============================================================
# FRAMEWORK CONNECTION
# ============================================================
#
# Browser / React / JavaScript
#           ↓
# Django Project URL Configuration
#           ↓
# api/urls.py
#           ↓
# urlpatterns / DefaultRouter
#           ↓
# api/views.py
#           ↓
# Services / Models / Alpaca / MATLAB
#           ↓
# JSON Response
#
# ============================================================
# 1. DJANGO URL IMPORTS
# ============================================================
#
# PROGRAMMING CONCEPT:
# IMPORTS / MODULE REUSE
#
# Python allows this file to reuse functions defined inside
# Django instead of recreating URL-routing functionality.
#
# include() inserts another collection of URL patterns.
# path() connects a URL pattern to a Django view.
from django.urls import (  # Imports selected names from Django's django.urls module.
    include,  # Imports include(), used to include another group of URL patterns.
    path,  # Imports path(), used to connect a URL route to a Django view.
)

# ============================================================
# 2. DJANGO REST FRAMEWORK IMPORT
# ============================================================
#
# PROGRAMMING CONCEPT:
# CLASS IMPORT / ABSTRACTION
#
# DefaultRouter is a Django REST Framework class that can
# automatically build REST-style URLs for ViewSets.
from rest_framework.routers import (  # Imports routing functionality from Django REST Framework.
    DefaultRouter,  # Imports the DefaultRouter class used to generate REST API routes automatically.
)

# ============================================================
# 3. MARKETPULSE API VIEWS
# ============================================================
#
# PROGRAMMING CONCEPT:
# RELATIVE IMPORT / MODULE
#
# "." means the current Python package.
#
# Therefore:
#
# from . import views
#
# means:
#
# Import api/views.py from this Django application.
from . import views  # Imports the local api/views.py module so its views can be connected to URLs.

# ============================================================
# 4. DJANGO REST FRAMEWORK ROUTER
# ============================================================
#
# PROGRAMMING CONCEPT:
# VARIABLE + OBJECT CREATION + CONSTRUCTOR CALL
#
# DefaultRouter
#     = class
#
# DefaultRouter()
#     = creates an object from that class
#
# router
#     = variable storing that object
router = (  # Creates the variable named router and begins the expression assigned to it.
    DefaultRouter()  # Calls the DefaultRouter class constructor and creates a router object.
)

# ------------------------------------------------------------
# 4.1 STRATEGY API
# ------------------------------------------------------------
#
# PROGRAMMING CONCEPT:
# METHOD CALL + OBJECT ATTRIBUTE
#
# router.register(...)
#
# register() is a method belonging to the router object.
#
# Automatically creates routes including:
#
# /api/strategies/
# /api/strategies/<id>/
#
# These endpoints expose strategy information through
# Django REST Framework.
router.register(  # Calls the register() method on the router object.
    "strategies",  # String argument defining the URL prefix generated by the router.
    views.StrategyViewSet,  # References StrategyViewSet from api/views.py.
    basename="strategy-api",  # Keyword argument defining the base name of generated URL names.
)

# ------------------------------------------------------------
# 4.2 BACKTEST API
# ------------------------------------------------------------
#
# PROGRAMMING CONCEPT:
# METHOD CALL + ARGUMENTS
#
# This repeats the same programming pattern used above but
# registers a different ViewSet.
#
# Automatically creates routes including:
#
# /api/backtests/
# /api/backtests/<id>/
#
# These endpoints expose backtest information through
# Django REST Framework.
router.register(  # Calls register() again to add another resource to the same router.
    "backtests",  # String argument defining the backtests URL prefix.
    views.BacktestViewSet,  # References BacktestViewSet from api/views.py.
    basename="backtest-api",  # Gives the generated backtest URLs their base URL name.
)

# ============================================================
# 5. API URL PATTERNS
# ============================================================
#
# PROGRAMMING CONCEPT:
# VARIABLE + LIST
#
# urlpatterns is a special Django variable.
#
# Django looks through this list when deciding which view
# should handle an incoming HTTP request.
#
# Simplified logic:
#
# Incoming URL
#     ↓
# Django checks urlpatterns from top to bottom
#     ↓
# Matching path found
#     ↓
# Matching view is called
#
# Each path(...) call produces a URLPattern object.
urlpatterns = [  # Creates the Django urlpatterns list that stores this application's explicit URL routes.

    # ========================================================
    # 5.1 APPLICATION HEALTH
    # ========================================================
    #
    # PROGRAMMING CONCEPTS:
    #
    # FUNCTION CALL
    #     path(...)
    #
    # STRING
    #     "health/"
    #
    # ATTRIBUTE ACCESS
    #     views.health
    #
    # KEYWORD ARGUMENT
    #     name="health"
    #
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
    path(  # Calls Django's path() function to create one URL rule.
        "health/",  # String defining the URL fragment Django should match.
        views.health,  # Passes the health view function that handles a matching request.
        name="health",  # Gives this route a reusable Django URL name.
    ),  # Ends this path() call and adds its result to urlpatterns.

    # ========================================================
    # 5.2 DASHBOARD - LIVE MARKET OVERVIEW
    # ========================================================
    #
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
    #
    # PROGRAMMING CONCEPT:
    # URL ROUTING
    #
    # Django maps one URL string to one callable view.
    path(  # Creates the Dashboard market-overview URL rule.
        "dashboard/market-overview/",  # Defines the URL fragment matched by Django.
        views.dashboard_market_overview,  # References the view function that processes the request.
        name="dashboard_market_overview",  # Assigns a reusable Django name to this URL.
    ),  # Finishes the dashboard market-overview URL pattern.

    # ========================================================
    # 5.3 STORED MARKET DATA
    # ========================================================
    #
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
    #
    # PROGRAMMING CONCEPT:
    # FUNCTION REFERENCE
    #
    # Notice that the code uses:
    #
    # views.market_latest
    #
    # and NOT:
    #
    # views.market_latest()
    #
    # Django receives the function itself so it can call the
    # function later when a request reaches this URL.
    path(  # Creates the stored-market-data URL rule.
        "market/latest/",  # Defines the URL fragment for retrieving latest stored market data.
        views.market_latest,  # Supplies the market_latest view function as the request handler.
        name="market_latest",  # Gives the URL pattern the name market_latest.
    ),  # Ends the stored-market-data path() call.

    # ========================================================
    # 5.4 RISK MANAGEMENT - POSITION SIZE
    # ========================================================
    #
    # Browser / API URL:
    #
    # /api/risk/position-size/
    #
    # Purpose:
    #
    # Accepts risk-calculation inputs and returns position-size
    # and stop-loss information.
    #
    # PROGRAMMING CONCEPT:
    # MAPPING INPUT TO BEHAVIOUR
    #
    # URL input:
    #
    # risk/position-size/
    #
    # is mapped to:
    #
    # views.risk_position_size
    path(  # Creates the position-size risk API URL pattern.
        "risk/position-size/",  # String containing the route Django should match.
        views.risk_position_size,  # References the risk_position_size view handling the request.
        name="risk_position_size",  # Creates a reusable Django URL name for this route.
    ),  # Ends the risk position-size URL pattern.

    # ========================================================
    # 5.5 MATLAB RISK INTEGRATION
    # ========================================================
    #
    # Browser / API URL:
    #
    # /api/matlab/risk/
    #
    # Purpose:
    #
    # Provides access to the optional MATLAB risk bridge.
    #
    # FRAMEWORK FLOW:
    #
    # HTTP request
    #     ↓
    # Django URL
    #     ↓
    # views.matlab_risk
    #     ↓
    # MATLAB integration
    path(  # Creates the URL rule for the MATLAB risk integration.
        "matlab/risk/",  # Defines the URL fragment used to access MATLAB risk functionality.
        views.matlab_risk,  # References the Django view responsible for MATLAB risk requests.
        name="matlab_risk",  # Assigns the Django URL name matlab_risk.
    ),  # Finishes the MATLAB risk route.

    # ========================================================
    # 5.6 ALPACA - ASSET SEARCH
    # ========================================================
    #
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
    #
    # PROGRAMMING CONCEPT:
    # QUERY PARAMETERS
    #
    # The route identifies the view:
    #
    # alpaca/assets/search/
    #
    # Values after "?" such as:
    #
    # ?q=AAPL
    #
    # are query-string inputs that the view can read from
    # the incoming HTTP request.
    path(  # Creates the Alpaca asset-search API URL pattern.
        "alpaca/assets/search/",  # Defines the static URL fragment for asset searches.
        views.alpaca_asset_search,  # Connects the route to the alpaca_asset_search view.
        name="alpaca_asset_search",  # Assigns the Django URL name alpaca_asset_search.
    ),  # Finishes the Alpaca asset-search path.

    # ========================================================
    # 5.7 ALPACA - ASSET DETAILS
    # ========================================================
    #
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
    #
    # PROGRAMMING CONCEPT:
    # DYNAMIC URL PARAMETER
    #
    # <str:symbol>
    #
    # means:
    #
    # 1. Capture part of the URL.
    # 2. Treat that value as a Python string.
    # 3. Store it using the parameter name "symbol".
    # 4. Pass it to the selected Django view.
    #
    # Example:
    #
    # URL:
    # /api/alpaca/assets/AAPL/
    #
    # Captured value:
    # symbol = "AAPL"
    path(  # Creates a dynamic route for retrieving one Alpaca asset.
        "alpaca/assets/<str:symbol>/",  # Captures the URL section as a string named symbol.
        views.alpaca_asset_detail,  # Connects the dynamic route to the asset-detail view.
        name="alpaca_asset_detail",  # Gives the route the Django name alpaca_asset_detail.
    ),  # Ends the Alpaca asset-detail route.

    # ========================================================
    # 5.8 ALPACA - CURRENT STOCK SNAPSHOT
    # ========================================================
    #
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
    #
    # PROGRAMMING CONCEPT:
    # PARAMETERISATION
    #
    # One route can work with many symbols because symbol is
    # supplied dynamically.
    #
    # AAPL:
    # alpaca/stocks/AAPL/snapshot/
    #
    # MSFT:
    # alpaca/stocks/MSFT/snapshot/
    #
    # NVDA:
    # alpaca/stocks/NVDA/snapshot/
    path(  # Creates the dynamic stock-snapshot API route.
        "alpaca/stocks/<str:symbol>/snapshot/",  # Captures the requested stock ticker into symbol.
        views.alpaca_stock_snapshot,  # Sends matching requests to alpaca_stock_snapshot.
        name="alpaca_stock_snapshot",  # Assigns a reusable Django name to the snapshot route.
    ),  # Ends the Alpaca stock-snapshot URL pattern.

    # ========================================================
    # 5.9 ALPACA - HISTORICAL STOCK OHLCV
    # ========================================================
    #
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
    # Purpose:
    #
    # Returns historical Alpaca OHLCV observations for the
    # selected stock or ETF.
    #
    # OHLCV:
    #
    # O = Open
    # H = High
    # L = Low
    # C = Close
    # V = Volume
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
    #
    # PROGRAMMING CONCEPT:
    # COMBINING PATH PARAMETERS + QUERY PARAMETERS
    #
    # Example:
    #
    # /api/alpaca/stocks/AAPL/history/?period=1M
    #
    # Dynamic path parameter:
    #
    # symbol = "AAPL"
    #
    # Query parameter:
    #
    # period = "1M"
    #
    # These values can both be used by the view to determine
    # what historical data should be returned.
    path(  # Creates the dynamic historical stock-data API route.
        "alpaca/stocks/<str:symbol>/history/",  # Captures the ticker symbol from the requested URL.
        views.alpaca_stock_history,  # Sends the request to alpaca_stock_history in api/views.py.
        name="alpaca_stock_history",  # Gives this route the Django name alpaca_stock_history.
    ),  # Ends the Alpaca historical-stock-data URL pattern.

    # ========================================================
    # 5.10 DJANGO REST FRAMEWORK ROUTES
    # ========================================================
    #
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
    #
    # PROGRAMMING CONCEPT:
    # COMPOSITION / REUSE
    #
    # router.urls already contains the URL patterns generated
    # by DefaultRouter.
    #
    # include(router.urls)
    #
    # tells Django to include those generated URLs inside the
    # urlpatterns list used by this application.
    #
    # This avoids manually writing every REST route.
    path(  # Creates a URL entry that includes the router-generated API patterns.
        "",  # Empty string means the router URLs begin directly at this URLconf's current root.
        include(  # Calls include() so Django can add the router's collection of URL patterns.
            router.urls  # Accesses the URLs automatically generated by the DefaultRouter object.
        ),  # Ends include(router.urls).
    ),  # Ends the path containing the Django REST Framework router.
]  # Ends the urlpatterns Python list.