"""
============================================================
MARKETPULSE - API ENDPOINTS
============================================================

FILE PURPOSE:

This file is the API controller layer for MarketPulse.

It receives HTTP requests from the frontend, communicates with
models, serializers, calculators, MATLAB and Alpaca services,
and returns structured API responses.

============================================================
FRAMEWORK MAPPING
============================================================

Browser / JavaScript / React
        ↓
Django URL Routing
        ↓
Django REST Framework
        ↓
api/views.py
        ↓
┌───────────────┬────────────────┬────────────────┬──────────────┐
│               │                │                │              │
▼               ▼                ▼                ▼              ▼
Django ORM   Serializers    Alpaca Service   Risk Logic      MATLAB
│               │                │                │              │
▼               ▼                ▼                ▼              ▼
PostgreSQL      JSON         Market Data     Calculations    Analytics
        ↓
Django REST Framework Response
        ↓
JSON
        ↓
Dashboard / JavaScript / React

============================================================
PROGRAMMING LANGUAGE CONCEPTS USED
============================================================

Modules / Imports
    Reuse Python code from other files.

Variables
    Store values while the program is running.

Constants
    Store reusable configuration values.

Functions
    Group reusable behaviour.

Parameters
    Pass information into functions.

Return Values
    Send information back from functions.

Conditionals
    if / elif / else make decisions.

Loops
    for repeats instructions.

Collections
    Lists, dictionaries and sets organise data.

Type Conversion
    int(), float(), str() and bool() change data types.

Exception Handling
    try / except prevents expected errors from crashing requests.

Decorators
    Configure functions as REST API endpoints.

Classes
    Group related state and behaviour.

Inheritance
    Reuse behaviour supplied by Django REST Framework.

Methods
    Functions defined inside classes.

Object-Oriented Programming
    Used by StrategyViewSet and BacktestViewSet.

ORM Abstraction
    Django converts Python QuerySets into database operations.

============================================================
THIS API LAYER PROVIDES ACCESS TO
============================================================

1. Application health information
2. Historical MarketPulse PostgreSQL data
3. Dashboard market overview
4. Risk calculations
5. MATLAB integration
6. Alpaca asset search
7. Alpaca asset information
8. Alpaca current market snapshots
9. Alpaca historical OHLCV chart data
10. User strategies
11. Backtest results

============================================================
DASHBOARD MARKET FLOW
============================================================

Dashboard
    ↓
MarketPulse API
    ↓

┌──────────────────────┬──────────────────────┬────────────────┐
│                      │                      │                │
▼                      ▼                      ▼                ▼
Alpaca Snapshot   Alpaca History        MarketRegime     PostgreSQL
│                      │                      │                │
▼                      ▼                      ▼                ▼
Live Benchmark    Chart / OHLCV         Market          Historical
Cards             Analysis              Condition       Fallback

============================================================
PROFESSIONAL CHART WORKSPACE FLOW
============================================================

Search / Watchlist
        ↓
Alpaca asset search
        ↓
Selected symbol
        ↓
┌──────────────────────────┬──────────────────────────┐
│                          │                          │
▼                          ▼                          ▼
Asset metadata        Current Snapshot         Historical OHLCV
                                                   ↓
                                    Candlestick / Line /
                                    Heikin-Ashi / Volume

============================================================
DASHBOARD BENCHMARKS
============================================================

SPY
    Broad US large-cap market

QQQ
    Nasdaq-100 / technology-heavy market

DIA
    Dow Jones large-cap market

IWM
    US small-cap market

============================================================
IMPORTANT SECURITY DESIGN
============================================================

The browser NEVER receives:

- ALPACA_API_KEY_ID
- ALPACA_API_SECRET_KEY

Instead:

Browser
    ↓
MarketPulse Django API
    ↓
Alpaca Service Layer
    ↓
Alpaca API

============================================================
IMPORTANT DATA-PROVENANCE DESIGN
============================================================

Current / latest market information:
    Alpaca

Interactive Dashboard chart information:
    Alpaca Historical Market Data

Professional selected-asset chart:
    Alpaca Historical Market Data

Historical analytical persistence:
    PostgreSQL MarketData

PostgreSQL may still contain observations imported from older
providers.

Therefore stored database rows are labelled:

    "Stored MarketPulse data"

rather than automatically claiming that every persisted row
originated from Alpaca.

============================================================
"""

# ============================================================
# 1. DJANGO IMPORTS
# Programming concept: modules and imports
# ============================================================

from django.conf import settings  # Imports Django project settings so this file can read configuration values.
from django.db.models import Avg  # Imports Django's Avg database aggregation function.
from django.utils import timezone  # Imports Django timezone utilities for timezone-aware dates and times.

# ============================================================
# 2. DJANGO REST FRAMEWORK IMPORTS
# Programming concept: framework modules and names
# ============================================================

from rest_framework import (  # Imports selected names from the Django REST Framework package.
    status,  # Provides readable HTTP status constants such as HTTP_400_BAD_REQUEST.
    viewsets,  # Provides reusable class-based REST API viewsets.
)
from rest_framework.decorators import (  # Imports decorators used to configure function-based API views.
    api_view,  # Converts a normal Python function into a DRF API view.
    authentication_classes,  # Allows an API view to override authentication behaviour.
    permission_classes,  # Allows an API view to define its access permissions.
)
from rest_framework.permissions import (  # Imports REST API permission classes.
    AllowAny,  # Allows authenticated and unauthenticated users.
    IsAuthenticated,  # Allows only authenticated users.
)
from rest_framework.response import Response  # Creates REST Framework HTTP responses from Python data.

# ============================================================
# 3. CORE MARKETPULSE IMPORTS
# Programming concept: importing classes and functions
# ============================================================

from core.models import (  # Imports Django model classes from the core application.
    Alert,  # Represents stored MarketPulse alerts.
    Backtest,  # Represents stored backtest results.
    MarketData,  # Represents stored historical market observations.
    Strategy,  # Represents user trading strategies.
)
from core.matlab_bridge import (  # Imports MarketPulse MATLAB integration code.
    run_matlab_operation,  # Runs a supported operation through the MATLAB bridge.
)
from core.exceptions import (  # Imports a custom MarketPulse exception class.
    MatlabUnavailable,  # Represents a failure to access the MATLAB service.
)

# ============================================================
# 4. INTERNAL ANALYTICS IMPORTS
# Programming concept: modular program design
# ============================================================

# analysis_tools is an internal analytical layer.
# Detailed market-condition analysis belongs under the Data
# workflow while the Dashboard displays the latest result.

from analysis_tools.models import (  # Imports models from the analytics application.
    MarketRegime,  # Represents a calculated historical market-condition result.
)

# ============================================================
# 5. RISK MANAGEMENT IMPORTS
# Programming concept: reusable functions
# ============================================================

from risk_management.calculators import (  # Imports reusable risk-calculation functions.
    calculate_position_size,  # Calculates how large a trading position should be.
    calculate_stop_loss,  # Calculates the stop-loss price.
)

# ============================================================
# 6. API SERIALIZERS
# Programming concept: object conversion / abstraction
# ============================================================

from .serializers import (  # Relative import means serializers.py belongs to this same api package.
    BacktestSerializer,  # Converts Backtest model objects into API-friendly data.
    MarketDataSerializer,  # Converts MarketData model objects into API-friendly data.
    StrategySerializer,  # Converts Strategy model objects into API-friendly data.
)

# ============================================================
# 7. ALPACA SERVICE IMPORTS
# Programming concept: separation of concerns
# ============================================================

# All direct communication with Alpaca remains inside the
# dedicated data-management service layer.
# This API layer never constructs Alpaca credentials itself.

from data_management.services.alpaca import (  # Imports functions from the dedicated Alpaca service module.
    AlpacaServiceError,  # Custom exception raised when an Alpaca request fails.
    get_asset,  # Retrieves metadata about one Alpaca asset.
    get_chart_history,  # Retrieves historical OHLCV bars.
    get_market_clock,  # Retrieves current US market clock information.
    get_stock_snapshot,  # Retrieves the latest snapshot for one stock.
    search_assets,  # Searches Alpaca's supported asset universe.
)

# ============================================================
# 8. DASHBOARD CONFIGURATION
# Programming concepts: constants and dictionaries
# ============================================================

DASHBOARD_BENCHMARKS = {  # Dictionary maps each benchmark symbol to a readable description.
    "SPY": "S&P 500 ETF",  # Dictionary key SPY stores its benchmark label.
    "QQQ": "Nasdaq-100 ETF",  # Dictionary key QQQ stores its benchmark label.
    "DIA": "Dow Jones ETF",  # Dictionary key DIA stores its benchmark label.
    "IWM": "Russell 2000 ETF",  # Dictionary key IWM stores its benchmark label.
}

DASHBOARD_MAX_CHART_ROWS = 250  # Constant limits the maximum number of chart observations.
DASHBOARD_DEFAULT_CHART_ROWS = 60  # Constant stores the normal chart observation count.
DASHBOARD_REFRESH_SECONDS = 60  # Constant tells the frontend how often automatic refresh should occur.

# ============================================================
# 8.1 SUPPORTED INTERACTIVE CHART PERIODS
# Programming concept: set collection
# ============================================================

# These periods currently correspond to periods implemented by:
#
#     data_management.services.alpaca.get_chart_history()
#
# We can later extend this to:
#
#     6M
#     YTD
#     1Y
#     5Y
#     ALL
#
# when the Alpaca service period configuration is expanded.

SUPPORTED_CHART_PERIODS = {  # A set stores unique allowed chart-period strings.
    "1D",  # One-day period.
    "5D",  # Five-day period.
    "1M",  # One-month period.
    "3M",  # Three-month period.
}

# ============================================================
# 9. GENERAL DASHBOARD HELPERS
# Programming concept: helper functions
# ============================================================

# ============================================================
# 9.1 SAFE FLOAT CONVERSION
# Programming concepts:
# - function
# - parameter
# - conditional
# - type conversion
# - exception handling
# - return value
# ============================================================

