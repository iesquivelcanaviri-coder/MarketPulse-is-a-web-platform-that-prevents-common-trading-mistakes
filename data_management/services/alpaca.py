"""
============================================================
MARKETPULSE - ALPACA MARKET DATA SERVICE
============================================================

SHORT PURPOSE:

This file is the main MarketPulse connection to Alpaca.

Instead of allowing every Django page to make its own Alpaca
request, MarketPulse puts Alpaca communication in one reusable
service module.

This makes the project easier to understand, maintain, test
and secure.

============================================================
FRAMEWORK MAPPING
============================================================

Browser / React / Django Template
        ↓
Django View / Django REST API
        ↓
data_management/services/alpaca.py
        ↓
Alpaca REST API
        ↓
Normalised Python dictionaries
        ↓
MarketPulse business logic
        ↓
PostgreSQL / Templates / Charts


EXAMPLES:

DATA IMPORT:

DataImportForm
    ↓
data_management/views.py
    ↓
data_management/tasks.py
    ↓
data_management/utils.py
    ↓
get_historical_bars()
    ↓
Alpaca
    ↓
core.MarketData
    ↓
PostgreSQL


DASHBOARD:

Dashboard JavaScript
    ↓
MarketPulse Django API
    ↓
get_stock_snapshot()
or
get_chart_history()
    ↓
Alpaca


MARKET CONDITION:

Data tab
    ↓
data_management/views.py
    ↓
get_market_condition_history()
    ↓
get_historical_bars()
    ↓
Alpaca Historical Bars
    ↓
core.MarketData
    ↓
identify_market_regime()
    ↓
MarketRegime
    ↓
Detailed Market Condition


RISK:

Risk workspace
    ↓
MarketPulse API
    ↓
get_stock_snapshot()
    ↓
Current Alpaca market information


============================================================
MAIN RESPONSIBILITIES
============================================================

1. Validate Alpaca configuration.
2. Authenticate server-side requests.
3. Search Alpaca's active US-equity universe.
4. Retrieve asset information.
5. Retrieve current stock snapshots.
6. Retrieve multiple stock snapshots.
7. Retrieve historical OHLCV bars.
8. Retrieve sufficient recent daily history for
   Market Condition analysis.
9. Retrieve US market clock information.
10. Build the Dashboard market overview.
11. Retrieve market history for Dashboard charts.


============================================================
IMPORTANT MARKET CONDITION ARCHITECTURE
============================================================

Market Condition does NOT create another Alpaca client.

Instead:

get_market_condition_history()
        ↓
get_historical_bars()
        ↓
_alpaca_get()
        ↓
Alpaca

This is an example of FUNCTION REUSE.

The same historical-data function is reused by several
different parts of MarketPulse.

Market Condition requires historical observations because
classification depends on:

- recent price direction
- moving averages
- historical volatility
- trend strength

One live price cannot calculate these measurements.

Current Alpaca snapshot data is therefore supplementary.

Historical daily OHLCV observations remain the main input for
MarketPulse Market Regime analysis.


============================================================
SECURITY
============================================================

The browser NEVER receives:

- ALPACA_API_KEY_ID
- ALPACA_API_SECRET_KEY

Credentials stay inside:

Local:
    .env

Production:
    Render Environment Variables

Django settings reads those values and this service uses them
only on the server.


============================================================
PROGRAMMING LANGUAGE CONCEPTS USED
============================================================

IMPORTS
    Reuse functionality from Python, Django and requests.

CLASS
    AlpacaServiceError creates a custom exception type.

INHERITANCE
    AlpacaServiceError inherits from Python's Exception class.

CONSTANT
    ALLOWED_DATA_FEEDS stores allowed configuration values.

FUNCTIONS
    Reusable blocks of logic such as get_historical_bars().

PARAMETERS
    Functions receive values such as symbol and start_date.

DEFAULT PARAMETERS
    Example:
        timeframe="1Day"

DICTIONARIES
    Store structured key/value market information.

LISTS
    Store collections of bars, assets and chart points.

SETS
    ALLOWED_DATA_FEEDS prevents duplicated feed names.

CONDITIONALS
    if / elif / else control decisions.

LOOPS
    for and while process assets, bars and API pages.

TRY / EXCEPT
    Handles network, conversion and API errors safely.

RAISE
    Creates controlled application errors.

RETURN
    Sends processed data back to the caller.

STRING METHODS
    strip(), upper(), lower(), rstrip(), lstrip().

TYPE CONVERSION
    str(), int(), float(), bool().

LIST COMPREHENSION
    Builds lists in a compact Python syntax.

LAMBDA
    Supplies a small anonymous sorting function.

SLICING
    Example:
        bars[-max_points:]

CACHING
    Django cache avoids unnecessary API requests.

HTTP
    requests.get() communicates with Alpaca.

============================================================
"""

# ============================================================
# 1. STANDARD LIBRARY IMPORTS
# ============================================================

from datetime import timedelta  # Imports timedelta so the code can calculate date ranges.
from urllib.parse import quote  # Imports quote so ticker symbols are safely placed inside URLs.

# ============================================================
# 2. THIRD-PARTY IMPORTS
# ============================================================

import requests  # Imports the requests library so Python can send HTTP requests to Alpaca.

# ============================================================
# 3. DJANGO IMPORTS
# ============================================================

from django.conf import settings  # Gives this service access to Django configuration values.
from django.core.cache import cache  # Gives the service Django's caching system.
from django.utils import timezone  # Gives timezone-aware Django date and time helpers.

# ============================================================
# 4. CUSTOM EXCEPTION
# ============================================================

class AlpacaServiceError(Exception):  # Defines a custom exception that inherits from Python's Exception class.
    """
    Raised when MarketPulse cannot successfully communicate
    with Alpaca or when the Alpaca configuration is invalid.

    Views and business-logic functions can catch this exception
    and display a friendly message instead of exposing raw
    external API errors.
    """

    pass  # The class needs no extra behaviour because the parent Exception class already provides it.

# ============================================================
# 5. SUPPORTED MARKET-DATA FEEDS
# ============================================================

ALLOWED_DATA_FEEDS = {  # Creates a set containing the Alpaca market-data feeds MarketPulse accepts.
    "iex",  # IEX market-data feed.
    "sip",  # SIP market-data feed.
    "delayed_sip",  # Delayed SIP feed.
    "boats",  # Alpaca BOATS feed.
    "overnight",  # Alpaca overnight feed.
    "otc",  # Over-the-counter feed.
}

# ============================================================
# 6. CONFIGURATION HELPERS
# ============================================================

def _normalise_base_url(url):  # Defines a private helper function for cleaning configured Alpaca URLs.
    """
    ------------------------------------------------------------
    NORMALISE ALPACA BASE URL
    ------------------------------------------------------------

    MarketPulse settings should ideally contain:

        https://paper-api.alpaca.markets

    and:

        https://data.alpaca.markets

    If /v2 or /v3 was accidentally included in the configured
    environment variable, remove it.

    This prevents malformed URLs such as:

        /v2/v2/assets
    ------------------------------------------------------------
    """

    if not url:  # Checks whether the supplied URL is empty or false.
        return ""  # Returns an empty string when no URL exists.

    cleaned_url = (  # Starts creating a cleaned version of the URL.
        str(url)  # Converts the supplied value to a string.
        .strip()  # Removes spaces from the beginning and end.
        .rstrip("/")  # Removes a trailing slash.
    )

    for ending in (  # Loops over URL suffixes that should not be present.
        "/v2",  # Alpaca API version 2 suffix.
        "/v3",  # Alpaca API version 3 suffix.
    ):
        if cleaned_url.endswith(ending):  # Checks whether the URL ends with the current suffix.
            cleaned_url = (  # Reassigns the cleaned URL.
                cleaned_url[:-len(ending)]  # Uses slicing to remove the unwanted suffix.
            )

    return cleaned_url.rstrip("/")  # Returns the final URL without a trailing slash.

# ============================================================
# 7. TRADING API BASE URL
# ============================================================

def _trading_base_url():  # Defines a private helper for retrieving Alpaca's trading API URL.
    """
    Return the configured Alpaca Trading API base URL.
    """

    url = _normalise_base_url(  # Passes the configured URL through the normalisation helper.
        getattr(  # Safely reads an attribute from Django settings.
            settings,  # Reads from the Django settings object.
            "ALPACA_TRADING_BASE_URL",  # Name of the setting to read.
            "https://paper-api.alpaca.markets",  # Default value if the setting does not exist.
        )
    )

    if not url:  # Checks whether a usable URL exists.
        raise AlpacaServiceError(  # Raises the project's custom Alpaca exception.
            "ALPACA_TRADING_BASE_URL is not configured."  # Friendly configuration error message.
        )

    return url  # Returns the valid trading API base URL.

