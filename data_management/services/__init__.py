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
data_management/services/__init__.py
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


HOW THIS FILE INTERACTS WITH THE PROJECT:

This file does not contact Alpaca itself.

Instead, it imports selected functions and classes from:

    data_management/services/alpaca.py

and makes them available through:

    data_management.services


Example:

Instead of another MarketPulse file needing:

    from data_management.services.alpaca import (
        get_historical_bars
    )

it can use:

    from data_management.services import get_historical_bars


This creates a cleaner service-layer boundary:

View / API
    ↓
services package
    ↓
Alpaca implementation
    ↓
External Alpaca API


WHY THIS FILE EXISTS:

The __init__.py file makes:

    data_management/services/

a Python package and defines its public service interface.

It helps keep the rest of MarketPulse less tightly coupled to
the internal organisation of alpaca.py.


PROGRAMMING LANGUAGE CONCEPTS USED:

1. Package
   A folder containing related Python modules.

2. Module
   A Python file such as alpaca.py.

3. Import
   Makes code defined in another module available here.

4. Relative import
   .alpaca means:
   import from alpaca.py inside this same package.

5. Exception class
   AlpacaServiceError represents a specific type of failure.

6. Function
   Functions such as get_asset() and get_historical_bars()
   perform reusable operations.

7. List
   __all__ is a Python list containing strings.

8. String
   Each name inside __all__ is represented as text.

9. Public interface
   __all__ documents which names form the intended external
   interface of this package.


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
#
# PROGRAMMING CONCEPT:
# Importing a class from another module.
#
# AlpacaServiceError is a custom Python exception.
#
# It lets MarketPulse distinguish an Alpaca-specific problem
# from another general Python error.
#
# Example framework interaction:
#
# alpaca.py
#     ↓
# raises AlpacaServiceError
#     ↓
# Django View / API catches error
#     ↓
# User receives a friendly error message
# ============================================================

from .alpaca import (  # Relative import: read from alpaca.py inside this package.
    AlpacaServiceError,  # Class: custom exception used for Alpaca service errors.
)


# ============================================================
# 2. ALPACA ASSET UNIVERSE
# ============================================================
#
# PROGRAMMING CONCEPT:
# Importing a reusable function.
#
# get_active_us_equities() retrieves the active US-equity
# universe available through Alpaca.
#
# It can support:
#
# - asset searches;
# - Data-tab ticker selection;
# - Risk asset searches;
# - API endpoints.
#
# Framework interaction:
#
# Django View / API
#     ↓
# data_management.services
#     ↓
# get_active_us_equities()
#     ↓
# Alpaca
# ============================================================

from .alpaca import (  # Relative import from the Alpaca service module.
    get_active_us_equities,  # Function: gets and caches active US equities.
)


# ============================================================
# 3. ALPACA ASSET SEARCH
# ============================================================
#
# PROGRAMMING CONCEPT:
# Function reuse.
#
# search_assets() searches the available Alpaca asset
# information instead of every view writing its own
# search algorithm.
#
# Search examples:
#
# AAPL
# Apple
# Microsoft
# MSFT
#
# Example:
#
# search_assets("Microsoft")
#
# may return:
#
# MSFT
# ============================================================

from .alpaca import (  # Import the existing asset-search function.
    search_assets,  # Function: searches assets by ticker or company name.
)


# ============================================================
# 4. ALPACA ASSET DETAILS
# ============================================================
#
# PROGRAMMING CONCEPT:
# Function abstraction.
#
# A caller supplies a symbol.
#
# Example:
#
# get_asset("AAPL")
#
# The function hides the lower-level HTTP/API implementation
# from the caller.
#
# Information can include:
#
# - symbol;
# - company name;
# - exchange;
# - tradable status;
# - shortable status;
# - marginable status;
# - fractional-share support.
# ============================================================

from .alpaca import (  # Import asset-detail functionality from alpaca.py.
    get_asset,  # Function: gets metadata for one Alpaca asset.
)