def _safe_float(value):  # Defines a private helper function receiving one parameter.
    """Convert numeric values into JSON-friendly floats. Missing or invalid values return None."""  # Function documentation.
    if value is None:  # Conditional checks whether there is no usable value.
        return None  # Stops the function and returns Python's null-like value.
    try:  # Begins protected code that may raise an expected error.
        return float(value)  # Converts the supplied value to a floating-point number.
    except (TypeError, ValueError):  # Catches invalid type or invalid numeric conversion errors.
        return None  # Returns None instead of allowing the request to crash.

# ============================================================
# 9.2 CALCULATE PRICE CHANGE
# Programming concepts:
# - function parameters
# - arithmetic
# - assignment
# - Boolean logic
# - tuple return
# ============================================================

def _calculate_price_change(latest_price, previous_close):  # Defines a function with two input parameters.
    """
    Calculate absolute and percentage price movement.

    Example:

        latest_price:
            105

        previous_close:
            100

        result:
            5
            5%
    """
    latest_price = _safe_float(latest_price)  # Converts latest_price safely to a float.
    previous_close = _safe_float(previous_close)  # Converts previous_close safely to a float.
    if (  # Begins a multi-condition decision.
        latest_price is None  # Tests whether the latest price is missing.
        or previous_close is None  # OR tests whether the previous closing price is missing.
        or previous_close == 0  # OR protects against division by zero.
    ):
        return (None, None)  # Returns two unavailable results as a tuple.
    change = latest_price - previous_close  # Arithmetic subtraction calculates the absolute price movement.
    change_percentage = change / previous_close * 100  # Arithmetic calculates percentage movement.
    return (change, change_percentage)  # Returns two related values in a tuple.

# ============================================================
# 9.3 NORMALISE ONE ALPACA SNAPSHOT
# Programming concepts:
# - dictionaries
# - dictionary methods
# - conditions
# - local variables
# - return object
# ============================================================

def _normalise_dashboard_snapshot(symbol, label, snapshot):  # Function accepts a symbol, label and snapshot dictionary.
    """Convert one normalised Alpaca snapshot into a compact Dashboard-friendly JSON object."""  # Explains the function.
    snapshot = snapshot or {}  # Uses an empty dictionary when snapshot is missing.
    daily_bar = snapshot.get("daily_bar") or {}  # Safely retrieves nested daily-bar data.
    latest_price = _safe_float(snapshot.get("latest_price"))  # Reads and safely converts the latest price.
    previous_close = _safe_float(snapshot.get("previous_close"))  # Reads and safely converts the previous close.
    daily_change = _safe_float(snapshot.get("daily_change"))  # Reads and safely converts the daily change.
    daily_change_pct = _safe_float(snapshot.get("daily_change_pct"))  # Reads and safely converts percentage change.

    # --------------------------------------------------------
    # FALLBACK CHANGE CALCULATION
    # Programming concept: fallback conditional logic
    # --------------------------------------------------------

    if daily_change is None or daily_change_pct is None:  # Checks whether Alpaca omitted either change value.
        (calculated_change, calculated_change_pct) = _calculate_price_change(  # Tuple unpacking receives two calculated values.
            latest_price,  # Sends the latest price into the helper.
            previous_close,  # Sends the previous close into the helper.
        )
        if daily_change is None:  # Checks whether absolute daily change was unavailable.
            daily_change = calculated_change  # Uses the calculated fallback value.
        if daily_change_pct is None:  # Checks whether percentage change was unavailable.
            daily_change_pct = calculated_change_pct  # Uses the calculated fallback percentage.

    return {  # Returns one dictionary that DRF can later serialise as JSON.
        "symbol": symbol,  # Stores the market ticker.
        "label": label,  # Stores the readable benchmark description.
        "available": latest_price is not None,  # Boolean reports whether useful current-price data exists.
        "latest_price": latest_price,  # Stores the latest market price.
        "previous_close": previous_close,  # Stores the previous closing price.
        "change": daily_change,  # Stores the absolute daily movement.
        "change_pct": daily_change_pct,  # Stores the percentage daily movement.
        "bid": _safe_float(snapshot.get("bid_price")),  # Stores the latest bid price.
        "ask": _safe_float(snapshot.get("ask_price")),  # Stores the latest ask price.
        "spread": _safe_float(snapshot.get("spread")),  # Stores the bid/ask spread.
        "day_open": _safe_float(daily_bar.get("open")),  # Stores today's opening price.
        "day_high": _safe_float(daily_bar.get("high")),  # Stores today's highest price.
        "day_low": _safe_float(daily_bar.get("low")),  # Stores today's lowest price.
        "day_close": _safe_float(daily_bar.get("close")),  # Stores today's latest/closing bar price.
        "day_volume": daily_bar.get("volume"),  # Stores today's traded volume.
        "latest_trade_timestamp": snapshot.get("latest_trade_timestamp"),  # Stores when the latest trade occurred.
    }

# ============================================================
# 9.4 EMPTY BENCHMARK SNAPSHOT
# Programming concept: safe fallback object
# ============================================================

def _empty_dashboard_snapshot(symbol, label):  # Defines a helper for failed benchmark requests.
    """Return a safe placeholder when one benchmark request fails."""  # Explains its fallback purpose.
    return {  # Returns the same dictionary structure as a successful snapshot.
        "symbol": symbol,  # Preserves the requested symbol.
        "label": label,  # Preserves the benchmark label.
        "available": False,  # Boolean tells the frontend that live data is unavailable.
        "latest_price": None,  # No latest price is available.
        "previous_close": None,  # No previous close is available.
        "change": None,  # No absolute movement is available.
        "change_pct": None,  # No percentage movement is available.
        "bid": None,  # No bid price is available.
        "ask": None,  # No ask price is available.
        "spread": None,  # No spread is available.
        "day_open": None,  # No opening price is available.
        "day_high": None,  # No daily high is available.
        "day_low": None,  # No daily low is available.
        "day_close": None,  # No daily close is available.
        "day_volume": None,  # No volume is available.
        "latest_trade_timestamp": None,  # No trade timestamp is available.
    }

# ============================================================
# 9.5 GET STORED POSTGRESQL CHART DATA
# Programming concepts:
# - Django ORM
# - method chaining
# - slicing
# - lists
# - serialization
# ============================================================

def _get_dashboard_chart_data(symbol, limit):  # Defines a helper requiring a symbol and maximum row count.
    """
    Retrieve historical observations stored in PostgreSQL.

    This is now primarily the Dashboard fallback source.

    Alpaca Historical Market Data is preferred for the live
    interactive chart.
    """
    rows = list(  # Converts the lazy Django QuerySet into a real Python list.
        MarketData.objects  # Starts a database query using the MarketData model manager.
        .filter(symbol=symbol)  # SQL-like WHERE condition selects one symbol.
        .order_by("-date")[:limit]  # Sorts newest first and limits the number of records.
    )
    rows.reverse()  # Reverses the list because charts need oldest-to-newest observations.
    return MarketDataSerializer(rows, many=True).data  # Serializes multiple model objects into primitive API data.

# ============================================================
# 9.5A GET ALPACA DASHBOARD CHART HISTORY
# Programming concepts:
# - default parameters
# - validation
# - string methods
# - list slicing
# - loops
# - dictionaries
# ============================================================

def _get_alpaca_dashboard_history(  # Defines the Alpaca history helper.
    symbol,  # Required market symbol parameter.
    period="1M",  # Default argument requests one month.
    limit=DASHBOARD_DEFAULT_CHART_ROWS,  # Default argument uses the configured row count.
):
    """
    Retrieve historical bars directly from Alpaca.

    Framework mapping:

    Dashboard
        ↓
    /api/dashboard/market-overview/
        ↓
    _get_alpaca_dashboard_history()
        ↓
    get_chart_history()
        ↓
    Alpaca Historical Market Data
        ↓
    OHLCV
        ↓
    Chart frontend

    The returned object intentionally contains:

        points

    using Alpaca-style readable fields:

        open
        high
        low
        close
        volume

    and:

        rows

    using MarketData-compatible fields:

        open_price
        high_price
        low_price
        close_price
        volume

    This gives MarketPulse compatibility during the transition
    from older Chart.js/database-driven code to the new
    professional chart workspace.
    """

    # --------------------------------------------------------
    # NORMALISE SYMBOL
    # Programming concepts: default value and string processing
    # --------------------------------------------------------

    symbol = symbol or "SPY"  # Uses SPY when the supplied symbol is empty or false-like.
    symbol = str(symbol).strip().upper()  # Converts to string, removes whitespace and normalises to uppercase.

    # --------------------------------------------------------
    # NORMALISE PERIOD
    # --------------------------------------------------------

    period = period or "1M"  # Uses one month when no usable period was supplied.
    period = str(period).strip().upper()  # Converts the period into a clean uppercase string.
    if period not in SUPPORTED_CHART_PERIODS:  # Membership test validates against the allowed set.
        period = "1M"  # Invalid values safely fall back to one month.

    # --------------------------------------------------------
    # NORMALISE LIMIT
    # Programming concepts: conversion and exception handling
    # --------------------------------------------------------

    try:  # Starts validation that could raise a conversion error.
        limit = int(limit)  # Converts the supplied limit into an integer.
    except (TypeError, ValueError):  # Handles unusable limit values.
        limit = DASHBOARD_DEFAULT_CHART_ROWS  # Restores the configured default value.
    limit = min(  # min() guarantees the result never exceeds the maximum.
        max(limit, 1),  # max() guarantees at least one record is requested.
        DASHBOARD_MAX_CHART_ROWS,  # Provides the maximum permitted row count.
    )

    # --------------------------------------------------------
    # REQUEST ALPACA HISTORY
    # Programming concept: service-layer function call
    # --------------------------------------------------------

    alpaca_history = get_chart_history(  # Calls the Alpaca service rather than connecting directly from the view.
        symbol=symbol,  # Keyword argument supplies the selected ticker.
        period=period,  # Keyword argument supplies the validated period.
    )
    raw_points = alpaca_history.get("points") or []  # Retrieves returned points or uses an empty list.
    points = raw_points[-limit:]  # Negative list slicing keeps only the newest requested observations.

    # --------------------------------------------------------
    # BUILD DATABASE-COMPATIBLE ROWS
    # Programming concepts: list, loop and dictionary
    # --------------------------------------------------------

    rows = []  # Creates an empty list that will receive converted chart rows.
    for point in points:  # Loop visits every historical Alpaca chart point.
        rows.append(  # Adds one converted dictionary to the list.
            {
                "date": point.get("date"),  # Copies the date field.
                "open_price": point.get("open"),  # Renames open to the MarketData-compatible name.
                "high_price": point.get("high"),  # Renames high to the MarketData-compatible name.
                "low_price": point.get("low"),  # Renames low to the MarketData-compatible name.
                "close_price": point.get("close"),  # Renames close to the MarketData-compatible name.
                "volume": point.get("volume"),  # Copies trading volume.
            }
        )

    has_data = bool(points)  # Converts the list into True when at least one point exists.
    message = None  # Initially there is no warning message.
    if not has_data:  # Runs only when Alpaca returned no historical observations.
        message = f"No Alpaca historical bars were returned for {symbol}."  # f-string inserts the selected symbol.

    return {  # Returns all historical-chart information in one dictionary.
        "symbol": symbol,  # Returns the normalised symbol.
        "period": alpaca_history.get("period", period),  # Uses the provider period or the requested fallback.
        "timeframe": alpaca_history.get("timeframe"),  # Returns the Alpaca timeframe.
        "provider": alpaca_history.get("provider", "Alpaca"),  # Returns provider name with Alpaca fallback.
        "feed": alpaca_history.get(  # Returns the market-data feed name.
            "feed",  # Looks for feed in the service response.
            getattr(settings, "ALPACA_DATA_FEED", "iex"),  # Falls back safely to Django settings or IEX.
        ),
        "has_data": has_data,  # Reports whether chart observations exist.
        "count": len(points),  # len() counts returned observations.
        "message": message,  # Returns the optional no-data message.
        "points": points,  # Returns Alpaca-style points.
        "rows": rows,  # Returns database-compatible rows.
        "first_bar_date": points[0].get("date") if points else None,  # Conditional expression safely gets first date.
        "last_bar_date": points[-1].get("date") if points else None,  # Conditional expression safely gets last date.
    }