# ============================================================
# 8. MARKET DATA API BASE URL
# ============================================================

def _data_base_url():  # Defines a private helper for retrieving Alpaca's market-data URL.
    """
    Return the configured Alpaca Market Data API base URL.
    """

    url = _normalise_base_url(  # Cleans the URL before it is used.
        getattr(  # Reads an optional setting safely.
            settings,  # Django settings object.
            "ALPACA_DATA_BASE_URL",  # Name of the market-data setting.
            "https://data.alpaca.markets",  # Default Alpaca data URL.
        )
    )

    if not url:  # Checks whether the data URL is missing.
        raise AlpacaServiceError(  # Stops the request with a controlled exception.
            "ALPACA_DATA_BASE_URL is not configured."  # Explains the configuration problem.
        )

    return url  # Returns the cleaned market-data base URL.

# ============================================================
# 9. MARKET DATA FEED
# ============================================================

def _data_feed():  # Defines a private function for reading the configured Alpaca feed.
    """
    Return the configured stock market-data feed.

    MarketPulse currently normally uses:

        iex
    """

    feed = (  # Begins reading the feed configuration.
        getattr(  # Reads the value safely from Django settings.
            settings,  # Django settings object.
            "ALPACA_DATA_FEED",  # Setting containing the selected feed.
            "iex",  # Uses IEX if the setting does not exist.
        )
        or "iex"  # Also falls back to IEX if the configured value is empty.
    )

    feed = (  # Cleans and standardises the feed name.
        str(feed)  # Converts it to a string.
        .strip()  # Removes surrounding whitespace.
        .lower()  # Converts it to lowercase.
    )

    if feed not in ALLOWED_DATA_FEEDS:  # Checks membership in the allowed-feed set.
        raise AlpacaServiceError(  # Raises a controlled error for invalid configuration.
            (
                "Invalid ALPACA_DATA_FEED configuration: "  # First part of the error message.
                f"{feed}"  # f-string inserts the actual configured feed.
            )
        )

    return feed  # Returns the validated feed name.

# ============================================================
# 10. REQUEST TIMEOUT
# ============================================================

def _request_timeout():  # Defines a helper for the maximum Alpaca HTTP waiting time.
    """
    Return the maximum number of seconds an Alpaca HTTP
    request should wait before failing.
    """

    try:  # Starts exception handling because converting the configuration may fail.
        timeout = int(  # Converts the configured timeout to an integer.
            getattr(  # Reads the setting safely.
                settings,  # Django settings object.
                "ALPACA_REQUEST_TIMEOUT",  # Name of the timeout setting.
                8,  # Uses eight seconds by default.
            )
        )
    except (TypeError, ValueError):  # Handles an invalid non-integer configuration value.
        timeout = 8  # Falls back to a safe eight-second timeout.

    return max(1, timeout)  # Ensures the timeout can never be less than one second.

# ============================================================
# 11. ALPACA AUTHENTICATION HEADERS
# ============================================================

def _alpaca_headers():  # Builds the HTTP headers required to authenticate with Alpaca.
    """
    ------------------------------------------------------------
    BUILD ALPACA AUTHENTICATION HEADERS
    ------------------------------------------------------------

    Credentials are read from Django settings.

    They should originate from private environment variables,
    not from source code.
    ------------------------------------------------------------
    """

    api_key = (  # Begins loading the Alpaca API key.
        getattr(  # Safely reads a Django setting.
            settings,  # Django settings object.
            "ALPACA_API_KEY_ID",  # Environment-backed API key setting.
            "",  # Empty string if no key exists.
        )
        or ""  # Also protects against None.
    )

    secret_key = (  # Begins loading the Alpaca API secret.
        getattr(  # Safely reads the Django setting.
            settings,  # Django settings object.
            "ALPACA_API_SECRET_KEY",  # Environment-backed secret key setting.
            "",  # Empty string if it does not exist.
        )
        or ""  # Also handles None.
    )

    api_key = (  # Standardises the API key value.
        str(api_key)  # Converts the value into a string.
        .strip()  # Removes accidental spaces.
    )

    secret_key = (  # Standardises the API secret value.
        str(secret_key)  # Converts the value into a string.
        .strip()  # Removes accidental spaces.
    )

    if not api_key:  # Checks whether the public API key is missing.
        raise AlpacaServiceError(  # Raises a controlled service-level exception.
            "ALPACA_API_KEY_ID is not configured."  # Explains which setting is missing.
        )

    if not secret_key:  # Checks whether the API secret is missing.
        raise AlpacaServiceError(  # Raises the same custom exception type.
            "ALPACA_API_SECRET_KEY is not configured."  # Explains which setting is missing.
        )

    return {  # Returns a Python dictionary of HTTP headers.
        "APCA-API-KEY-ID": api_key,  # Sends the Alpaca API key only from the server.
        "APCA-API-SECRET-KEY": secret_key,  # Sends the Alpaca secret only from the server.
        "Accept": "application/json",  # Tells Alpaca that MarketPulse expects JSON.
    }

# ============================================================
# 12. GENERIC ALPACA GET REQUEST
# ============================================================

def _alpaca_get(base_url, path, params=None):  # Centralises all authenticated HTTP GET requests.
    """
    ------------------------------------------------------------
    PERFORM AUTHENTICATED ALPACA GET REQUEST
    ------------------------------------------------------------

    All GET requests from this service pass through this
    function.

    This provides one central location for:

    - authentication
    - request timeouts
    - HTTP errors
    - network failures
    - JSON decoding
    ------------------------------------------------------------
    """

    url = (  # Builds the complete URL used for the HTTP request.
        base_url.rstrip("/")  # Removes a trailing slash from the base.
        + "/"  # Adds exactly one separator.
        + path.lstrip("/")  # Removes a leading slash from the endpoint path.
    )

    try:  # Starts controlled handling of network problems.
        response = requests.get(  # Sends an HTTP GET request using the requests library.
            url,  # Destination Alpaca URL.
            headers=_alpaca_headers(),  # Adds secure authentication headers.
            params=params or {},  # Adds query parameters or an empty dictionary.
            timeout=_request_timeout(),  # Prevents the request from hanging forever.
        )
    except requests.Timeout as exc:  # Catches requests that take too long.
        raise AlpacaServiceError(  # Converts the low-level library error into a MarketPulse error.
            (
                "The Alpaca request timed out. "
                "Please try again."
            )
        ) from exc  # Keeps the original exception linked for debugging.
    except requests.ConnectionError as exc:  # Handles failures connecting to Alpaca.
        raise AlpacaServiceError(
            (
                "MarketPulse could not connect to Alpaca. "
                "Check the internet connection and try again."
            )
        ) from exc
    except requests.RequestException as exc:  # Handles other requests-library errors.
        raise AlpacaServiceError(
            (
                "An unexpected network error occurred while "
                "communicating with Alpaca."
            )
        ) from exc

    # ========================================================
    # 12.1 HTTP ERROR HANDLING
    # ========================================================

    if not response.ok:  # Checks whether Alpaca returned a non-success HTTP status.
        message = ""  # Creates an empty optional API error message.

        try:  # Attempts to read Alpaca's response as JSON.
            error_data = response.json() or {}  # Uses an empty dictionary when JSON is empty.
            if isinstance(error_data, dict):  # Confirms the response is a dictionary.
                message = (  # Attempts to find a useful Alpaca error description.
                    error_data.get("message")  # Uses a standard message field first.
                    or error_data.get("error")  # Otherwise checks an error field.
                    or ""  # Uses an empty string if neither exists.
                )
        except ValueError:  # Handles responses that are not valid JSON.
            message = ""  # Continues without an API-specific message.

        if response.status_code == 401:  # Handles HTTP authentication failure.
            friendly_message = (
                "Alpaca authentication failed. "
                "Check the configured API credentials."
            )
        elif response.status_code == 403:  # Handles permission or subscription restrictions.
            friendly_message = (
                "Alpaca rejected this request because the "
                "account is not entitled to the requested "
                "market-data resource or feed."
            )
        elif response.status_code == 404:  # Handles missing resources.
            friendly_message = (
                "The requested Alpaca resource was not found."
            )
        elif response.status_code == 429:  # Handles API rate limiting.
            friendly_message = (
                "The Alpaca API rate limit was reached. "
                "Please wait briefly and try again."
            )
        elif response.status_code >= 500:  # Handles Alpaca server failures.
            friendly_message = (
                "Alpaca is temporarily unavailable. "
                "Please try again later."
            )
        else:  # Handles any other HTTP error status.
            friendly_message = (
                f"Alpaca returned HTTP {response.status_code}."  # f-string includes the status code.
            )

        if message:  # Checks whether Alpaca supplied additional error information.
            friendly_message += f" {message}"  # Appends that information to MarketPulse's message.

        raise AlpacaServiceError(friendly_message)  # Stops processing and returns a controlled error.

    # ========================================================
    # 12.2 JSON RESPONSE
    # ========================================================

    try:  # Tries to convert the successful HTTP response into Python data.
        return response.json()  # Returns the decoded JSON dictionary/list.
    except ValueError as exc:  # Handles a successful response containing invalid JSON.
        raise AlpacaServiceError(
            (
                "Alpaca returned a response that MarketPulse "
                "could not interpret as JSON."
            )
        ) from exc

