"""
============================================================
MARKETPULSE - DATA MANAGEMENT SERVICES PACKAGE
============================================================

PURPOSE:

This package provides the public service-layer interface
between MarketPulse and external market-data providers.

The current primary market-data provider is:

    Alpaca

Other parts of MarketPulse should import Alpaca functionality
through this services package where practical rather than
communicating with Alpaca directly.


FRAMEWORK MAPPING:

Browser / React / Django Template
        ↓
Django Views / REST API
        ↓
data_management.services
        ↓
data_management/services/alpaca.py
        ↓
Alpaca Trading API
        +
Alpaca Market Data API
        ↓
Normalised Python dictionaries
        ↓
PostgreSQL / Dashboard / Data / Strategies / Risk


WHY THIS FILE EXISTS:

The __init__.py file defines the public interface of the
data_management.services package.

For example, another file can write:

    from data_management.services import get_historical_bars

instead of:

    from data_management.services.alpaca import (
        get_historical_bars
    )

This keeps the rest of the project less tightly coupled to the
internal structure of the Alpaca service module.


CURRENT ALPACA CAPABILITIES:

1. Active US-equity universe
2. Asset search
3. Individual asset metadata
4. Latest stock snapshot
5. Multiple stock snapshots
6. Historical OHLCV market bars
7. US market clock
8. Dashboard benchmark overview
9. Dashboard chart history
10. Alpaca connection testing


SECURITY:

This package does NOT expose Alpaca credentials.

Credentials remain server-side inside:

    .env
        ↓
    marketpulse/settings.py
        ↓
    data_management/services/alpaca.py

The browser should never receive:

    ALPACA_API_KEY_ID

or:

    ALPACA_API_SECRET_KEY

============================================================
"""


# ============================================================
# 1. ALPACA SERVICE ERROR
# ============================================================

# AlpacaServiceError provides one MarketPulse-specific
# exception for communication/configuration problems involving
# Alpaca.
#
# Views and API endpoints can catch this exception and return a
# user-friendly message instead of exposing requests-library
# exceptions or raw Alpaca responses.
from .alpaca import (
    AlpacaServiceError,
)


# ============================================================
# 2. ALPACA ASSET UNIVERSE
# ============================================================

# get_active_us_equities()
#
# Downloads and caches Alpaca's active US-equity universe.
#
# Used primarily by:
#
# Risk asset search
# Data asset search
# API asset-search endpoints
from .alpaca import (
    get_active_us_equities,
)


# ============================================================
# 3. ALPACA ASSET SEARCH
# ============================================================

# search_assets()
#
# Searches Alpaca's cached active-equity universe using:
#
# - ticker
# - company name
# - partial ticker
# - partial company name
#
# Example:
#
# search_assets("Microsoft")
#
# may return MSFT.
from .alpaca import (
    search_assets,
)


# ============================================================
# 4. ALPACA ASSET DETAILS
# ============================================================

# get_asset()
#
# Retrieves Alpaca metadata for one symbol.
#
# Example information:
#
# - symbol
# - company name
# - exchange
# - tradable status
# - shortable status
# - marginable status
# - fractional-share support
from .alpaca import (
    get_asset,
)


# ============================================================
# 5. SINGLE STOCK SNAPSHOT
# ============================================================

# get_stock_snapshot()
#
# Retrieves current/recent market information for one stock.
#
# Framework mapping:
#
# Symbol
#     ↓
# Alpaca snapshot endpoint
#     ↓
# Latest trade
# Latest quote
# Bid / Ask
# Daily bar
# Previous daily bar
#     ↓
# MarketPulse normalised snapshot
#
# Primarily used by:
#
# Risk
# Data
# Dashboard APIs
from .alpaca import (
    get_stock_snapshot,
)


# ============================================================
# 6. MULTIPLE STOCK SNAPSHOTS
# ============================================================

# get_stock_snapshots()
#
# Retrieves several stock snapshots in one Alpaca request.
#
# This is particularly useful for the Dashboard:
#
# SPY
# QQQ
# DIA
# IWM
#
# can be retrieved together rather than through four separate
# HTTP requests.
from .alpaca import (
    get_stock_snapshots,
)


# ============================================================
# 7. HISTORICAL OHLCV MARKET DATA
# ============================================================