# ============================================================
# 9.6 FIND BENCHMARKS WITH STORED HISTORY
# Programming concepts:
# - QuerySet
# - set
# - list comprehension
# ============================================================

def _get_dashboard_chart_symbols():  # Defines a helper with no required arguments.
    """
    Return benchmark symbols with stored MarketData rows.

    This describes PostgreSQL availability only.

    Alpaca historical data may be available even when the
    symbol has not been imported into PostgreSQL.
    """
    stored_symbols = set(  # set() removes duplicate values.
        MarketData.objects  # Begins a MarketData database query.
        .filter(symbol__in=list(DASHBOARD_BENCHMARKS.keys()))  # Selects only configured benchmark symbols.
        .values_list("symbol", flat=True)  # Requests only symbol values rather than full model objects.
        .distinct()  # Asks the database for unique symbols.
    )
    return [  # Returns a new list.
        symbol  # Each matching symbol becomes one list element.
        for symbol in DASHBOARD_BENCHMARKS  # Comprehension loops over configured benchmarks.
        if symbol in stored_symbols  # Keeps only benchmarks that exist in PostgreSQL.
    ]

# ============================================================
# 9.7 GET LATEST MARKET CONDITION
# Programming concepts:
# - ORM query
# - exception handling
# - dictionary
# ============================================================

def _get_latest_market_condition(symbol):  # Defines a helper requiring one market symbol.
    """Retrieve the newest stored MarketRegime result."""  # Describes the helper.
    regime = (  # Stores the database result.
        MarketRegime.objects  # Begins a MarketRegime ORM query.
        .filter(symbol=symbol)  # Filters rows for the selected symbol.
        .order_by("-date", "-created_at")  # Sorts newest analytical result first.
        .first()  # Returns only the first model object or None.
    )
    if regime is None:  # Checks whether no regime record was found.
        return None  # Stops here when no condition exists.
    try:  # Attempts to use Django's generated display helper.
        display_name = regime.get_regime_display()  # Converts a model choice value into its readable label.
    except AttributeError:  # Handles models without the generated display method.
        display_name = regime.regime  # Falls back to the raw stored value.
    return {  # Returns API-friendly condition information.
        "symbol": regime.symbol,  # Returns model attribute symbol.
        "date": regime.date,  # Returns model attribute date.
        "regime": regime.regime,  # Returns raw market-regime code.
        "display": display_name,  # Returns readable regime name.
        "confidence": _safe_float(regime.confidence),  # Converts confidence safely to JSON-friendly float.
        "volatility": _safe_float(regime.volatility),  # Converts volatility safely.
        "trend_strength": _safe_float(regime.trend_strength),  # Converts trend strength safely.
    }

# ============================================================
# 9.8 GET DATABASE DATA HEALTH
# Programming concepts:
# - aggregation
# - counting
# - dates
# - arithmetic
# ============================================================

def _get_dashboard_data_health():  # Defines a helper summarising persisted market-data health.
    """Summarise the PostgreSQL MarketData persistence layer."""  # Explains the helper.
    total_rows = MarketData.objects.count()  # ORM count() efficiently counts all MarketData rows.
    symbol_count = (  # Stores the number of distinct symbols.
        MarketData.objects  # Begins another database query.
        .values("symbol")  # Selects symbol values.
        .distinct()  # Removes duplicate symbols.
        .count()  # Counts the resulting unique symbols.
    )
    latest_date = (  # Stores the newest MarketData date.
        MarketData.objects  # Begins an ORM query.
        .order_by("-date")  # Sorts newest first.
        .values_list("date", flat=True)  # Returns just the date column.
        .first()  # Returns the first date or None.
    )
    earliest_date = (  # Stores the oldest MarketData date.
        MarketData.objects  # Begins another ORM query.
        .order_by("date")  # Sorts oldest first.
        .values_list("date", flat=True)  # Requests only dates.
        .first()  # Returns the first date or None.
    )
    symbols = list(  # Converts the QuerySet result into a Python list.
        MarketData.objects  # Begins another database query.
        .order_by("symbol")  # Sorts alphabetically by symbol.
        .values_list("symbol", flat=True)  # Requests only symbol strings.
        .distinct()[:20]  # Keeps at most twenty unique symbols.
    )
    days_since_latest_data = None  # Starts with no age value.
    if latest_date is not None:  # Runs date arithmetic only when stored data exists.
        days_since_latest_data = (timezone.localdate() - latest_date).days  # Subtracts dates and extracts day count.
    return {  # Returns the persistence-health summary.
        "database": "PostgreSQL",  # Identifies the database technology.
        "historical_storage": "MarketPulse MarketData",  # Identifies the application's persistence model.
        "total_market_rows": total_rows,  # Returns the number of observations.
        "stored_symbols": symbol_count,  # Returns the unique symbol count.
        "symbols": symbols,  # Returns up to twenty stored symbols.
        "earliest_stored_date": earliest_date,  # Returns the oldest observation date.
        "latest_stored_date": latest_date,  # Returns the newest observation date.
        "days_since_latest_data": days_since_latest_data,  # Reports database freshness.
        "historical_provider": "Stored MarketPulse data",  # Avoids incorrectly attributing old rows to one provider.
    }

# ============================================================
# 9.9 SERIALISE ONE ALERT
# Programming concepts:
# - objects
# - getattr()
# - fallback expressions
# - type conversion
# ============================================================

def _serialise_dashboard_alert(alert):  # Defines a helper that receives one Alert model object.
    """Convert one persistent Alert model instance into JSON."""  # Explains its purpose.
    title = (  # Builds the safest available alert title.
        getattr(alert, "title", None)  # getattr() safely checks whether the object has a title attribute.
        or getattr(alert, "alert_type", None)  # Uses alert_type when title is absent.
        or "MarketPulse Alert"  # Uses a final default title.
    )
    message = (  # Builds the safest available alert message.
        getattr(alert, "message", None)  # First tries message.
        or getattr(alert, "description", None)  # Then tries description.
        or str(alert)  # Finally converts the object itself to a string.
    )
    severity = getattr(alert, "severity", None) or "warning"  # Reads severity or defaults to warning.
    destination = (  # Looks for several possible navigation fields.
        getattr(alert, "action_url", None)  # First tries action_url.
        or getattr(alert, "destination", None)  # Then destination.
        or getattr(alert, "url", None)  # Finally url.
    )
    return {  # Returns a clean dictionary for the API.
        "id": alert.pk,  # pk is Django's primary-key attribute.
        "title": str(title),  # Ensures the title is a string.
        "message": str(message),  # Ensures the message is a string.
        "severity": str(severity),  # Ensures severity is a string.
        "alert_type": getattr(alert, "alert_type", None),  # Safely reads alert_type.
        "is_active": bool(getattr(alert, "is_active", True)),  # Converts active state to a Boolean.
        "is_read": bool(getattr(alert, "is_read", False)),  # Converts read state to a Boolean.
        "destination": destination,  # Returns the discovered navigation destination.
        "created_at": getattr(alert, "created_at", None),  # Safely returns creation timestamp.
    }

# ============================================================
# 9.10 GET ACTIVE USER ALERTS
# Programming concepts:
# - default arguments
# - ORM filtering
# - list comprehension
# ============================================================

def _get_dashboard_alerts(user, limit=5):  # Function receives user and optional maximum result count.
    """
    Return active persistent Alert records.

    Alert:
        persisted event/notification

    Notice:
        generated current-state explanation
    """
    alerts = (  # Stores a lazy database QuerySet.
        Alert.objects  # Uses the Alert model manager.
        .filter(user=user, is_active=True)  # Restricts alerts to this user and active records.
        .order_by("-created_at")[:limit]  # Sorts newest first and applies the requested maximum.
    )
    return [  # Returns a Python list.
        _serialise_dashboard_alert(alert)  # Converts each model object into API-friendly data.
        for alert in alerts  # Loops through the QuerySet.
    ]