# ============================================================
# 13. VALUE NORMALISATION HELPERS
# ============================================================

def _to_float(value):  # Converts external API values into Python floating-point numbers.
    """
    Convert an API value into a float when possible.
    """

    if value is None:  # Checks explicitly for missing data.
        return None  # Keeps missing data represented as None.

    try:  # Attempts numerical conversion.
        return float(value)  # Converts strings or numbers into a float.
    except (TypeError, ValueError):  # Handles data that cannot be converted.
        return None  # Returns None rather than crashing the application.

def _to_int(value):  # Converts external API values into Python integer values.
    """
    Convert an API value into an integer when possible.
    """

    if value is None:  # Checks for missing API data.
        return None  # Keeps missing values as None.

    try:  # Attempts integer conversion.
        return int(value)  # Returns a Python integer.
    except (TypeError, ValueError):  # Handles invalid values safely.
        return None  # Returns None instead of raising an error.

# ============================================================
# 14. NORMALISE ALPACA ASSET
# ============================================================

def _normalise_asset(asset):  # Converts Alpaca asset JSON into MarketPulse's consistent structure.
    """
    Convert Alpaca's raw asset response into a predictable
    MarketPulse dictionary.
    """

    if not isinstance(asset, dict):  # Ensures the incoming value is a dictionary.
        return {}  # Returns an empty dictionary for an unexpected response.

    return {  # Builds and returns a normalised Python dictionary.
        "id": asset.get("id"),  # Reads Alpaca's asset identifier.
        "symbol": (asset.get("symbol") or "").upper(),  # Reads and uppercases the ticker symbol.
        "name": asset.get("name") or "",  # Reads the company or asset name.
        "exchange": asset.get("exchange") or "",  # Reads the exchange.
        "asset_class": (  # Normalises different possible Alpaca asset-class field names.
            asset.get("class")
            or asset.get("asset_class")
            or ""
        ),
        "status": asset.get("status") or "",  # Reads whether Alpaca considers the asset active.
        "tradable": bool(asset.get("tradable", False)),  # Converts tradability to a Boolean.
        "marginable": bool(asset.get("marginable", False)),  # Converts margin availability to a Boolean.
        "shortable": bool(asset.get("shortable", False)),  # Converts shortability to a Boolean.
        "fractionable": bool(asset.get("fractionable", False)),  # Converts fractional support to a Boolean.
        "borrow_status": asset.get("borrow_status") or "",  # Reads optional short-borrow status.
    }

# ============================================================
# 15. NORMALISE ALPACA BAR
# ============================================================

def _normalise_bar(bar, symbol=None):  # Converts one Alpaca OHLCV bar into a readable dictionary.
    """
    ------------------------------------------------------------
    NORMALISE ALPACA OHLCV BAR
    ------------------------------------------------------------

    Alpaca normally returns compact field names:

        t = timestamp
        o = open
        h = high
        l = low
        c = close
        v = volume
        n = trade count
        vw = volume-weighted average price

    MarketPulse converts these into readable field names.
    ------------------------------------------------------------
    """

    if not isinstance(bar, dict):  # Ensures the API bar is dictionary data.
        return None  # Returns None when the supplied bar cannot be processed.

    timestamp = (  # Reads the timestamp using either Alpaca naming style.
        bar.get("t")
        or bar.get("timestamp")
    )

    date_value = None  # Starts with no extracted date.

    if timestamp:  # Checks whether a timestamp exists.
        date_value = str(timestamp)[:10]  # Uses string slicing to keep YYYY-MM-DD.

    return {  # Returns a normalised OHLCV dictionary.
        "symbol": symbol.upper() if symbol else None,  # Adds an uppercase ticker when supplied.
        "timestamp": timestamp,  # Stores the original timestamp.
        "date": date_value,  # Stores the simplified trading date.
        "open": _to_float(  # Converts the opening price to a float.
            bar.get("o") if "o" in bar else bar.get("open")
        ),
        "high": _to_float(  # Converts the high price to a float.
            bar.get("h") if "h" in bar else bar.get("high")
        ),
        "low": _to_float(  # Converts the low price to a float.
            bar.get("l") if "l" in bar else bar.get("low")
        ),
        "close": _to_float(  # Converts the closing price to a float.
            bar.get("c") if "c" in bar else bar.get("close")
        ),
        "volume": _to_int(  # Converts trading volume to an integer.
            bar.get("v") if "v" in bar else bar.get("volume")
        ),
        "trade_count": _to_int(  # Converts Alpaca trade count to an integer.
            bar.get("n") if "n" in bar else bar.get("trade_count")
        ),
        "vwap": _to_float(  # Converts volume-weighted average price to a float.
            bar.get("vw") if "vw" in bar else bar.get("vwap")
        ),
    }

# ============================================================
# 16. NORMALISE ALPACA SNAPSHOT
# ============================================================

def _normalise_snapshot(raw_snapshot, feed=None):  # Converts Alpaca snapshot JSON into MarketPulse format.
    """
    Convert the Alpaca snapshot response into data that the
    Dashboard, Risk and Data tab can consume consistently.
    """

    if not isinstance(raw_snapshot, dict):  # Checks that the raw response is dictionary data.
        raw_snapshot = {}  # Replaces invalid input with an empty dictionary.

    latest_trade = (  # Retrieves the most recent trade object.
        raw_snapshot.get("latestTrade")
        or raw_snapshot.get("latest_trade")
        or {}
    )

    latest_quote = (  # Retrieves the most recent bid/ask quote.
        raw_snapshot.get("latestQuote")
        or raw_snapshot.get("latest_quote")
        or {}
    )

    minute_bar_raw = (  # Retrieves Alpaca's latest one-minute bar.
        raw_snapshot.get("minuteBar")
        or raw_snapshot.get("minute_bar")
        or {}
    )

    daily_bar_raw = (  # Retrieves the current daily OHLCV bar.
        raw_snapshot.get("dailyBar")
        or raw_snapshot.get("daily_bar")
        or {}
    )

    previous_daily_bar_raw = (  # Retrieves the previous completed daily bar.
        raw_snapshot.get("prevDailyBar")
        or raw_snapshot.get("previous_daily_bar")
        or {}
    )

    latest_price = _to_float(  # Extracts and converts the latest traded price.
        latest_trade.get("p")
        if "p" in latest_trade
        else latest_trade.get("price")
    )

    bid_price = _to_float(  # Extracts the current bid price.
        latest_quote.get("bp")
        if "bp" in latest_quote
        else latest_quote.get("bid_price")
    )

    ask_price = _to_float(  # Extracts the current ask price.
        latest_quote.get("ap")
        if "ap" in latest_quote
        else latest_quote.get("ask_price")
    )

    spread = None  # Starts without a calculated bid/ask spread.

    if bid_price is not None and ask_price is not None:  # Requires both prices before calculating spread.
        spread = ask_price - bid_price  # Arithmetic operator subtracts bid from ask.

    daily_bar = _normalise_bar(daily_bar_raw)  # Normalises the current daily bar.
    previous_daily_bar = _normalise_bar(previous_daily_bar_raw)  # Normalises the previous daily bar.
    minute_bar = _normalise_bar(minute_bar_raw)  # Normalises the latest minute bar.

    previous_close = (  # Reads the previous close only when a previous bar exists.
        previous_daily_bar.get("close")
        if previous_daily_bar
        else None
    )

    daily_change = None  # Starts with no absolute daily change.
    daily_change_pct = None  # Starts with no percentage daily change.

    if (  # Calculates changes only when both prices exist and previous close is non-zero.
        latest_price is not None
        and previous_close is not None
        and previous_close != 0
    ):
        daily_change = latest_price - previous_close  # Calculates absolute price movement.
        daily_change_pct = (  # Calculates percentage movement.
            daily_change
            / previous_close
            * 100
        )

    return {  # Returns a predictable snapshot dictionary used by several MarketPulse pages.
        "feed": feed or _data_feed(),  # Uses the supplied feed or the configured feed.
        "latest_price": latest_price,  # Stores the most recent traded price.
        "latest_trade_timestamp": (  # Stores when the latest trade occurred.
            latest_trade.get("t")
            or latest_trade.get("timestamp")
        ),
        "bid_price": bid_price,  # Stores current bid.
        "ask_price": ask_price,  # Stores current ask.
        "spread": spread,  # Stores calculated bid/ask spread.
        "previous_close": previous_close,  # Stores previous session close.
        "daily_change": daily_change,  # Stores absolute daily movement.
        "daily_change_pct": daily_change_pct,  # Stores percentage daily movement.
        "minute_bar": minute_bar,  # Stores the latest minute OHLCV bar.
        "daily_bar": daily_bar,  # Stores the current daily OHLCV bar.
        "previous_daily_bar": previous_daily_bar,  # Stores the previous daily OHLCV bar.
    }