# ============================================================
# 5. SINGLE STOCK SNAPSHOT
# ============================================================
#
# PROGRAMMING CONCEPT:
# Reusable service function.
#
# get_stock_snapshot() provides current/recent market
# information for one ticker.
#
# Framework interaction:
#
# Symbol
#     ↓
# get_stock_snapshot()
#     ↓
# Alpaca snapshot endpoint
#     ↓
# Latest trade
# Latest quote
# Bid / Ask
# Daily bar
# Previous daily bar
#     ↓
# Normalised Python dictionary
#     ↓
# Dashboard / Data / Risk
# ============================================================

from .alpaca import (  # Import one-stock snapshot functionality.
    get_stock_snapshot,  # Function: retrieves current/recent data for one stock.
)


# ============================================================
# 6. MULTIPLE STOCK SNAPSHOTS
# ============================================================
#
# PROGRAMMING CONCEPT:
# Batch processing.
#
# Instead of making separate requests such as:
#
# SPY → request
# QQQ → request
# DIA → request
# IWM → request
#
# this function can request several stock snapshots together.
#
# This reduces unnecessary API calls.
#
# It is particularly useful for the Dashboard.
# ============================================================

from .alpaca import (  # Import the multi-stock snapshot function.
    get_stock_snapshots,  # Function: gets several stock snapshots together.
)


# ============================================================
# 7. HISTORICAL OHLCV MARKET DATA
# ============================================================
#
# PROGRAMMING CONCEPT:
# Data abstraction.
#
# OHLCV means:
#
# O = Open
# H = High
# L = Low
# C = Close
# V = Volume
#
# get_historical_bars() hides the Alpaca HTTP implementation
# and gives the rest of MarketPulse normalised market data.
#
# Framework interaction:
#
# Alpaca Historical Bars
#     ↓
# get_historical_bars()
#     ↓
# Normalised Python dictionaries
#     ↓
# Data import
#     ↓
# core.MarketData
#     ↓
# PostgreSQL
#
# The same historical data can then support:
#
# - Data charts;
# - Strategy backtesting;
# - Market Condition;
# - Risk analytics;
# - Stress testing;
# - Dashboard charts.
# ============================================================

from .alpaca import (  # Import the central historical-data service function.
    get_historical_bars,  # Function: retrieves historical OHLCV bars from Alpaca.
)


# ============================================================
# 8. US MARKET CLOCK
# ============================================================
#
# PROGRAMMING CONCEPT:
# Encapsulation.
#
# The rest of the application does not need to know the exact
# Alpaca /v2/clock endpoint.
#
# It only calls:
#
# get_market_clock()
#
# Information returned can include:
#
# - current market timestamp;
# - whether the US market is open;
# - next market open;
# - next market close.
#
# Framework interaction:
#
# Alpaca Trading API
#     ↓
# /v2/clock
#     ↓
# get_market_clock()
#     ↓
# Dashboard
#     ↓
# "Market Open" / "Market Closed"
# ============================================================

from .alpaca import (  # Import the market-clock service function.
    get_market_clock,  # Function: retrieves current US market-session information.
)


# ============================================================
# 9. DASHBOARD MARKET OVERVIEW
# ============================================================
#
# PROGRAMMING CONCEPT:
# Composition.
#
# A higher-level function can combine results from other
# functions to create a more useful application result.
#
# get_dashboard_market_overview() combines:
#
# get_stock_snapshots()
#         +
# get_market_clock()
#         ↓
# Dashboard market overview
#
# Default benchmark assets:
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
# ============================================================

from .alpaca import (  # Import the higher-level Dashboard market service.
    get_dashboard_market_overview,  # Function: builds Dashboard benchmark information.
)