# ============================================================
# 9.11 GET USER DASHBOARD SUMMARY
# Programming concepts:
# - ORM
# - aggregation
# - relationships
# - arithmetic
# ============================================================

def _get_dashboard_user_summary(user):  # Defines a helper for one authenticated user.
    """Build user-specific Dashboard statistics."""  # Describes the function.
    strategies = Strategy.objects.filter(user=user)  # Retrieves strategies belonging to this user.
    backtests = Backtest.objects.filter(strategy__user=user)  # Follows the Strategy relationship to retrieve the user's backtests.
    average_win_rate = (  # Stores an aggregate win-rate value.
        backtests  # Starts from the filtered QuerySet.
        .aggregate(value=Avg("win_rate"))  # Asks the database to calculate the average.
        .get("value")  # Retrieves the aggregate dictionary value.
        or 0  # Uses zero when no backtests exist.
    )
    active_alert_count = (  # Stores the number of active alerts.
        Alert.objects  # Begins an Alert query.
        .filter(user=user, is_active=True)  # Restricts records to active alerts for this user.
        .count()  # Counts them efficiently in the database.
    )
    return {  # Returns the Dashboard statistics dictionary.
        "active_strategies": strategies.filter(is_active=True).count(),  # Counts only active strategies.
        "total_strategies": strategies.count(),  # Counts all strategies for this user.
        "completed_backtests": backtests.count(),  # Counts backtest records.
        "average_win_rate_pct": float(average_win_rate) * 100,  # Converts the stored fraction into a percentage.
        "historical_observations": MarketData.objects.count(),  # Counts all historical market observations.
        "active_alerts": active_alert_count,  # Returns active-alert count.
    }

# ============================================================
# 9.12 GET RECENT BACKTESTS
# Programming concepts:
# - ORM relationships
# - optimisation
# - serialization
# ============================================================

def _get_recent_backtests(user, limit=5):  # Defines a helper with a default result limit.
    """Return recent user backtests."""  # Explains the function.
    backtests = (  # Builds the QuerySet.
        Backtest.objects  # Begins a Backtest database query.
        .filter(strategy__user=user)  # Retrieves backtests whose related strategy belongs to the user.
        .select_related("strategy")  # Performs an SQL join to avoid additional strategy queries.
        .order_by("-created_at")[:limit]  # Sorts newest first and limits results.
    )
    return BacktestSerializer(backtests, many=True).data  # Serializes several Backtest model objects.

# ============================================================
# 9.13 BUILD BENCHMARK MARKET SUMMARY
# Programming concepts:
# - counters
# - loops
# - continue
# - comparisons
# - arithmetic
# - branching
# ============================================================

def _build_benchmark_market_summary(benchmark_results):  # Function receives a collection of benchmark dictionaries.
    """
    Describe current direction across Dashboard benchmarks.

    This is descriptive market context, not a forecast or
    investment recommendation.
    """
    available = 0  # Counter for usable benchmarks.
    advancing = 0  # Counter for positive benchmarks.
    declining = 0  # Counter for negative benchmarks.
    unchanged = 0  # Counter for benchmarks with zero movement.
    percentage_changes = []  # List will store valid percentage changes.

    for benchmark in benchmark_results:  # Loop examines each benchmark dictionary.
        if not benchmark.get("available"):  # Checks whether current market information exists.
            continue  # Skips the rest of this loop iteration.
        change_pct = _safe_float(benchmark.get("change_pct"))  # Safely converts percentage movement.
        if change_pct is None:  # Checks whether no usable percentage was available.
            continue  # Skips this benchmark.
        available += 1  # Augmented assignment increases the counter by one.
        percentage_changes.append(change_pct)  # Adds this percentage to the collection.
        if change_pct > 0:  # Tests for a positive movement.
            advancing += 1  # Increases advancing count.
        elif change_pct < 0:  # Tests for a negative movement.
            declining += 1  # Increases declining count.
        else:  # Runs when the percentage is exactly zero.
            unchanged += 1  # Increases unchanged count.

    average_change_pct = None  # Starts with no calculated average.
    if percentage_changes:  # An inhabited list evaluates as True.
        average_change_pct = sum(percentage_changes) / len(percentage_changes)  # Calculates the arithmetic mean.

    if available == 0:  # First branch handles no available benchmark information.
        direction = "unavailable"  # Stores a machine-readable direction.
        message = "Current benchmark market data is unavailable."  # Stores a human-readable explanation.
    elif advancing > declining:  # Second branch handles predominantly positive benchmarks.
        direction = "mostly_positive"  # Stores positive market direction.
        message = f"{advancing} of {available} available benchmark ETFs are above their previous close."  # f-string inserts counters.
    elif declining > advancing:  # Third branch handles predominantly negative benchmarks.
        direction = "mostly_negative"  # Stores negative market direction.
        message = f"{declining} of {available} available benchmark ETFs are below their previous close."  # Builds explanation.
    else:  # Final branch handles tied/mixed market movement.
        direction = "mixed"  # Stores mixed direction.
        message = "The displayed benchmark ETFs currently show mixed market direction."  # Human-readable explanation.

    return {  # Returns all summary values.
        "available_benchmarks": available,  # Returns number of usable benchmarks.
        "advancing": advancing,  # Returns number moving upward.
        "declining": declining,  # Returns number moving downward.
        "unchanged": unchanged,  # Returns number unchanged.
        "average_change_pct": average_change_pct,  # Returns average benchmark movement.
        "direction": direction,  # Returns machine-readable direction.
        "message": message,  # Returns human-readable market summary.
    }

# ============================================================
# 9.14 BUILD DASHBOARD NOTICES
# Programming concepts:
# - list construction
# - conditions
# - dictionary literals
# - nested data access
# ============================================================

def _build_dashboard_notices(  # Defines a helper taking several Dashboard state values.
    user_summary,  # User-specific strategy/backtest statistics.
    data_health,  # PostgreSQL historical-data health information.
    chart_rows,  # Historical observations currently available for the chart.
    selected_symbol,  # Currently selected benchmark.
    provider_status,  # Overall Alpaca provider status.
):
    """
    Generate useful Dashboard notices.

    These are separate from persistent Alert records.
    """
    notices = []  # Creates the output collection.

    # --------------------------------------------------------
    # NO ACTIVE STRATEGIES
    # --------------------------------------------------------

    if user_summary["active_strategies"] == 0:  # Checks whether the user currently has no active strategy.
        notices.append(  # Adds an informational notice.
            {
                "level": "info",  # Sets Bootstrap-like notice severity.
                "code": "NO_ACTIVE_STRATEGIES",  # Provides a stable machine-readable notice code.
                "title": "No active strategies",  # Provides a user-facing heading.
                "message": "Create or activate a strategy to begin backtesting and strategy validation.",  # Explains the next action.
                "destination": "/strategy/",  # Provides a navigation target.
            }
        )

    # --------------------------------------------------------
    # NO BACKTESTS
    # --------------------------------------------------------

    if user_summary["completed_backtests"] == 0:  # Checks whether the user has no Backtest records.
        notices.append(  # Adds another notice dictionary.
            {
                "level": "info",  # Sets informational severity.
                "code": "NO_BACKTESTS",  # Sets stable notice identifier.
                "title": "No backtests completed",  # User-facing title.
                "message": "Run a backtest to populate performance, win-rate and strategy results.",  # Explains why the notice exists.
                "destination": "/strategy/",  # Links toward strategy/backtest functionality.
            }
        )

    # --------------------------------------------------------
    # NO CHART HISTORY
    # --------------------------------------------------------

    if not chart_rows:  # Empty collections evaluate as False, so not makes this True.
        notices.append(  # Adds a missing-data warning.
            {
                "level": "warning",  # Marks the notice as a warning.
                "code": "NO_CHART_HISTORY",  # Stable warning code.
                "title": f"No {selected_symbol} historical chart data",  # f-string inserts selected ticker.
                "message": "MarketPulse could not obtain historical chart observations for this asset.",  # Explains the issue.
                "destination": "/data/import/" f"?symbol={selected_symbol}",  # Adjacent strings combine into one destination URL.
            }
        )

    # --------------------------------------------------------
    # STORED DATA MAY BE STALE
    # --------------------------------------------------------

    days_since_latest_data = data_health.get("days_since_latest_data")  # Safely retrieves database freshness.
    if days_since_latest_data is not None and days_since_latest_data > 4:  # Checks whether persisted data is older than four days.
        notices.append(  # Adds the stale-data warning.
            {
                "level": "warning",  # Warning severity.
                "code": "HISTORICAL_DATA_STALE",  # Machine-readable stale-data code.
                "title": "Stored historical data may be stale",  # Human-readable heading.
                "message": "The most recent PostgreSQL MarketData " f"observation is {days_since_latest_data} " "days old.",  # String concatenation plus f-string inserts age.
                "destination": "/data/import/",  # Links to the data workflow.
            }
        )

    # --------------------------------------------------------
    # PARTIAL ALPACA CONNECTIVITY
    # --------------------------------------------------------

    if provider_status == "partial":  # Checks whether only part of Alpaca succeeded.
        notices.append(  # Adds a partial-service notice.
            {
                "level": "warning",  # Warning severity.
                "code": "ALPACA_PARTIAL",  # Stable notice code.
                "title": "Some Alpaca information is unavailable",  # User-facing title.
                "message": "MarketPulse retrieved some Alpaca information successfully, but one or more provider components were unavailable.",  # Explains degraded operation.
                "destination": "/dashboard/",  # Links back to the Dashboard.
            }
        )

    # --------------------------------------------------------
    # ALPACA UNAVAILABLE
    # --------------------------------------------------------

    elif provider_status == "unavailable":  # Runs when no useful Alpaca information is available.
        notices.append(  # Adds a higher-severity provider warning.
            {
                "level": "danger",  # Marks the notice as serious.
                "code": "ALPACA_UNAVAILABLE",  # Stable machine-readable code.
                "title": "Current Alpaca market data is unavailable",  # User-facing problem title.
                "message": "MarketPulse could not retrieve current market information. Stored PostgreSQL data may still remain available.",  # Explains available fallback.
                "destination": "/dashboard/",  # Links to the Dashboard.
            }
        )

    # --------------------------------------------------------
    # ACTIVE ALERTS
    # --------------------------------------------------------

    if user_summary["active_alerts"] > 0:  # Checks whether one or more active alerts exist.
        notices.append(  # Adds an alert-attention notice.
            {
                "level": "warning",  # Warning severity.
                "code": "ACTIVE_ALERTS",  # Stable notice identifier.
                "title": "MarketPulse alerts require attention",  # User-facing heading.
                "message": f"{user_summary['active_alerts']} active alert(s) are stored for your account.",  # Nested dictionary access inside an f-string.
                "destination": "/dashboard/",  # Dashboard destination.
            }
        )
    return notices  # Returns the complete list of generated notices.