# ============================================================
# 17. GET ACTIVE US EQUITIES
# ============================================================

def get_active_us_equities():  # Retrieves Alpaca's active US-equity universe.
    """
    ------------------------------------------------------------
    GET ALPACA ACTIVE US EQUITY UNIVERSE
    ------------------------------------------------------------

    The complete universe is cached because downloading the
    full asset list for every search keystroke would be
    inefficient.
    ------------------------------------------------------------
    """

    cache_key = "marketpulse_alpaca_active_us_equities"  # Creates a stable key for Django's cache.

    cached_assets = cache.get(cache_key)  # Checks whether the asset universe is already cached.

    if cached_assets is not None:  # Uses the cached result when available.
        return cached_assets  # Avoids making another Alpaca HTTP request.

    response = _alpaca_get(  # Uses the shared authenticated GET helper.
        _trading_base_url(),  # Sends the request to Alpaca's trading API.
        "/v2/assets",  # Alpaca endpoint containing assets.
        params={  # Supplies URL query parameters.
            "status": "active",  # Requests only active assets.
            "asset_class": "us_equity",  # Requests only US equities.
        },
    )

    if not isinstance(response, list):  # Verifies Alpaca returned the expected list.
        raise AlpacaServiceError(
            "Alpaca returned an unexpected asset response."
        )

    assets = []  # Creates an empty Python list for normalised assets.

    for raw_asset in response:  # Iterates through every raw Alpaca asset.
        asset = _normalise_asset(raw_asset)  # Reuses the asset-normalisation helper.

        if asset and asset.get("symbol"):  # Keeps only useful asset records containing a symbol.
            assets.append(asset)  # Adds the asset dictionary to the list.

    cache_seconds = int(  # Converts the configured cache duration into an integer.
        getattr(
            settings,
            "ALPACA_ASSET_CACHE_SECONDS",
            1800,
        )
    )

    cache.set(  # Stores the completed asset universe in Django's cache.
        cache_key,  # Cache identifier.
        assets,  # Value being cached.
        cache_seconds,  # Number of seconds before expiry.
    )

    return assets  # Returns all normalised active US equities.

# ============================================================
# 18. SEARCH ALPACA ASSETS
# ============================================================

def search_assets(query, limit=12):  # Searches cached Alpaca assets using symbol and company name.
    """
    ------------------------------------------------------------
    SEARCH ACTIVE ALPACA ASSETS
    ------------------------------------------------------------

    Search by:

    - exact ticker
    - ticker beginning
    - ticker containing query
    - company name beginning
    - company name containing query

    Results are ranked so the most obvious match appears first.
    ------------------------------------------------------------
    """

    query = query or ""  # Replaces None or another false value with an empty string.
    query = str(query).strip().upper()  # Standardises the search term.

    if not query:  # Stops when the user has not supplied meaningful search text.
        return []  # Returns an empty list.

    try:  # Attempts to convert the requested result limit.
        limit = int(limit)  # Converts the value into an integer.
    except (TypeError, ValueError):  # Handles invalid limits.
        limit = 12  # Uses the default search size.

    limit = max(1, min(limit, 50))  # Restricts the number of results between 1 and 50.

    assets = get_active_us_equities()  # Reuses the cached full asset universe.
    ranked = []  # Creates an empty list that will contain ranking tuples.

    for asset in assets:  # Loops through every active Alpaca asset.
        symbol = asset.get("symbol", "").upper()  # Reads and standardises the symbol.
        name = asset.get("name", "").upper()  # Reads and standardises the company name.
        score = None  # Starts with no search-match ranking.

        if symbol == query:  # Exact ticker match receives the best score.
            score = 0
        elif symbol.startswith(query):  # Ticker-prefix match receives the next-best score.
            score = 1
        elif query in symbol:  # Ticker containing the text receives score 2.
            score = 2
        elif name.startswith(query):  # Company-name prefix receives score 3.
            score = 3
        elif query in name:  # Company-name substring receives score 4.
            score = 4

        if score is None:  # Checks whether the asset did not match the search.
            continue  # Skips directly to the next loop iteration.

        tradable_penalty = (  # Gives tradable assets a slight ranking advantage.
            0
            if asset.get("tradable")
            else 1
        )

        ranked.append(  # Adds a sortable tuple to the ranked results.
            (
                score,  # Primary ranking based on match quality.
                tradable_penalty,  # Secondary ranking prefers tradable assets.
                len(symbol),  # Third ranking prefers shorter ticker symbols.
                symbol,  # Fourth ranking sorts alphabetically.
                asset,  # Final tuple value keeps the actual asset dictionary.
            )
        )

    ranked.sort(  # Sorts the list in place.
        key=lambda row: (  # Lambda creates a small anonymous sorting function.
            row[0],  # Sort by search score.
            row[1],  # Then tradable penalty.
            row[2],  # Then symbol length.
            row[3],  # Then symbol alphabetically.
        )
    )

    return [  # Uses a list comprehension to return only asset dictionaries.
        row[4]  # Selects the asset from each ranking tuple.
        for row in ranked[:limit]  # Uses slicing to keep only the requested number.
    ]

# ============================================================
# 19. GET ONE ALPACA ASSET
# ============================================================

def get_asset(symbol):  # Retrieves Alpaca metadata for one ticker.
    """
    Retrieve metadata for one Alpaca asset.
    """

    symbol = symbol or ""  # Replaces a missing symbol with an empty string.
    symbol = str(symbol).strip().upper()  # Standardises the ticker.

    if not symbol:  # Makes sure a ticker was supplied.
        raise AlpacaServiceError("A symbol is required.")  # Stops with a controlled validation error.

    cache_key = "marketpulse_alpaca_asset_" + symbol  # Creates a symbol-specific cache key.
    cached_asset = cache.get(cache_key)  # Checks the Django cache.

    if cached_asset is not None:  # Uses cached metadata when possible.
        return cached_asset  # Avoids another Alpaca request.

    response = _alpaca_get(  # Sends a centralised authenticated Alpaca request.
        _trading_base_url(),  # Uses the trading API base URL.
        (
            "/v2/assets/"  # Alpaca asset-detail endpoint.
            + quote(symbol, safe="")  # URL-encodes the ticker safely.
        ),
    )

    asset = _normalise_asset(response)  # Converts Alpaca's response to MarketPulse format.

    if not asset:  # Checks whether normalisation produced useful data.
        raise AlpacaServiceError(
            (
                f"Alpaca returned no asset information "
                f"for {symbol}."
            )
        )

    cache.set(  # Caches the metadata so repeated lookups are cheaper.
        cache_key,  # Symbol-specific cache identifier.
        asset,  # Asset dictionary being stored.
        1800,  # Cache duration in seconds.
    )

    return asset  # Returns normalised asset information.

# ============================================================
# 20. GET ONE STOCK SNAPSHOT
# ============================================================

def get_stock_snapshot(symbol):  # Retrieves current/latest Alpaca market context for one ticker.
    """
    ------------------------------------------------------------
    GET ALPACA STOCK SNAPSHOT
    ------------------------------------------------------------

    Returns current/latest information including:

    - latest trade
    - latest quote
    - bid
    - ask
    - spread
    - minute bar
    - daily bar
    - previous daily bar
    - daily price change

    IMPORTANT:

    Snapshot data represents current/latest market context.

    Market Condition classification itself uses historical
    daily bars rather than one current quote.
    ------------------------------------------------------------
    """

    symbol = symbol or ""  # Handles None or another empty value.
    symbol = str(symbol).strip().upper()  # Standardises the ticker.

    if not symbol:  # Validates that a ticker exists.
        raise AlpacaServiceError("A symbol is required.")  # Raises a controlled validation error.

    feed = _data_feed()  # Reuses the configured and validated Alpaca feed.

    cache_key = (  # Creates a unique cache key for feed and ticker.
        "marketpulse_alpaca_snapshot_"
        + feed
        + "_"
        + symbol
    )

    cached_snapshot = cache.get(cache_key)  # Checks whether a recent snapshot is cached.

    if cached_snapshot is not None:  # Uses recent cached data where available.
        return cached_snapshot  # Returns without calling Alpaca again.

    response = _alpaca_get(  # Calls the central HTTP request function.
        _data_base_url(),  # Uses the market-data API.
        (
            "/v2/stocks/"  # Alpaca stock endpoint.
            + quote(symbol, safe="")  # Safely URL-encodes the ticker.
            + "/snapshot"  # Requests the snapshot resource.
        ),
        params={  # Adds Alpaca query parameters.
            "feed": feed,  # Uses the configured feed.
            "currency": "USD",  # Requests US-dollar values.
        },
    )

    snapshot = _normalise_snapshot(  # Converts raw Alpaca fields into MarketPulse fields.
        response,
        feed=feed,
    )

    snapshot["symbol"] = symbol  # Adds the ticker explicitly to the normalised dictionary.

    cache_seconds = int(  # Reads how long current snapshots should be cached.
        getattr(
            settings,
            "ALPACA_SNAPSHOT_CACHE_SECONDS",
            15,
        )
    )

    cache.set(  # Stores the snapshot temporarily.
        cache_key,
        snapshot,
        cache_seconds,
    )

    return snapshot  # Returns the normalised current-market snapshot.