# ============================================================
# 10. DASHBOARD HISTORICAL CHART
# ============================================================
#
# PROGRAMMING CONCEPT:
# Function composition and parameter passing.
#
# Example:
#
# get_chart_history(
#     "SPY",
#     "1M",
# )
#
# In this example:
#
# "SPY"
#     is a function argument representing the ticker.
#
# "1M"
#     is a function argument representing the period.
#
# Framework interaction:
#
# User selects SPY
#     ↓
# Dashboard / Data JavaScript
#     ↓
# Django API
#     ↓
# get_chart_history()
#     ↓
# get_historical_bars()
#     ↓
# Alpaca Historical Market Data API
#     ↓
# Normalised observations
#     ↓
# Chart.js
#
# Supported periods currently include:
#
# 1D
# 5D
# 1M
# 3M
# ============================================================

from .alpaca import (  # Import the chart-history helper from alpaca.py.
    get_chart_history,  # Function: prepares historical Alpaca data for charting.
)


# ============================================================
# 11. ALPACA CONNECTION TEST
# ============================================================
#
# PROGRAMMING CONCEPT:
# Diagnostic function.
#
# test_alpaca_connection() lets MarketPulse test whether the
# backend can communicate successfully with Alpaca.
#
# It does not need to expose the actual API credentials.
#
# Example returned Python dictionary:
#
# {
#     "success": True,
#     "provider": "Alpaca",
#     "feed": "IEX",
#     "market_open": False,
#     "message": "MarketPulse connected successfully to Alpaca."
# }
#
# Possible uses:
#
# - deployment diagnostics;
# - administration;
# - configuration testing;
# - provider-health information.
# ============================================================

from .alpaca import (  # Import the safe Alpaca diagnostic function.
    test_alpaca_connection,  # Function: checks whether the Alpaca service is working.
)


# ============================================================
# 12. PUBLIC SERVICE INTERFACE
# ============================================================
#
# PROGRAMMING CONCEPT:
# Python list.
#
# __all__ is assigned a list:
#
#     [...]
#
# A list is an ordered Python collection.
#
#
# PROGRAMMING CONCEPT:
# Strings.
#
# Each item such as:
#
#     "get_asset"
#
# is a Python string containing the public name.
#
#
# PROGRAMMING CONCEPT:
# Package interface.
#
# __all__ documents which names are intentionally considered
# part of this package's public API.
#
# It is especially relevant to:
#
#     from data_management.services import *
#
# It also makes the intended service interface clear to another
# developer reading the project.
#
#
# IMPORTANT:
#
# Functions beginning with "_" inside alpaca.py are internal
# implementation helpers and are deliberately not listed here.
#
# Examples include implementation concepts such as:
#
# _alpaca_get()
# _normalise_bar()
# _normalise_snapshot()
#
# Those implementation details remain inside alpaca.py.
# ============================================================

__all__ = [  # Assignment: store the public service names in a Python list.

    # --------------------------------------------------------
    # EXCEPTION
    # --------------------------------------------------------

    "AlpacaServiceError",  # String: public custom Alpaca exception.

    # --------------------------------------------------------
    # ASSET DISCOVERY
    # --------------------------------------------------------

    "get_active_us_equities",  # String: public active-equity function name.
    "search_assets",  # String: public asset-search function name.
    "get_asset",  # String: public single-asset function name.

    # --------------------------------------------------------
    # CURRENT / RECENT MARKET INFORMATION
    # --------------------------------------------------------

    "get_stock_snapshot",  # String: public one-stock snapshot function name.
    "get_stock_snapshots",  # String: public multi-stock snapshot function name.

    # --------------------------------------------------------
    # HISTORICAL MARKET DATA
    # --------------------------------------------------------

    "get_historical_bars",  # String: public historical OHLCV function name.

    # --------------------------------------------------------
    # MARKET STATUS
    # --------------------------------------------------------

    "get_market_clock",  # String: public US market-clock function name.

    # --------------------------------------------------------
    # DASHBOARD SERVICES
    # --------------------------------------------------------

    "get_dashboard_market_overview",  # String: public Dashboard overview function name.
    "get_chart_history",  # String: public historical chart-data function name.

    # --------------------------------------------------------
    # DIAGNOSTICS
    # --------------------------------------------------------

    "test_alpaca_connection",  # String: public Alpaca connection-test function name.

]  # End of the __all__ public-interface list.