# ============================================================
# 10. API HEALTH CHECK
# Programming concepts:
# - decorators
# - function
# - dictionary
# - HTTP GET
# ============================================================

@api_view(["GET"])  # DRF decorator allows this function to answer GET requests.
@permission_classes([AllowAny])  # Permission decorator allows access without login.
def health(request):  # API view function receives the HTTP request object.
    """
    Example:

        GET /api/health/
    """
    return Response(  # Creates a Django REST Framework response.
        {
            "status": "ok",  # Reports that the service is running.
            "application": "MarketPulse",  # Identifies the application.
            "api": "Django REST Framework",  # Identifies the API framework.
            "timestamp": timezone.now(),  # Returns the current timezone-aware server timestamp.
        }
    )

# ============================================================
# 11. STORED HISTORICAL MARKET DATA API
# Programming concepts:
# - HTTP query parameters
# - input validation
# - ORM
# - serialization
# ============================================================

@api_view(["GET"])  # Exposes this function as a GET API endpoint.
@permission_classes([AllowAny])  # Allows public access to this endpoint.
def market_latest(request):  # Receives the DRF request object.
    """
    Return OHLCV observations stored in PostgreSQL.

    Example:

        GET /api/market/latest/?symbol=AAPL&limit=60
    """
    symbol = (  # Stores a cleaned market symbol.
        request.query_params  # Accesses URL query-string parameters.
        .get("symbol", "AAPL")  # Retrieves symbol or defaults to AAPL.
        .strip()  # Removes leading/trailing spaces.
        .upper()  # Converts ticker to uppercase.
    )
    try:  # Begins validation of the limit query parameter.
        limit = int(  # Converts the supplied value to an integer.
            request.query_params.get("limit", 60)  # Retrieves limit or defaults to sixty.
        )
        limit = min(max(limit, 1), 250)  # Clamps the result between one and 250.
    except (TypeError, ValueError):  # Handles invalid integer values.
        limit = 60  # Uses the safe default.
    rows = list(  # Evaluates the database QuerySet into a Python list.
        MarketData.objects  # Begins a MarketData ORM query.
        .filter(symbol=symbol)  # Selects observations for the requested ticker.
        .order_by("-date")[:limit]  # Retrieves newest rows first and limits count.
    )
    rows.reverse()  # Converts order to oldest-to-newest for chart use.
    return Response(  # Sends structured API data back to the frontend.
        {
            "symbol": symbol,  # Returns cleaned ticker.
            "count": len(rows),  # Counts returned observations.
            "storage": "MarketPulse PostgreSQL",  # Identifies persistence location.
            "historical_provider": "Stored MarketPulse data",  # Safely identifies data provenance.
            "rows": MarketDataSerializer(rows, many=True).data,  # Serializes database model objects into primitive values.
        }
    )

# ============================================================
# 12. DASHBOARD MARKET OVERVIEW API
# Programming concepts:
# - authenticated API endpoint
# - control flow
# - loops
# - exception handling
# - service integration
# - ORM integration
# - nested dictionaries
# ============================================================