# ============================================================
# 21. GET MULTIPLE STOCK SNAPSHOTS
# ============================================================

def get_stock_snapshots(symbols):  # Retrieves current market snapshots for several tickers in one call.
    """
    ------------------------------------------------------------
    GET MULTIPLE ALPACA STOCK SNAPSHOTS
    ------------------------------------------------------------

    Useful for Dashboard benchmark data because multiple
    symbols can be requested together.
    ------------------------------------------------------------
    """

    if isinstance(symbols, str):  # Checks whether the caller supplied a comma-separated string.
        symbols = symbols.split(",")  # Splits the string into a Python list.

    cleaned_symbols = []  # Creates the final validated ticker list.

    for symbol in symbols or []:  # Iterates through supplied symbols or an empty list.
        symbol = str(symbol).strip().upper()  # Standardises each symbol.

        if symbol and symbol not in cleaned_symbols:  # Keeps non-empty symbols and avoids duplicates.
            cleaned_symbols.append(symbol)  # Adds the ticker to the request list.

    if not cleaned_symbols:  # Checks whether any valid tickers remain.
        return {}  # Returns an empty dictionary when there is nothing to request.

    cleaned_symbols = cleaned_symbols[:50]  # Uses slicing to prevent an accidentally huge request.
    feed = _data_feed()  # Loads the configured market-data feed.

    response = _alpaca_get(  # Sends one request for the full ticker group.
        _data_base_url(),  # Uses Alpaca's market-data API.
        "/v2/stocks/snapshots",  # Uses Alpaca's multi-snapshot endpoint.
        params={  # Supplies query parameters.
            "symbols": ",".join(cleaned_symbols),  # join() converts the list into comma-separated symbols.
            "feed": feed,  # Selects the Alpaca feed.
            "currency": "USD",  # Requests USD prices.
        },
    )

    if not isinstance(response, dict):  # Confirms the expected JSON object was returned.
        raise AlpacaServiceError(
            (
                "Alpaca returned an unexpected multi-symbol "
                "snapshot response."
            )
        )

    snapshots = {}  # Creates an empty dictionary keyed by ticker.

    for symbol in cleaned_symbols:  # Processes each requested symbol.
        raw_snapshot = (  # Retrieves that symbol's raw response.
            response.get(symbol)
            or response.get(symbol.upper())
        )

        if raw_snapshot is None:  # Checks whether Alpaca omitted this symbol.
            continue  # Skips to the next symbol.

        snapshot = _normalise_snapshot(  # Reuses the same normalisation function as single snapshots.
            raw_snapshot,
            feed=feed,
        )

        snapshot["symbol"] = symbol  # Adds the ticker to its dictionary.
        snapshots[symbol] = snapshot  # Stores it under the ticker key.

    return snapshots  # Returns all successfully retrieved snapshots.

# ============================================================
# 22. GET HISTORICAL BARS
# ============================================================

def get_historical_bars(
    symbol,  # Ticker that historical data is required for.
    start_date,  # Beginning of the requested historical period.
    end_date,  # End of the requested historical period.
    timeframe="1Day",  # Default argument requests daily bars.
    adjustment="raw",  # Default argument requests raw Alpaca price data.
    limit=10000,  # Default maximum records requested per API page.
):
    """
    ------------------------------------------------------------
    GET ALPACA HISTORICAL OHLCV DATA
    ------------------------------------------------------------

    This is MarketPulse's CENTRAL historical-data retrieval
    function.

    Other parts of the application should reuse this function
    rather than implementing additional direct Alpaca
    historical-data requests.

    Used by:

        data_management/utils.py

        Market Data imports

        Dashboard charts

        Market Condition data preparation

        Strategy analysis

        Risk analytics

        Stress testing


    PARAMETERS:

    symbol
        Example:
            AAPL

    start_date
        Example:
            2025-01-01

    end_date
        Example:
            2026-09-04

    timeframe
        Default:
            1Day

    adjustment
        Default:
            raw

    limit
        Maximum bars requested per Alpaca page.


    PAGINATION:

    If Alpaca returns more data than one response can contain,
    next_page_token is followed automatically.
    ------------------------------------------------------------
    """

    symbol = symbol or ""  # Protects against a None symbol.
    symbol = str(symbol).strip().upper()  # Converts the ticker to MarketPulse's standard format.

    if not symbol:  # Checks whether a usable ticker exists.
        raise AlpacaServiceError("A symbol is required.")  # Stops the function when no ticker was supplied.

    if not start_date:  # Checks whether a start date exists.
        raise AlpacaServiceError(
            "A start date is required for historical data."
        )

    if not end_date:  # Checks whether an end date exists.
        raise AlpacaServiceError(
            "An end date is required for historical data."
        )

    start_value = (  # Converts Python date/datetime objects into API-compatible text.
        start_date.isoformat()
        if hasattr(start_date, "isoformat")  # hasattr checks whether the object supports isoformat().
        else str(start_date)
    )

    end_value = (  # Performs the same conversion for the end date.
        end_date.isoformat()
        if hasattr(end_date, "isoformat")
        else str(end_date)
    )

    try:  # Attempts to normalise the requested pagination limit.
        limit = int(limit)  # Converts the supplied value to an integer.
    except (TypeError, ValueError):  # Handles invalid values safely.
        limit = 10000  # Restores the default limit.

    limit = max(1, min(limit, 10000))  # Ensures the value stays between 1 and 10,000.
    feed = _data_feed()  # Loads the configured Alpaca data feed.
    all_bars = []  # Creates a list that will collect bars from every API page.
    page_token = None  # Starts with no pagination token.
    page_count = 0  # Counts how many pages have been requested.
    max_pages = 100  # Safety limit preventing an accidental infinite pagination loop.

    while True:  # Starts a loop that continues until Alpaca has no next page.
        page_count += 1  # Increment assignment adds one to the page counter.

        if page_count > max_pages:  # Stops if pagination behaves unexpectedly.
            raise AlpacaServiceError(
                (
                    "Historical-data pagination exceeded "
                    "the MarketPulse safety limit."
                )
            )

        params = {  # Creates the query-parameter dictionary for Alpaca.
            "timeframe": timeframe,  # Requests daily, minute, or another supported bar interval.
            "start": start_value,  # Beginning of requested period.
            "end": end_value,  # End of requested period.
            "limit": limit,  # Maximum records requested in this page.
            "adjustment": adjustment,  # Raw or adjusted data setting.
            "feed": feed,  # Market-data source such as IEX.
            "sort": "asc",  # Requests observations oldest to newest.
        }

        if page_token:  # Checks whether Alpaca supplied another pagination page.
            params["page_token"] = page_token  # Adds that token to the next request.

        response = _alpaca_get(  # Reuses the project's central authenticated request function.
            _data_base_url(),  # Calls Alpaca's market-data API.
            (
                "/v2/stocks/"  # Historical stock-data endpoint.
                + quote(symbol, safe="")  # URL-encodes the ticker.
                + "/bars"  # Selects historical OHLCV bars.
            ),
            params=params,  # Sends the query parameters.
        )

        if not isinstance(response, dict):  # Confirms Alpaca returned the expected JSON structure.
            raise AlpacaServiceError(
                (
                    "Alpaca returned an unexpected "
                    "historical-bars response."
                )
            )

        raw_bars = response.get("bars") or []  # Reads the bar array or falls back to an empty list.

        for raw_bar in raw_bars:  # Loops through every bar in this API page.
            bar = _normalise_bar(  # Converts compact Alpaca fields to MarketPulse field names.
                raw_bar,
                symbol=symbol,
            )

            if not bar:  # Checks whether normalisation failed.
                continue  # Skips invalid bars.

            bar["provider"] = "Alpaca"  # Adds data provenance.
            bar["feed"] = feed  # Records which Alpaca feed supplied the data.
            bar["timeframe"] = timeframe  # Records the requested interval.
            all_bars.append(bar)  # Adds the completed bar to the output list.

        page_token = response.get("next_page_token")  # Reads Alpaca's optional next-page token.

        if not page_token:  # Checks whether pagination has finished.
            break  # Exits the while loop.

    return all_bars  # Returns the complete historical dataset.