# get_historical_bars()
#
# Retrieves historical:
#
# Open
# High
# Low
# Close
# Volume
#
# observations from Alpaca.
#
# Framework mapping:
#
# Alpaca Historical Bars
#     ↓
# get_historical_bars()
#     ↓
# Normalised OHLCV dictionaries
#     ↓
# Data tab
# PostgreSQL MarketData
# Strategy backtesting
# Market Condition
# Risk analytics
# Stress testing
# Dashboard charts
from .alpaca import (
    get_historical_bars,
)


# ============================================================
# 8. US MARKET CLOCK
# ============================================================

# get_market_clock()
#
# Retrieves the Alpaca US market clock.
#
# Information includes:
#
# - current market timestamp
# - whether the US market is open
# - next market open
# - next market close
#
# Dashboard workflow:
#
# Alpaca Trading API
#     ↓
# /v2/clock
#     ↓
# get_market_clock()
#     ↓
# "Market Open" / "Market Closed"
from .alpaca import (
    get_market_clock,
)


# ============================================================
# 9. DASHBOARD MARKET OVERVIEW
# ============================================================

# get_dashboard_market_overview()
#
# Builds the high-level benchmark information used by the
# MarketPulse Dashboard.
#
# Default benchmark universe:
#
# SPY
#     Broad US large-cap market
#
# QQQ
#     Nasdaq-100
#
# DIA
#     Dow Jones
#
# IWM
#     US small-cap equities
#
# The function combines:
#
# Multiple Alpaca stock snapshots
#         +
# Alpaca market clock
#         ↓
# Dashboard market cards
from .alpaca import (
    get_dashboard_market_overview,
)


# ============================================================
# 10. DASHBOARD HISTORICAL CHART
# ============================================================

# get_chart_history()
#
# Retrieves and prepares historical Alpaca data specifically
# for Dashboard Chart.js visualisation.
#
# Example:
#
# get_chart_history(
#     "SPY",
#     "1M",
# )
#
# Dashboard workflow:
#
# User selects SPY
#     ↓
# Dashboard API
#     ↓
# get_chart_history()
#     ↓
# get_historical_bars()
#     ↓
# Alpaca historical bars
#     ↓
# Latest trading sessions
#     ↓
# Chart.js
#
# Supported chart periods currently include:
#
# 1D
# 5D
# 1M
# 3M
from .alpaca import (
    get_chart_history,
)


# ============================================================
# 11. ALPACA CONNECTION TEST
# ============================================================

# test_alpaca_connection()
#
# Provides a safe way to check that MarketPulse can communicate
# with Alpaca without revealing credentials.
#
# Example result:
#
# {
#     "success": True,
#     "provider": "Alpaca",
#     "feed": "IEX",
#     "market_open": False,
#     "message": "MarketPulse connected successfully to Alpaca."
# }
#
# This can later support:
#
# - system diagnostics
# - admin diagnostics
# - deployment checks
# - Dashboard provider-health indicators
from .alpaca import (
    test_alpaca_connection,
)


# ============================================================
# 12. PUBLIC SERVICE INTERFACE
# ============================================================

# __all__ documents the functions that are intentionally
# exposed when other MarketPulse modules import from:
#
#     data_management.services
#
# rather than reaching directly into alpaca.py.
#
# Functions beginning with an underscore inside alpaca.py remain
# private implementation details and are deliberately excluded.
__all__ = [

    # --------------------------------------------------------
    # EXCEPTION
    # --------------------------------------------------------

    "AlpacaServiceError",


    # --------------------------------------------------------
    # ASSET DISCOVERY
    # --------------------------------------------------------

    "get_active_us_equities",

    "search_assets",

    "get_asset",


    # --------------------------------------------------------
    # CURRENT / RECENT MARKET INFORMATION
    # --------------------------------------------------------

    "get_stock_snapshot",

    "get_stock_snapshots",


    # --------------------------------------------------------
    # HISTORICAL MARKET DATA
    # --------------------------------------------------------

    "get_historical_bars",


    # --------------------------------------------------------
    # MARKET STATUS
    # --------------------------------------------------------

    "get_market_clock",


    # --------------------------------------------------------
    # DASHBOARD SERVICES
    # --------------------------------------------------------

    "get_dashboard_market_overview",

    "get_chart_history",


    # --------------------------------------------------------
    # DIAGNOSTICS
    # --------------------------------------------------------

    "test_alpaca_connection",

]