@api_view(["GET"])  # Allows GET requests only.
@permission_classes([IsAuthenticated])  # Requires the requester to be logged in.
def dashboard_market_overview(request):  # Main Dashboard API controller function.
    """
    ============================================================
    DASHBOARD MARKET OVERVIEW
    ============================================================

    Examples:

        GET /api/dashboard/market-overview/

        GET /api/dashboard/market-overview/?symbol=SPY

        GET /api/dashboard/market-overview/?symbol=QQQ&period=1M

        GET /api/dashboard/market-overview/?symbol=DIA&limit=60

    DATA SOURCES:

    Alpaca
        Current benchmark snapshots

    Alpaca
        Historical Dashboard graph

    Alpaca Trading API
        US market clock

    PostgreSQL
        Historical fallback

    PostgreSQL
        Market Condition

    PostgreSQL
        Strategies / Backtests / Alerts

    IMPORTANT:

    Alpaca is the preferred Dashboard chart provider.

    PostgreSQL remains a fallback and persistence layer.
    ============================================================
    """

    # ========================================================
    # 12.1 SELECT DASHBOARD SYMBOL
    # Programming concept: input normalisation
    # ========================================================

    selected_symbol = (  # Stores the requested Dashboard symbol.
        request.query_params  # Accesses URL query-string parameters.
        .get("symbol", "SPY")  # Retrieves symbol or defaults to SPY.
        .strip()  # Removes unnecessary whitespace.
        .upper()  # Normalises ticker to uppercase.
    )
    if selected_symbol not in DASHBOARD_BENCHMARKS:  # Validates membership in the configured benchmark dictionary.
        selected_symbol = "SPY"  # Invalid values fall back to SPY.

    # ========================================================
    # 12.2 SELECT CHART PERIOD
    # ========================================================

    chart_period = (  # Stores requested chart period.
        request.query_params  # Accesses query-string data.
        .get("period", "1M")  # Retrieves period or defaults to one month.
        .strip()  # Removes whitespace.
        .upper()  # Normalises case.
    )
    if chart_period not in SUPPORTED_CHART_PERIODS:  # Validates the selected period.
        chart_period = "1M"  # Invalid periods use one month.

    # ========================================================
    # 12.3 VALIDATE CHART LIMIT
    # ========================================================

    try:  # Begins protected integer conversion.
        chart_limit = int(  # Converts URL text to an integer.
            request.query_params.get("limit", DASHBOARD_DEFAULT_CHART_ROWS)  # Reads query parameter with default.
        )
        chart_limit = min(  # Prevents values above maximum.
            max(chart_limit, 1),  # Prevents values below one.
            DASHBOARD_MAX_CHART_ROWS,  # Sets the hard maximum.
        )
    except (TypeError, ValueError):  # Catches invalid values.
        chart_limit = DASHBOARD_DEFAULT_CHART_ROWS  # Restores safe default.

    # ========================================================
    # 12.4 PROVIDER ERROR STORAGE
    # ========================================================

    provider_errors = []  # Empty list will collect non-fatal provider failures.

    # ========================================================
    # 12.5 GET CURRENT BENCHMARK SNAPSHOTS
    # Programming concepts: dictionary iteration and exceptions
    # ========================================================

    benchmark_results = []  # Creates the benchmark output collection.
    for (symbol, label) in DASHBOARD_BENCHMARKS.items():  # Dictionary items() supplies each key/value pair.
        try:  # Each benchmark request is independently protected.
            snapshot = get_stock_snapshot(symbol)  # Requests current snapshot from the Alpaca service layer.
            benchmark_results.append(  # Adds normalised data to the output list.
                _normalise_dashboard_snapshot(  # Calls the helper function.
                    symbol=symbol,  # Passes ticker by keyword.
                    label=label,  # Passes readable label.
                    snapshot=snapshot,  # Passes raw service response.
                )
            )
        except AlpacaServiceError as error:  # Handles a provider-specific exception.
            benchmark_results.append(  # Still adds a placeholder to preserve frontend structure.
                _empty_dashboard_snapshot(  # Calls fallback helper.
                    symbol=symbol,  # Preserves failed symbol.
                    label=label,  # Preserves readable name.
                )
            )
            provider_errors.append(  # Records error without terminating the whole Dashboard request.
                {
                    "component": "snapshot",  # Identifies the failing component.
                    "symbol": symbol,  # Identifies affected ticker.
                    "message": str(error),  # Converts exception into readable text.
                }
            )

    # ========================================================
    # 12.6 GET MARKET CLOCK
    # ========================================================

    try:  # Attempts the provider request.
        raw_market_clock = get_market_clock()  # Requests US market-clock information from Alpaca.
        market_clock = {  # Normalises clock data for the frontend.
            "available": True,  # Reports successful retrieval.
            "timestamp": raw_market_clock.get("timestamp"),  # Current provider timestamp.
            "is_open": raw_market_clock.get("is_open"),  # Boolean reports whether market is open.
            "next_open": raw_market_clock.get("next_open"),  # Next opening time.
            "next_close": raw_market_clock.get("next_close"),  # Next closing time.
            "message": None,  # No error message is needed on success.
        }
    except AlpacaServiceError as error:  # Handles provider failure.
        market_clock = {  # Creates a stable fallback structure.
            "available": False,  # Reports clock unavailable.
            "timestamp": None,  # No timestamp.
            "is_open": None,  # Open status unknown.
            "next_open": None,  # Next opening unknown.
            "next_close": None,  # Next close unknown.
            "message": str(error),  # Returns the provider error.
        }
        provider_errors.append(  # Records non-fatal failure.
            {
                "component": "market_clock",  # Identifies component.
                "symbol": None,  # Market clock does not belong to one ticker.
                "message": str(error),  # Stores readable exception text.
            }
        )

    # ========================================================
    # 12.7 GET ALPACA HISTORICAL CHART
    # ========================================================

    alpaca_history_error = None  # Starts with no historical-data error.
    try:  # Attempts preferred live historical provider.
        history = _get_alpaca_dashboard_history(  # Calls the dedicated history helper.
            symbol=selected_symbol,  # Requests currently selected benchmark.
            period=chart_period,  # Requests validated period.
            limit=chart_limit,  # Requests validated maximum rows.
        )
    except AlpacaServiceError as error:  # Handles an Alpaca historical-data failure.
        alpaca_history_error = str(error)  # Stores readable provider error.
        history = {  # Creates a complete no-data history structure.
            "symbol": selected_symbol,  # Preserves requested symbol.
            "period": chart_period,  # Preserves requested period.
            "timeframe": None,  # Provider timeframe unavailable.
            "provider": "Alpaca",  # Identifies attempted provider.
            "feed": getattr(settings, "ALPACA_DATA_FEED", "iex"),  # Reads configured feed safely.
            "has_data": False,  # Reports no Alpaca historical points.
            "count": 0,  # Zero observations returned.
            "message": alpaca_history_error,  # Returns failure explanation.
            "points": [],  # Empty chart points collection.
            "rows": [],  # Empty compatibility rows collection.
            "first_bar_date": None,  # No first date available.
            "last_bar_date": None,  # No last date available.
        }
        provider_errors.append(  # Records provider failure.
            {
                "component": "historical_bars",  # Identifies failing API area.
                "symbol": selected_symbol,  # Records affected symbol.
                "message": alpaca_history_error,  # Stores provider error.
            }
        )

    # ========================================================
    # 12.8 GET POSTGRESQL FALLBACK
    # ========================================================

    stored_chart_rows = _get_dashboard_chart_data(  # Calls database helper regardless of provider success.
        symbol=selected_symbol,  # Retrieves selected symbol.
        limit=chart_limit,  # Uses same chart observation limit.
    )

    # ========================================================
    # 12.9 SELECT CHART SOURCE
    # Programming concept: if / elif / else fallback strategy
    # ========================================================

    if history.get("has_data"):  # Preferred path uses Alpaca when historical points exist.
        chart_rows = history.get("rows", [])  # Reads database-compatible rows.
        chart_points = history.get("points", [])  # Reads preferred chart-point structure.
        chart_provider = "Alpaca"  # Records current provider.
        chart_storage = "Alpaca Market Data API"  # Records where the data came from.
        chart_fallback_used = False  # Reports that no fallback was necessary.
        chart_message = None  # No fallback warning is needed.
    elif stored_chart_rows:  # Secondary path uses PostgreSQL when Alpaca has no history.
        chart_rows = stored_chart_rows  # Uses serialized database observations.
        chart_points = []  # Starts conversion to preferred chart format.
        for row in stored_chart_rows:  # Loops through each stored observation.
            chart_points.append(  # Adds one converted chart point.
                {
                    "timestamp": None,  # Older persisted rows do not provide the new timestamp structure.
                    "date": row.get("date"),  # Reads observation date.
                    "open": _safe_float(row.get("open_price")),  # Converts stored opening value.
                    "high": _safe_float(row.get("high_price")),  # Converts stored high value.
                    "low": _safe_float(row.get("low_price")),  # Converts stored low value.
                    "close": _safe_float(row.get("close_price")),  # Converts stored close value.
                    "volume": row.get("volume"),  # Reads stored volume.
                }
            )
        chart_provider = "Stored MarketPulse data"  # Identifies fallback provider.
        chart_storage = "MarketPulse PostgreSQL"  # Identifies persistence layer.
        chart_fallback_used = True  # Reports that fallback occurred.
        chart_message = (  # Builds explanation for frontend display.
            "Alpaca historical bars were unavailable, so "
            "MarketPulse is displaying stored PostgreSQL "
            "historical data instead."
        )
        history = {  # Rebuilds history using the fallback source.
            "symbol": selected_symbol,  # Selected symbol.
            "period": chart_period,  # Selected period.
            "timeframe": None,  # Stored observations have no Alpaca timeframe.
            "provider": "Stored MarketPulse data",  # Correctly identifies fallback provenance.
            "feed": None,  # PostgreSQL fallback has no live Alpaca feed.
            "has_data": True,  # Stored chart points exist.
            "count": len(chart_points),  # Counts converted points.
            "message": chart_message,  # Returns fallback explanation.
            "points": chart_points,  # Returns preferred chart format.
            "rows": chart_rows,  # Returns compatibility rows.
            "first_bar_date": chart_points[0].get("date") if chart_points else None,  # Safe first-date expression.
            "last_bar_date": chart_points[-1].get("date") if chart_points else None,  # Safe last-date expression.
            "fallback_used": True,  # Explicitly reports fallback.
            "alpaca_error": alpaca_history_error,  # Preserves original provider failure.
        }
    else:  # Final branch handles no Alpaca history and no PostgreSQL history.
        chart_rows = []  # No compatibility rows exist.
        chart_points = []  # No chart points exist.
        chart_provider = "Unavailable"  # Reports no provider could supply history.
        chart_storage = None  # There is no active storage source.
        chart_fallback_used = False  # No fallback data actually succeeded.
        chart_message = (  # Builds the best available explanation.
            history.get("message")  # Uses existing provider message first.
            or f"No historical {selected_symbol} bars are currently available."  # Otherwise creates a generic message.
        )

    # ========================================================
    # 12.10 AVAILABLE CHART SYMBOLS
    # ========================================================

    # Alpaca can provide these benchmark charts even when no
    # corresponding MarketData row exists in PostgreSQL.

    available_chart_symbols = list(DASHBOARD_BENCHMARKS.keys())  # Converts benchmark dictionary keys into a list.
    stored_chart_symbols = _get_dashboard_chart_symbols()  # Retrieves which benchmarks also exist in PostgreSQL.

    # ========================================================
    # 12.11 DETERMINE PROVIDER STATUS
    # Programming concepts: generator expression and sum()
    # ========================================================

    available_benchmark_count = sum(  # sum() counts generated values.
        1  # Produces one for every available benchmark.
        for benchmark in benchmark_results  # Generator expression loops through results.
        if benchmark.get("available")  # Keeps only available snapshots.
    )
    if available_benchmark_count == 0 and not history.get("has_data"):  # Checks whether both snapshots and history are unavailable.
        provider_status = "unavailable"  # Reports complete provider outage for this response.
    elif (  # Checks several partial-degradation conditions.
        available_benchmark_count < len(DASHBOARD_BENCHMARKS)  # Some benchmark snapshots failed.
        or not market_clock.get("available")  # Or market clock failed.
        or chart_provider != "Alpaca"  # Or chart needed a different provider.
    ):
        provider_status = "partial"  # Reports partial connectivity.
    else:  # Runs when all provider components succeeded.
        provider_status = "connected"  # Reports full connectivity.

    # ========================================================
    # 12.12 GET MARKET CONDITION
    # ========================================================

    market_condition = _get_latest_market_condition(selected_symbol)  # Loads latest stored analytical regime.

    # ========================================================
    # 12.13 GET DATA HEALTH
    # ========================================================

    data_health = _get_dashboard_data_health()  # Calculates PostgreSQL persistence statistics.

    # ========================================================
    # 12.14 GET USER SUMMARY
    # ========================================================

    user_summary = _get_dashboard_user_summary(request.user)  # Builds summary for the authenticated requester.

    # ========================================================
    # 12.15 GET USER ALERTS
    # ========================================================

    active_alerts = _get_dashboard_alerts(  # Retrieves active persisted alerts.
        request.user,  # Supplies authenticated user object.
        limit=5,  # Limits response to five alerts.
    )

    # ========================================================
    # 12.16 GET RECENT BACKTESTS
    # ========================================================

    recent_backtests = _get_recent_backtests(  # Retrieves recent user backtest activity.
        request.user,  # Supplies authenticated user.
        limit=5,  # Limits result count.
    )

    # ========================================================
    # 12.17 BUILD MARKET SUMMARY
    # ========================================================

    market_summary = _build_benchmark_market_summary(benchmark_results)  # Calculates descriptive benchmark breadth.

    # ========================================================
    # 12.18 BUILD NOTICES
    # ========================================================

    notices = _build_dashboard_notices(  # Generates contextual Dashboard messages.
        user_summary=user_summary,  # Supplies user statistics.
        data_health=data_health,  # Supplies persistence freshness.
        chart_rows=chart_rows,  # Supplies currently available chart rows.
        selected_symbol=selected_symbol,  # Supplies selected benchmark.
        provider_status=provider_status,  # Supplies Alpaca connection condition.
    )

    # ========================================================
    # 12.19 RETURN DASHBOARD RESPONSE
    # Programming concept: nested dictionary / API data structure
    # ========================================================

    return Response(  # Sends the complete Dashboard API payload to the browser.
        {
            "application": "MarketPulse",  # Identifies the application.

            # ------------------------------------------------
            # REFRESH CONFIGURATION
            # ------------------------------------------------

            "refresh": {  # Nested dictionary stores frontend refresh behaviour.
                "automatic": True,  # Enables automatic frontend refresh.
                "interval_seconds": DASHBOARD_REFRESH_SECONDS,  # Supplies configured interval.
            },

            # ------------------------------------------------
            # PROVIDER
            # ------------------------------------------------

            "provider": {  # Nested dictionary describes current market-data provider.
                "name": "Alpaca",  # Provider name.
                "feed": getattr(settings, "ALPACA_DATA_FEED", "iex"),  # Reads selected market-data feed.
                "status": provider_status,  # Returns connected/partial/unavailable state.
                "purpose": "Current market snapshots and historical chart data",  # Explains provider role.
            },

            # ------------------------------------------------
            # MARKET CLOCK
            # ------------------------------------------------

            "market_clock": market_clock,  # Returns US market open/close information.

            # ------------------------------------------------
            # BENCHMARK CARDS
            # ------------------------------------------------

            "benchmarks": benchmark_results,  # Returns live SPY/QQQ/DIA/IWM card information.

            # ------------------------------------------------
            # MARKET BREADTH
            # ------------------------------------------------

            "market_summary": market_summary,  # Returns descriptive benchmark-direction summary.

            # ------------------------------------------------
            # PREFERRED HISTORICAL STRUCTURE
            # ------------------------------------------------

            "history": history,  # Returns preferred complete historical-chart object.

            # ------------------------------------------------
            # DASHBOARD CHART COMPATIBILITY STRUCTURE
            # ------------------------------------------------

            "chart": {  # Nested dictionary supports Dashboard chart rendering.
                "symbol": selected_symbol,  # Selected benchmark ticker.
                "label": DASHBOARD_BENCHMARKS[selected_symbol],  # Looks up readable label using dictionary indexing.
                "period": chart_period,  # Selected time period.
                "limit": chart_limit,  # Maximum observation count.
                "has_data": bool(chart_points),  # Converts point-list state into True/False.
                "count": len(chart_points),  # Returns number of points.
                "available_symbols": available_chart_symbols,  # Returns provider-supported benchmark list.
                "stored_symbols": stored_chart_symbols,  # Returns benchmarks persisted locally.
                "supported_symbols": list(DASHBOARD_BENCHMARKS.keys()),  # Returns configured symbols.
                "provider": chart_provider,  # Identifies source actually used.
                "storage": chart_storage,  # Identifies where returned chart information resides.
                "fallback_used": chart_fallback_used,  # Reports whether PostgreSQL fallback was needed.
                "message": chart_message,  # Returns optional chart explanation.
                "rows": chart_rows,  # Returns compatibility format.
                "points": chart_points,  # Returns preferred chart format.
            },

            # ------------------------------------------------
            # MARKET CONDITION
            # ------------------------------------------------

            "market_condition": market_condition,  # Returns latest stored analytical market regime.

            # ------------------------------------------------
            # USER SUMMARY
            # ------------------------------------------------

            "user_summary": user_summary,  # Returns authenticated-user strategy/backtest statistics.

            # ------------------------------------------------
            # PERSISTENT ALERT EVENTS
            # ------------------------------------------------

            "alerts": active_alerts,  # Returns persistent Alert model records.

            # ------------------------------------------------
            # GENERATED NOTICES
            # ------------------------------------------------

            "notices": notices,  # Returns dynamically generated Dashboard notices.

            # ------------------------------------------------
            # RECENT USER ACTIVITY
            # ------------------------------------------------

            "recent_backtests": recent_backtests,  # Returns latest serialized backtest results.

            # ------------------------------------------------
            # POSTGRESQL DATA HEALTH
            # ------------------------------------------------

            "data_health": data_health,  # Returns stored market-data statistics.

            # ------------------------------------------------
            # NON-FATAL PROVIDER ERRORS
            # ------------------------------------------------

            "provider_errors": provider_errors,  # Returns provider problems that did not stop the API response.

            # ------------------------------------------------
            # RESPONSE TIMESTAMP
            # ------------------------------------------------

            "updated_at": timezone.now(),  # Adds the current timezone-aware response timestamp.
        }
    )