# ============================================================
# 23. MARKET CONDITION HISTORY
# ============================================================

def get_market_condition_history(
    symbol,  # Asset that Market Condition should analyse.
    minimum_observations=60,  # Minimum historical observations required by the analytical model.
    initial_calendar_days=120,  # First Alpaca history window that will be tried.
    maximum_calendar_days=730,  # Maximum expansion allowed when more history is needed.
    include_snapshot=True,  # Controls whether current Alpaca context should also be retrieved.
):
    """
    ============================================================
    GET DATA REQUIRED FOR MARKET CONDITION ANALYSIS
    ============================================================

    PURPOSE:

    Retrieve enough recent Alpaca daily history for
    MarketPulse's Market Condition / Market Regime analysis.

    IMPORTANT:

    This function does NOT contain another implementation of
    the Alpaca historical-bars API.

    It deliberately reuses:

        get_historical_bars()

    Therefore:

        Market Condition
            ↓
        get_market_condition_history()
            ↓
        get_historical_bars()
            ↓
        _alpaca_get()
            ↓
        Alpaca


    WHY 60 OBSERVATIONS?

    analysis_tools.analyzers.identify_market_regime()
    currently calculates:

        - 20-period moving average
        - 60-period moving average
        - annualised historical volatility
        - trend strength

    Therefore at least 60 historical observations are required
    before the classification can be calculated consistently.


    HISTORICAL VS CURRENT DATA:

    Historical daily bars
        ↓
    Used for actual Market Condition classification.

    Current Alpaca snapshot
        ↓
    Used only as supplementary current-market context.

    A single current quote must not replace the historical
    series used by the analysis.


    ADAPTIVE HISTORY WINDOW:

    US equity markets do not trade every calendar day.

    Therefore 60 observations normally require considerably
    more than 60 calendar days.

    MarketPulse begins with approximately 120 calendar days.

    If that does not provide enough observations, the helper
    progressively expands the historical window up to the
    configured maximum.


    RETURNS:

    {
        "symbol": "SPY",
        "provider": "Alpaca",
        "feed": "IEX",
        "timeframe": "1Day",
        "minimum_observations": 60,
        "count": 83,
        "has_minimum_history": True,
        "bars": [...],
        "snapshot": {...},
        "latest_price": 123.45,
        ...
    }

    The calling business-logic layer can then persist
    the returned bars into core.MarketData before calling:

        identify_market_regime(symbol)
    ============================================================
    """

    # ========================================================
    # 23.1 NORMALISE SYMBOL
    # ========================================================

    symbol = symbol or ""  # Converts a missing symbol into an empty value.
    symbol = str(symbol).strip().upper()  # Standardises ticker format.

    if not symbol:  # Requires a ticker for the analysis.
        raise AlpacaServiceError(
            (
                "A symbol is required for Market Condition "
                "data retrieval."
            )
        )

    # ========================================================
    # 23.2 NORMALISE MINIMUM OBSERVATION COUNT
    # ========================================================

    try:  # Attempts integer conversion.
        minimum_observations = int(minimum_observations)  # Converts the parameter to an integer.
    except (TypeError, ValueError):  # Handles invalid input.
        minimum_observations = 60  # Restores the analytical default.

    minimum_observations = max(  # Makes sure the analyser always has at least 60 observations.
        60,
        minimum_observations,
    )

    # ========================================================
    # 23.3 NORMALISE INITIAL WINDOW
    # ========================================================

    try:  # Attempts to convert calendar-window configuration.
        initial_calendar_days = int(initial_calendar_days)
    except (TypeError, ValueError):  # Handles invalid input.
        initial_calendar_days = 120  # Uses the default.

    initial_calendar_days = max(  # Ensures enough calendar time exists for non-trading days.
        initial_calendar_days,
        minimum_observations * 2,  # Arithmetic multiplies observations by two.
    )

    # ========================================================
    # 23.4 NORMALISE MAXIMUM WINDOW
    # ========================================================

    try:  # Attempts integer conversion.
        maximum_calendar_days = int(maximum_calendar_days)
    except (TypeError, ValueError):  # Handles invalid values.
        maximum_calendar_days = 730  # Uses approximately two years as the fallback maximum.

    maximum_calendar_days = max(  # Makes sure maximum is never smaller than the initial window.
        initial_calendar_days,
        maximum_calendar_days,
    )

    # ========================================================
    # 23.5 DATE RANGE
    # ========================================================

    end_value = (  # Creates the upper date boundary.
        timezone.localdate()  # Gets today's local date using Django timezone configuration.
        + timedelta(days=1)  # Adds one day so the newest available daily bar can be included.
    )

    # ========================================================
    # 23.6 BUILD PROGRESSIVE SEARCH WINDOWS
    # ========================================================

    history_windows = []  # Creates a list of calendar ranges that may be tried.
    current_window = initial_calendar_days  # Starts with the configured initial range.

    while True:  # Builds progressively larger windows.
        history_windows.append(current_window)  # Adds the current range to the list.

        if current_window >= maximum_calendar_days:  # Stops when the maximum allowed range is reached.
            break

        expanded_window = max(  # Calculates the next larger date range.
            current_window + 60,  # Adds at least 60 calendar days.
            int(current_window * 1.75),  # Or expands the current window by 75%.
        )

        current_window = min(  # Prevents expansion beyond the configured maximum.
            expanded_window,
            maximum_calendar_days,
        )

    # ========================================================
    # 23.7 FETCH HISTORICAL BARS
    # ========================================================

    selected_bars = []  # Will eventually contain the best historical dataset.
    selected_start = None  # Will record the start date used.
    calendar_days_used = None  # Will record how wide a window was required.

    for calendar_days in history_windows:  # Tries each progressively larger date range.
        start_value = (  # Calculates the beginning date for this request.
            end_value
            - timedelta(days=calendar_days)
        )

        bars = get_historical_bars(  # IMPORTANT: reuses the central historical Alpaca implementation.
            symbol=symbol,  # Sends the selected ticker.
            start_date=start_value,  # Sends the calculated beginning date.
            end_date=end_value,  # Sends the upper date boundary.
            timeframe="1Day",  # Market Condition uses daily historical observations.
            adjustment="raw",  # Requests raw Alpaca OHLCV values.
        )

        # ====================================================
        # 23.8 CLEAN DAILY BARS
        # ====================================================

        valid_bars = []  # Creates a list containing only analytically usable observations.

        for bar in bars:  # Checks every returned historical bar.
            if not bar.get("date"):  # Rejects observations without a date.
                continue

            if bar.get("open") is None:  # Rejects bars without an opening price.
                continue

            if bar.get("high") is None:  # Rejects bars without a high.
                continue

            if bar.get("low") is None:  # Rejects bars without a low.
                continue

            if bar.get("close") is None:  # Rejects bars without a closing price.
                continue

            valid_bars.append(bar)  # Keeps the valid OHLC observation.

        # ====================================================
        # 23.9 REMOVE DUPLICATE DAILY OBSERVATIONS
        # ====================================================

        bars_by_date = {}  # Uses a dictionary because each date should appear only once.

        for bar in valid_bars:  # Loops through validated observations.
            bars_by_date[bar["date"]] = bar  # Dictionary assignment replaces a duplicate date automatically.

        valid_bars = [  # Uses a list comprehension to rebuild data in chronological order.
            bars_by_date[bar_date]  # Retrieves the observation for each date.
            for bar_date in sorted(bars_by_date)  # sorted() orders the dictionary's date keys.
        ]

        selected_bars = valid_bars  # Stores the latest attempted historical dataset.
        selected_start = start_value  # Stores the range's starting date.
        calendar_days_used = calendar_days  # Stores how much calendar history was required.

        if len(selected_bars) >= minimum_observations:  # Checks whether enough trading observations now exist.
            break  # Stops requesting progressively older history.

    # ========================================================
    # 23.10 CURRENT / LIVE SNAPSHOT
    # ========================================================

    snapshot = None  # Starts without current Alpaca data.
    snapshot_error = None  # Starts without a snapshot error.

    if include_snapshot:  # Checks the Boolean function argument.
        try:  # Snapshot problems should not invalidate historical analysis data.
            snapshot = get_stock_snapshot(symbol)  # Reuses the current-market snapshot helper.
        except AlpacaServiceError as exc:  # Handles only controlled Alpaca service failures.
            snapshot_error = str(exc)  # Converts the exception into displayable text.

    # ========================================================
    # 23.11 RESULT STATUS
    # ========================================================

    observation_count = len(selected_bars)  # len() counts usable historical observations.

    has_minimum_history = (  # Creates a Boolean readiness flag.
        observation_count >= minimum_observations
    )

    latest_bar = (  # Gets the final observation when history exists.
        selected_bars[-1]  # Negative list index selects the final item.
        if selected_bars
        else None
    )

    earliest_bar = (  # Gets the first observation when history exists.
        selected_bars[0]
        if selected_bars
        else None
    )

    latest_price = None  # Starts without current-price context.

    if snapshot:  # Uses current Alpaca data when a snapshot was retrieved.
        latest_price = snapshot.get("latest_price")  # Reads the most recent trade price.

    if latest_price is None and latest_bar:  # Provides historical fallback context.
        latest_price = latest_bar.get("close")  # Uses the latest available historical close.

    # ========================================================
    # 23.12 USER-FRIENDLY MESSAGE
    # ========================================================

    if has_minimum_history:  # Builds the success message.
        message = (
            f"{observation_count} daily Alpaca observations "
            f"are available for {symbol}. "
            "The dataset is ready for Market Condition "
            "analysis."
        )
    elif observation_count:  # Handles some data existing but not enough.
        message = (
            f"Alpaca returned {observation_count} daily "
            f"observations for {symbol}. "
            f"At least {minimum_observations} observations "
            "are required for Market Condition analysis."
        )
    else:  # Handles no usable history.
        message = (
            f"Alpaca returned no usable daily historical "
            f"observations for {symbol}."
        )

    # ========================================================
    # 23.13 RETURN MARKET CONDITION DATA PACKAGE
    # ========================================================

    return {  # Returns one dictionary containing everything required by the calling layer.
        "symbol": symbol,  # Selected ticker.

        # ----------------------------------------------------
        # Provenance
        # ----------------------------------------------------

        "provider": "Alpaca",  # Records the external provider.
        "feed": _data_feed().upper(),  # Records the configured Alpaca feed in display format.
        "timeframe": "1Day",  # Records that the analytical observations are daily bars.

        # ----------------------------------------------------
        # Analytical requirement
        # ----------------------------------------------------

        "minimum_observations": minimum_observations,  # Number of bars required by the Market Regime model.
        "count": observation_count,  # Number of valid observations obtained.
        "has_minimum_history": has_minimum_history,  # Boolean indicating analysis readiness.

        # ----------------------------------------------------
        # Requested historical window
        # ----------------------------------------------------

        "calendar_days_used": calendar_days_used,  # Number of calendar days requested from Alpaca.
        "requested_start": (  # Stores the request's beginning date in serialisable text format.
            selected_start.isoformat()
            if selected_start
            else None
        ),
        "requested_end": end_value.isoformat(),  # Stores the upper request date.

        # ----------------------------------------------------
        # Actual historical coverage
        # ----------------------------------------------------

        "earliest_date": (  # Reads the first actual market observation.
            earliest_bar.get("date")
            if earliest_bar
            else None
        ),
        "latest_date": (  # Reads the latest actual historical observation.
            latest_bar.get("date")
            if latest_bar
            else None
        ),

        # ----------------------------------------------------
        # Current/latest Alpaca market context
        # ----------------------------------------------------

        "latest_price": latest_price,  # Current trade or fallback latest historical close.
        "snapshot": snapshot,  # Complete current-market snapshot dictionary.
        "snapshot_error": snapshot_error,  # Friendly snapshot error when current data failed.

        # ----------------------------------------------------
        # Historical observations used by importing layer
        # ----------------------------------------------------

        "bars": selected_bars,  # Historical OHLCV observations used by the next business-logic layer.

        # ----------------------------------------------------
        # Display status
        # ----------------------------------------------------

        "message": message,  # User-friendly explanation of data readiness.
    }