# ============================================================
# 13. POSITION SIZE RISK API
# Programming concepts:
# - POST request
# - request body
# - dictionary indexing
# - exception handling
# - HTTP status codes
# ============================================================

@api_view(["POST"])  # Restricts this endpoint to HTTP POST requests.
@permission_classes([AllowAny])  # Allows access without an authenticated user.
@authentication_classes([])  # Overrides authentication classes with an empty list.
def risk_position_size(request):  # Defines the risk-calculation API controller.
    """
    Calculate basic position sizing and stop-loss information.

    Required JSON:

        account_balance
        risk_percentage
        stop_loss_pct
        entry_price
    """
    try:  # Protects required request-data access and numeric calculations.
        position_size = calculate_position_size(  # Calls reusable risk business logic.
            request.data["account_balance"],  # Dictionary indexing requires account_balance in POST body.
            request.data["risk_percentage"],  # Reads allowed risk percentage.
            request.data["stop_loss_pct"],  # Reads stop-loss percentage.
            request.data["entry_price"],  # Reads entry price.
        )
        stop_loss_price = calculate_stop_loss(  # Calls reusable stop-loss calculator.
            request.data["entry_price"],  # Supplies entry price.
            request.data["stop_loss_pct"],  # Supplies stop-loss percentage.
        )
        return Response(  # Returns successful calculation result.
            {
                "position_size": position_size,  # Returns calculated position size.
                "stop_loss_price": stop_loss_price,  # Returns calculated stop-loss price.
            }
        )
    except (KeyError, TypeError, ValueError) as error:  # Handles missing keys and invalid input data.
        return Response(  # Returns structured error response.
            {
                "error": str(error),  # Converts exception into readable message.
            },
            status=status.HTTP_400_BAD_REQUEST,  # Sends HTTP 400 because client input was invalid.
        )

# ============================================================
# 14. MATLAB RISK API
# Programming concepts:
# - integration
# - dictionary conversion
# - custom exception
# - HTTP 503
# ============================================================