# ============================================================
# 24. GET US MARKET CLOCK
# ============================================================

def get_market_clock():  # Retrieves the current US market open/closed state from Alpaca.
    """
    ------------------------------------------------------------
    GET US MARKET CLOCK
    ------------------------------------------------------------

    Returns:

    - current Alpaca market timestamp
    - whether the US market is open
    - next market open
    - next market close

    Useful for the live Dashboard header.
    ------------------------------------------------------------
    """

    cache_key = "marketpulse_alpaca_market_clock"  # Creates the cache identifier.
    cached_clock = cache.get(cache_key)  # Checks for a recently retrieved market clock.

    if cached_clock is not None:  # Reuses cached data when it exists.
        return cached_clock  # Avoids another API request.

    response = _alpaca_get(  # Uses the shared authenticated HTTP function.
        _trading_base_url(),  # Market clock belongs to Alpaca's trading API.
        "/v2/clock",  # Alpaca market-clock endpoint.
    )

    if not isinstance(response, dict):  # Confirms the expected JSON object.
        raise AlpacaServiceError(
            (
                "Alpaca returned an unexpected market "
                "clock response."
            )
        )

    market_clock = {  # Builds a smaller predictable MarketPulse dictionary.
        "timestamp": response.get("timestamp"),  # Current Alpaca market timestamp.
        "is_open": bool(response.get("is_open", False)),  # Boolean saying whether the market is currently open.
        "next_open": response.get("next_open"),  # Next scheduled market opening.
        "next_close": response.get("next_close"),  # Next scheduled market closing.
    }

    cache.set(  # Caches the market clock briefly.
        cache_key,
        market_clock,
        30,
    )

    return market_clock  # Returns the market-clock information.

# ============================================================
# 25. DASHBOARD MARKET OVERVIEW
# ============================================================

def get_dashboard_market_overview(symbols=None):  # Builds the benchmark-market summary shown by the Dashboard.
    """
    ------------------------------------------------------------
    BUILD DASHBOARD MARKET OVERVIEW
    ------------------------------------------------------------

    Default benchmarks:

        SPY
            Broad large-cap US equities

        QQQ
            Nasdaq-100 / technology-heavy equities

        DIA
            Dow Jones large-cap equities

        IWM
            US small-cap equities
    ------------------------------------------------------------
    """

    if symbols is None:  # Uses default benchmark ETFs when the caller supplies nothing.
        symbols = [
            "SPY",  # S&P 500 ETF.
            "QQQ",  # Nasdaq-100 ETF.
            "DIA",  # Dow Jones ETF.
            "IWM",  # Russell 2000 ETF.
        ]

    snapshots = get_stock_snapshots(symbols)  # Retrieves all benchmark snapshots efficiently.

    benchmark_names = {  # Maps ticker symbols to user-friendly names.
        "SPY": "S&P 500 ETF",
        "QQQ": "Nasdaq-100 ETF",
        "DIA": "Dow Jones ETF",
        "IWM": "Russell 2000 ETF",
    }

    benchmarks = []  # Creates the final Dashboard benchmark list.

    for symbol in symbols:  # Processes each requested benchmark.
        symbol = str(symbol).strip().upper()  # Standardises the ticker.
        snapshot = snapshots.get(symbol)  # Retrieves that ticker's snapshot.

        if not snapshot:  # Handles a benchmark that Alpaca did not return.
            benchmarks.append(
                {
                    "symbol": symbol,  # Requested ticker.
                    "name": benchmark_names.get(symbol, symbol),  # Friendly label with ticker fallback.
                    "available": False,  # Marks current data as unavailable.
                    "latest_price": None,  # No current price.
                    "previous_close": None,  # No previous close.
                    "change": None,  # No daily absolute change.
                    "change_pct": None,  # No daily percentage change.
                    "day_open": None,  # No current-day open.
                    "day_high": None,  # No current-day high.
                    "day_low": None,  # No current-day low.
                    "day_volume": None,  # No current-day volume.
                }
            )
            continue  # Moves directly to the next ticker.

        daily_bar = snapshot.get("daily_bar") or {}  # Retrieves the current daily OHLCV bar.

        benchmarks.append(  # Adds the successfully retrieved benchmark to the output.
            {
                "symbol": symbol,  # Ticker.
                "name": benchmark_names.get(symbol, symbol),  # User-friendly benchmark name.
                "available": True,  # Shows that live information is available.
                "latest_price": snapshot.get("latest_price"),  # Current trade price.
                "previous_close": snapshot.get("previous_close"),  # Previous session close.
                "change": snapshot.get("daily_change"),  # Absolute daily movement.
                "change_pct": snapshot.get("daily_change_pct"),  # Percentage daily movement.
                "day_open": daily_bar.get("open"),  # Current session opening value.
                "day_high": daily_bar.get("high"),  # Current session high.
                "day_low": daily_bar.get("low"),  # Current session low.
                "day_volume": daily_bar.get("volume"),  # Current session volume.
            }
        )

    try:  # Market overview can still be returned if the clock endpoint fails.
        market_clock = get_market_clock()  # Retrieves current exchange clock information.
    except AlpacaServiceError:  # Handles a controlled market-clock failure.
        market_clock = {  # Supplies a safe fallback structure.
            "timestamp": None,
            "is_open": False,
            "next_open": None,
            "next_close": None,
        }

    return {  # Returns the Dashboard market-overview package.
        "provider": "Alpaca",  # Market-data source.
        "feed": _data_feed().upper(),  # Configured feed.
        "market_clock": market_clock,  # US market clock information.
        "benchmarks": benchmarks,  # Benchmark ETF data.
        "updated_at": timezone.now().isoformat(),  # Timestamp showing when MarketPulse built this response.
    }

# ============================================================
# 26. DASHBOARD CHART HISTORY
# ============================================================

def get_chart_history(symbol="SPY", period="1M"):  # Retrieves historical Alpaca data formatted for Dashboard charts.
    """
    ============================================================
    MARKETPULSE - DASHBOARD CHART HISTORY
    ============================================================

    Framework mapping:

    Dashboard
        ↓
    API dashboard market overview
        ↓
    get_chart_history()
        ↓
    get_historical_bars()
        ↓
    Alpaca Historical Market Data API
        ↓
    Normalised OHLCV observations
        ↓
    Chart.js


    PURPOSE:

    Retrieve a useful historical price series for the
    Dashboard graph.

    IMPORTANT:

    30 calendar days are NOT the same as 30 trading sessions.

    Weekends and exchange holidays contain no daily bars.

    Therefore MarketPulse requests a wider calendar window and
    then keeps the latest required number of actual trading
    observations.
    ============================================================
    """

    # ========================================================
    # 26.1 NORMALISE SYMBOL
    # ========================================================

    symbol = symbol or "SPY"  # Uses SPY when no ticker is supplied.
    symbol = str(symbol).strip().upper()  # Standardises the ticker.

    if not symbol:  # Handles a string containing only whitespace.
        symbol = "SPY"  # Restores the default benchmark.

    # ========================================================
    # 26.2 NORMALISE PERIOD
    # ========================================================

    period = period or "1M"  # Uses one month as the default chart period.
    period = str(period).strip().upper()  # Standardises the period code.

    # ========================================================
    # 26.3 PERIOD CONFIGURATION
    # ========================================================

    period_config = {  # Creates a nested dictionary describing each supported chart range.
        "1D": {
            "calendar_days": 7,  # Requests several calendar days to find enough recent trading data.
            "timeframe": "5Min",  # Uses five-minute bars.
            "max_points": 120,  # Limits how many chart points are returned.
            "date_only": False,  # Intraday queries use full datetimes.
        },
        "5D": {
            "calendar_days": 14,  # Uses a wider range to account for weekends.
            "timeframe": "30Min",  # Uses 30-minute bars.
            "max_points": 100,  # Limits chart density.
            "date_only": False,  # Requires datetime values.
        },
        "1M": {
            "calendar_days": 60,  # Requests 60 calendar days to get about 30 trading sessions.
            "timeframe": "1Day",  # Uses daily bars.
            "max_points": 30,  # Keeps the most recent 30 trading observations.
            "date_only": True,  # Daily bars need only dates.
        },
        "3M": {
            "calendar_days": 140,  # Requests enough calendar history for roughly three trading months.
            "timeframe": "1Day",  # Uses daily observations.
            "max_points": 70,  # Keeps approximately 70 trading sessions.
            "date_only": True,  # Uses date boundaries.
        },
    }

    config = period_config.get(period)  # Retrieves configuration for the selected period.

    if config is None:  # Detects an unsupported period.
        raise AlpacaServiceError(
            (
                "Unsupported chart period. "
                "Use 1D, 5D, 1M or 3M."
            )
        )

    # ========================================================
    # 26.4 BUILD ALPACA DATE RANGE
    # ========================================================

    if config["date_only"]:  # Uses date objects for daily history.
        end_value = (  # Builds an inclusive upper boundary.
            timezone.localdate()
            + timedelta(days=1)
        )

        start_value = (  # Calculates the requested starting date.
            end_value
            - timedelta(days=config["calendar_days"])
        )
    else:  # Intraday history needs full timezone-aware datetimes.
        end_value = timezone.now()  # Uses the current Django-aware datetime.
        start_value = (  # Subtracts the configured calendar window.
            end_value
            - timedelta(days=config["calendar_days"])
        )

    # ========================================================
    # 26.5 REQUEST HISTORICAL BARS FROM ALPACA
    # ========================================================

    bars = get_historical_bars(  # Reuses the same central historical-data service as imports and analysis.
        symbol=symbol,
        start_date=start_value,
        end_date=end_value,
        timeframe=config["timeframe"],
        adjustment="raw",
    )

    # ========================================================
    # 26.6 KEEP LATEST REQUIRED OBSERVATIONS
    # ========================================================

    max_points = config["max_points"]  # Reads the maximum chart size.

    if max_points and len(bars) > max_points:  # Checks whether the returned series is too large.
        bars = bars[-max_points:]  # Uses negative slicing to keep only the most recent points.

    # ========================================================
    # 26.7 BUILD CHART POINTS
    # ========================================================

    chart_points = []  # Creates the final list that the frontend chart consumes.

    for bar in bars:  # Processes each normalised historical bar.
        timestamp = bar.get("timestamp")  # Retrieves its timestamp.
        close_price = bar.get("close")  # Retrieves its closing price.

        if not timestamp:  # Chart points require a horizontal-axis value.
            continue  # Skips a bar with no timestamp.

        if close_price is None:  # Chart points require a numerical price.
            continue  # Skips a bar with no close value.

        chart_points.append(  # Adds a frontend-friendly price observation.
            {
                "timestamp": timestamp,  # Full Alpaca timestamp.
                "date": bar.get("date"),  # Simplified date.
                "open": bar.get("open"),  # Opening price.
                "high": bar.get("high"),  # Highest price.
                "low": bar.get("low"),  # Lowest price.
                "close": close_price,  # Closing price.
                "volume": bar.get("volume"),  # Trading volume.
            }
        )

    # ========================================================
    # 26.8 STATUS MESSAGE
    # ========================================================

    if chart_points:  # Builds a success message when usable price observations exist.
        message = (
            f"{len(chart_points)} historical "
            f"{config['timeframe']} bars were returned "
            f"from Alpaca."
        )
    else:  # Builds an explanatory message when Alpaca provided no usable chart points.
        message = (
            "Alpaca returned no historical bars "
            f"for {symbol} using the "
            f"{_data_feed().upper()} feed."
        )

    # ========================================================
    # 26.9 RETURN DASHBOARD DATA
    # ========================================================

    return {  # Returns the historical chart package.
        "symbol": symbol,  # Asset displayed by the chart.
        "period": period,  # Selected user period.
        "timeframe": config["timeframe"],  # Alpaca bar interval.
        "provider": "Alpaca",  # External provider.
        "feed": _data_feed().upper(),  # Alpaca feed.
        "requested_start": (  # Serialises the beginning of the requested period.
            start_value.isoformat()
            if hasattr(start_value, "isoformat")
            else str(start_value)
        ),
        "requested_end": (  # Serialises the end of the requested period.
            end_value.isoformat()
            if hasattr(end_value, "isoformat")
            else str(end_value)
        ),
        "points": chart_points,  # Actual OHLCV points sent to the frontend.
        "count": len(chart_points),  # Number of usable points.
        "has_data": bool(chart_points),  # Converts list existence into True/False.
        "message": message,  # Human-readable API status.
    }

# ============================================================
# 27. TEST ALPACA CONNECTION
# ============================================================

def test_alpaca_connection():  # Provides a safe backend health check for Alpaca configuration.
    """
    ------------------------------------------------------------
    TEST ALPACA CONFIGURATION AND CONNECTION
    ------------------------------------------------------------

    This helper deliberately does not expose API credentials.

    It confirms only whether MarketPulse can authenticate
    successfully and retrieve Alpaca market-clock information.
    ------------------------------------------------------------
    """

    try:  # Attempts a real authenticated request.
        market_clock = get_market_clock()  # Reuses the market-clock service as the connection test.

        return {  # Returns a success dictionary.
            "success": True,  # Boolean indicates the connection worked.
            "provider": "Alpaca",  # Identifies the tested provider.
            "feed": _data_feed().upper(),  # Shows which data feed MarketPulse is configured to use.
            "market_open": market_clock.get("is_open"),  # Includes useful but non-sensitive status.
            "message": (
                "MarketPulse connected successfully "
                "to Alpaca."
            ),
        }

    except AlpacaServiceError as exc:  # Catches only controlled Alpaca service failures.
        return {  # Returns a safe failure dictionary rather than exposing credentials.
            "success": False,  # Indicates connection/configuration failure.
            "provider": "Alpaca",  # Identifies which provider failed.
            "feed": None,  # Feed is unavailable when configuration fails.
            "market_open": None,  # Market status could not be determined.
            "message": str(exc),  # Converts the friendly custom exception to text.
        }