@api_view(["POST"])  # Allows POST requests.
@permission_classes([AllowAny])  # Does not require authenticated access.
@authentication_classes([])  # Disables authentication classes for this endpoint.
def matlab_risk(request):  # Defines MATLAB risk API endpoint.
    """Run the optional MATLAB risk bridge."""  # Documents endpoint purpose.
    try:  # Attempts optional external/integration operation.
        result = run_matlab_operation(  # Calls the MATLAB bridge.
            "risk",  # Supplies operation name.
            dict(request.data),  # Converts request data into a standard Python dictionary.
        )
        return Response(result)  # Returns MATLAB result directly through DRF.
    except MatlabUnavailable as error:  # Handles custom integration failure.
        return Response(  # Returns structured failure response.
            {
                "error": str(error),  # Converts exception to message.
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,  # 503 means required service is unavailable.
        )

# ============================================================
# 15. ALPACA ASSET SEARCH
# Programming concepts:
# - protected GET endpoint
# - validation
# - service function
# - exceptions
# ============================================================

@api_view(["GET"])  # Creates a GET endpoint.
@permission_classes([IsAuthenticated])  # Requires authenticated user.
def alpaca_asset_search(request):  # Defines asset-search controller.
    """
    Search Alpaca's active US equity universe.

    Examples:

        GET /api/alpaca/assets/search/?q=AAPL

        GET /api/alpaca/assets/search/?q=Microsoft
    """
    query = (  # Stores cleaned search input.
        request.query_params  # Accesses URL query string.
        .get("q", "")  # Reads q or uses an empty string.
        .strip()  # Removes surrounding whitespace.
    )
    if not query:  # Runs when the query is empty.
        return Response(  # Returns a valid empty search response rather than an error.
            {
                "query": "",  # Returns empty query.
                "count": 0,  # No matches.
                "provider": "Alpaca",  # Identifies provider.
                "results": [],  # Empty result collection.
            }
        )
    if len(query) > 100:  # Validates maximum query length.
        return Response(  # Rejects unreasonable input.
            {
                "error": "Search query is too long.",  # Explains validation failure.
            },
            status=status.HTTP_400_BAD_REQUEST,  # Returns client-input error status.
        )
    try:  # Attempts provider search.
        results = search_assets(  # Calls Alpaca service abstraction.
            query=query,  # Passes user's search string.
            limit=12,  # Limits results to twelve assets.
        )
        return Response(  # Sends successful search result.
            {
                "query": query,  # Echoes normalised query.
                "count": len(results),  # Counts returned matches.
                "provider": "Alpaca",  # Identifies provider.
                "results": results,  # Returns matching asset dictionaries.
            }
        )
    except AlpacaServiceError as error:  # Handles external provider failure.
        return Response(  # Sends service-unavailable result.
            {
                "error": str(error),  # Returns provider error text.
                "provider": "Alpaca",  # Identifies failing provider.
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,  # Reports external-service availability problem.
        )

# ============================================================
# 16. ALPACA ASSET DETAIL
# Programming concepts:
# - URL/path parameter
# - string conversion
# - service call
# ============================================================

@api_view(["GET"])  # Exposes the function as GET endpoint.
@permission_classes([IsAuthenticated])  # Restricts it to logged-in users.
def alpaca_asset_detail(  # Defines asset-detail endpoint.
    request,  # DRF request object.
    symbol,  # URL path parameter identifies requested asset.
):
    """
    Return Alpaca metadata for one asset.

    Example:

        GET /api/alpaca/assets/AAPL/
    """
    symbol = (  # Reassigns symbol to its normalised form.
        str(symbol)  # Ensures the value is a Python string.
        .strip()  # Removes unnecessary spaces.
        .upper()  # Normalises ticker case.
    )
    if not symbol:  # Validates required ticker.
        return Response(  # Sends validation error.
            {
                "error": "A symbol is required.",  # Explains missing value.
            },
            status=status.HTTP_400_BAD_REQUEST,  # Reports invalid client input.
        )
    try:  # Attempts provider lookup.
        asset = get_asset(symbol)  # Requests metadata through the Alpaca service layer.
        return Response(  # Returns successful API response.
            {
                "provider": "Alpaca",  # Identifies data source.
                "asset": asset,  # Returns asset metadata.
            }
        )
    except AlpacaServiceError as error:  # Handles provider failure.
        return Response(  # Returns structured provider error.
            {
                "error": str(error),  # Readable failure information.
                "provider": "Alpaca",  # Identifies provider.
                "symbol": symbol,  # Returns affected symbol.
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,  # Reports dependency unavailable.
        )

# ============================================================
# 17. ALPACA CURRENT STOCK SNAPSHOT
# Programming concepts:
# - multiple service calls
# - nested response data
# - configuration lookup
# ============================================================

@api_view(["GET"])  # Exposes GET endpoint.
@permission_classes([IsAuthenticated])  # Requires login.
def alpaca_stock_snapshot(  # Defines selected-stock snapshot API.
    request,  # DRF request object.
    symbol,  # Ticker supplied in URL path.
):
    """
    Return selected-asset metadata and current market snapshot.

    Example:

        GET /api/alpaca/stocks/AAPL/snapshot/

    RESPONSE CAN SUPPORT:

    Selected Asset Header
        ↓

    AAPL
    Apple Inc.
    Current Price
    Daily Change
    Open
    High
    Low
    Volume
    Bid / Ask
    """
    symbol = (  # Normalises path input.
        str(symbol)  # Converts it to a string.
        .strip()  # Removes surrounding whitespace.
        .upper()  # Converts ticker to uppercase.
    )
    if not symbol:  # Rejects missing ticker.
        return Response(  # Sends validation response.
            {
                "error": "A stock symbol is required.",  # User-facing validation message.
            },
            status=status.HTTP_400_BAD_REQUEST,  # Uses HTTP 400.
        )
    try:  # Attempts both Alpaca operations.
        asset = get_asset(symbol)  # Retrieves descriptive asset metadata.
        snapshot = get_stock_snapshot(symbol)  # Retrieves current price/snapshot information.
        return Response(  # Returns combined API object.
            {
                "provider": "Alpaca",  # Identifies provider.
                "feed": getattr(settings, "ALPACA_DATA_FEED", "iex"),  # Reads configured feed safely.
                "asset": asset,  # Returns company/asset metadata.
                "snapshot": snapshot,  # Returns current market information.
                "updated_at": timezone.now(),  # Records response generation time.
            }
        )
    except AlpacaServiceError as error:  # Handles either provider request failing.
        return Response(  # Returns failure response.
            {
                "error": str(error),  # Provider error message.
                "provider": "Alpaca",  # Provider identifier.
                "symbol": symbol,  # Affected stock ticker.
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,  # Reports provider unavailable.
        )

# ============================================================
# 18. ALPACA STOCK HISTORY
# Programming concepts:
# - path/query parameters
# - validation
# - Boolean conversion
# - nested dictionary
# - exceptions
# ============================================================

@api_view(["GET"])  # Exposes the function as a GET endpoint.
@permission_classes([IsAuthenticated])  # Requires authenticated user.
def alpaca_stock_history(  # Defines selected-asset historical-data endpoint.
    request,  # DRF request object.
    symbol,  # URL path parameter containing the selected ticker.
):
    """
    ============================================================
    ALPACA SELECTED-ASSET HISTORICAL OHLCV
    ============================================================

    Return historical OHLCV bars for any supported Alpaca US
    equity or ETF.

    Examples:

        GET /api/alpaca/stocks/AAPL/history/?period=1M

        GET /api/alpaca/stocks/MSFT/history/?period=3M

        GET /api/alpaca/stocks/NVDA/history/?period=1M

        GET /api/alpaca/stocks/SPY/history/?period=1M

    FRAMEWORK MAPPING:

    Search / Watchlist
        ↓
    User selects AAPL
        ↓
    Dashboard JavaScript
        ↓
    /api/alpaca/stocks/AAPL/history/
        ↓
    get_chart_history()
        ↓
    Alpaca Historical Market Data API
        ↓
    OHLCV points
        ↓
    Professional Chart

    THESE FIELDS SUPPORT:

    Candlestick:
        open
        high
        low
        close

    Line:
        close

    Heikin-Ashi:
        derived in the frontend or analytics layer from
        open/high/low/close

    Volume:
        volume

    NOTE:

    Volume Profile can later be derived from a suitable
    intraday price/volume dataset.

    Futures Curve is NOT generated here because a genuine
    futures curve requires contract maturity data rather than
    ordinary equity OHLCV.
    ============================================================
    """

    # ========================================================
    # 18.1 NORMALISE SYMBOL
    # ========================================================

    symbol = (  # Cleans the ticker supplied in the URL.
        str(symbol or "")  # Replaces a false-like value with empty string and ensures string type.
        .strip()  # Removes surrounding spaces.
        .upper()  # Normalises case.
    )
    if not symbol:  # Rejects missing ticker.
        return Response(  # Returns client validation failure.
            {
                "error": "A stock symbol is required.",  # Explains required value.
            },
            status=status.HTTP_400_BAD_REQUEST,  # HTTP 400 means invalid request.
        )

    # Prevent unreasonable URL values.
    if len(symbol) > 20:  # Validates ticker/path length.
        return Response(  # Rejects excessively long path value.
            {
                "error": "The supplied market symbol is too long.",  # Explains validation issue.
            },
            status=status.HTTP_400_BAD_REQUEST,  # Returns client-input error status.
        )

    # ========================================================
    # 18.2 NORMALISE PERIOD
    # ========================================================

    period = (  # Reads requested history period.
        request.query_params  # Accesses URL query parameters.
        .get("period", "1M")  # Retrieves period or defaults to one month.
        .strip()  # Removes spaces.
        .upper()  # Normalises to uppercase.
    )
    if period not in SUPPORTED_CHART_PERIODS:  # Checks period against allowed set.
        period = "1M"  # Invalid period safely falls back to one month.

    # ========================================================
    # 18.3 REQUEST ALPACA HISTORY
    # ========================================================

    try:  # Attempts historical-data service call.
        history = get_chart_history(  # Calls Alpaca service abstraction.
            symbol=symbol,  # Supplies selected ticker.
            period=period,  # Supplies validated chart period.
        )
        points = history.get("points") or []  # Retrieves points or uses an empty list.

        # ====================================================
        # 18.4 RETURN PROFESSIONAL-CHART RESPONSE
        # ====================================================

        return Response(  # Sends chart data to frontend.
            {
                "provider": "Alpaca",  # Identifies provider.
                "feed": history.get(  # Retrieves provider feed.
                    "feed",  # Attempts response value first.
                    getattr(settings, "ALPACA_DATA_FEED", "iex"),  # Falls back to project configuration.
                ),
                "symbol": symbol,  # Returns cleaned ticker.
                "period": period,  # Returns selected period.
                "timeframe": history.get("timeframe"),  # Returns provider timeframe.
                "has_data": bool(points),  # Boolean reports whether observations exist.
                "count": len(points),  # Counts observations.

                # --------------------------------------------
                # Preferred chart structure
                # --------------------------------------------

                "points": points,  # Returns normalised OHLCV points.

                # --------------------------------------------
                # Full original service result
                # --------------------------------------------

                "history": history,  # Also exposes the complete normalised service response.

                # --------------------------------------------
                # Chart capabilities
                # --------------------------------------------

                "chart_capabilities": {  # Describes which visualisations current data can support.
                    "candlestick": True,  # OHLC supports candlestick charts.
                    "line": True,  # Close prices support line charts.
                    "heikin_ashi": True,  # OHLC values can derive Heikin-Ashi candles.
                    "volume": True,  # Volume field supports volume bars.
                    "volume_profile": False,  # Requires additional implementation.
                    "futures_curve": False,  # Requires futures-contract maturity data.
                },
                "updated_at": timezone.now(),  # Adds response timestamp.
            }
        )
    except AlpacaServiceError as error:  # Handles provider failure.
        return Response(  # Returns predictable no-data response.
            {
                "provider": "Alpaca",  # Identifies attempted provider.
                "symbol": symbol,  # Returns affected ticker.
                "period": period,  # Returns requested period.
                "has_data": False,  # Reports no usable historical data.
                "count": 0,  # Zero chart points.
                "points": [],  # Empty chart collection.
                "error": str(error),  # Returns service error message.
                "chart_capabilities": {  # Keeps chart-capability structure consistent.
                    "candlestick": True,  # Data format supports this when provider is available.
                    "line": True,  # Data format supports line charts.
                    "heikin_ashi": True,  # Data format supports derived Heikin-Ashi.
                    "volume": True,  # Data format supports volume.
                    "volume_profile": False,  # Still not implemented.
                    "futures_curve": False,  # Still requires futures-specific data.
                },
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,  # Reports dependency unavailable.
        )

# ============================================================
# 19. STRATEGY API
# Programming concepts:
# - class
# - inheritance
# - class attributes
# - methods
# - self
# - ORM
# - encapsulation
# ============================================================

class StrategyViewSet(  # Defines an object-oriented API controller class.
    viewsets.ModelViewSet  # Inheritance gives the class standard CRUD REST behaviour.
):
    """
    Authenticated CRUD access to strategies belonging only to
    the currently logged-in user.
    """

    serializer_class = StrategySerializer  # Class attribute tells DRF which serializer handles Strategy objects.
    permission_classes = [IsAuthenticated]  # Class attribute restricts all ViewSet actions to logged-in users.

    def get_queryset(self):  # Method decides which Strategy records this particular request may access.
        return (  # Returns a Django QuerySet.
            Strategy.objects  # Begins Strategy database query.
            .filter(user=self.request.user)  # Limits records to the currently authenticated user.
            .order_by("-created_at")  # Sorts newest strategies first.
        )

    def perform_create(  # Method customises how DRF saves a newly submitted Strategy.
        self,  # self represents the current StrategyViewSet instance.
        serializer,  # serializer contains already-validated incoming strategy data.
    ):
        serializer.save(  # Persists the Strategy model instance.
            user=self.request.user  # Forces ownership to the authenticated user rather than trusting client input.
        )

# ============================================================
# 20. BACKTEST API
# Programming concepts:
# - class
# - inheritance
# - read-only behaviour
# - relationships
# - method overriding
# ============================================================

class BacktestViewSet(  # Defines another object-oriented REST API controller.
    viewsets.ReadOnlyModelViewSet  # Inheritance provides list/retrieve behaviour without create/update/delete actions.
):
    """
    Read-only API access to backtests belonging to strategies
    owned by the current user.
    """

    serializer_class = BacktestSerializer  # Tells DRF how Backtest model objects should be serialized.
    permission_classes = [IsAuthenticated]  # Requires authenticated access to all Backtest endpoints.

    def get_queryset(self):  # Overrides framework method to control accessible database records.
        return (  # Returns filtered QuerySet.
            Backtest.objects  # Begins Backtest database query.
            .filter(strategy__user=self.request.user)  # Follows Strategy relationship and restricts records to current user.
            .select_related("strategy")  # Joins Strategy in the same database query for efficiency.
            .order_by("-created_at")  # Sorts newest backtests first.
        )