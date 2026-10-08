"""
============================================================
MARKETPULSE - ALPACA MARKET DATA SERVICE
============================================================

PURPOSE:

This module provides one central service layer between
MarketPulse and Alpaca.

The rest of the application should NOT communicate with
Alpaca directly.

Instead:

Browser / React / Django Views
        ↓
MarketPulse API / Business Logic
        ↓
data_management.services.alpaca
        ↓
Alpaca API
        ↓
Normalised Python dictionaries
        ↓
PostgreSQL / MarketPulse Interface


MAIN RESPONSIBILITIES:

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


IMPORTANT MARKET CONDITION ARCHITECTURE:

Market Condition does NOT implement a second Alpaca client.

Instead:

get_market_condition_history()
        ↓
get_historical_bars()
        ↓
Alpaca Historical Bars API


This keeps one reusable historical-data implementation.

Market Condition requires historical observations because
classification depends on:

- recent price direction
- moving averages
- historical volatility
- trend strength

A single live price cannot provide these measurements.

For current/latest context, the Market Condition helper can
also retrieve:

get_stock_snapshot()
        ↓
latest trade / quote / daily bar


The snapshot is supplementary market context.

The historical daily bars remain the reproducible input used
by MarketPulse's Market Regime analysis.


SECURITY:

The browser NEVER receives:

- ALPACA_API_KEY_ID
- ALPACA_API_SECRET_KEY

Credentials remain inside Django settings and private
environment variables.

============================================================
"""


# ============================================================
# 1. STANDARD LIBRARY IMPORTS
# ============================================================

from datetime import timedelta

from urllib.parse import quote


# ============================================================
# 2. THIRD-PARTY IMPORTS
# ============================================================

import requests


# ============================================================
# 3. DJANGO IMPORTS
# ============================================================

from django.conf import settings

from django.core.cache import cache

from django.utils import timezone


# ============================================================
# 4. CUSTOM EXCEPTION
# ============================================================


class AlpacaServiceError(Exception):
    """
    Raised when MarketPulse cannot successfully communicate
    with Alpaca or when the Alpaca configuration is invalid.

    Views and business-logic functions can catch this exception
    and display a friendly message instead of exposing raw
    external API errors.
    """

    pass


# ============================================================
# 5. SUPPORTED MARKET-DATA FEEDS
# ============================================================

ALLOWED_DATA_FEEDS = {
    "iex",
    "sip",
    "delayed_sip",
    "boats",
    "overnight",
    "otc",
}


# ============================================================
# 6. CONFIGURATION HELPERS
# ============================================================


def _normalise_base_url(url):
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

    if not url:
        return ""

    cleaned_url = (
        str(url)
        .strip()
        .rstrip("/")
    )

    for ending in (
        "/v2",
        "/v3",
    ):

        if cleaned_url.endswith(
            ending
        ):

            cleaned_url = (
                cleaned_url[
                    :-len(ending)
                ]
            )

    return cleaned_url.rstrip("/")


# ============================================================
# 7. TRADING API BASE URL
# ============================================================


def _trading_base_url():
    """
    Return the configured Alpaca Trading API base URL.
    """

    url = _normalise_base_url(
        getattr(
            settings,
            "ALPACA_TRADING_BASE_URL",
            "https://paper-api.alpaca.markets",
        )
    )

    if not url:

        raise AlpacaServiceError(
            "ALPACA_TRADING_BASE_URL is not configured."
        )

    return url


# ============================================================
# 8. MARKET DATA API BASE URL
# ============================================================


def _data_base_url():
    """
    Return the configured Alpaca Market Data API base URL.
    """

    url = _normalise_base_url(
        getattr(
            settings,
            "ALPACA_DATA_BASE_URL",
            "https://data.alpaca.markets",
        )
    )

    if not url:

        raise AlpacaServiceError(
            "ALPACA_DATA_BASE_URL is not configured."
        )

    return url


# ============================================================
# 9. MARKET DATA FEED
# ============================================================


def _data_feed():
    """
    Return the configured stock market-data feed.

    MarketPulse currently normally uses:

        iex
    """

    feed = (
        getattr(
            settings,
            "ALPACA_DATA_FEED",
            "iex",
        )
        or
        "iex"
    )

    feed = (
        str(feed)
        .strip()
        .lower()
    )

    if feed not in ALLOWED_DATA_FEEDS:

        raise AlpacaServiceError(
            (
                "Invalid ALPACA_DATA_FEED configuration: "
                f"{feed}"
            )
        )

    return feed


# ============================================================
# 10. REQUEST TIMEOUT
# ============================================================


def _request_timeout():
    """
    Return the maximum number of seconds an Alpaca HTTP
    request should wait before failing.
    """

    try:

        timeout = int(
            getattr(
                settings,
                "ALPACA_REQUEST_TIMEOUT",
                8,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        timeout = 8

    return max(
        1,
        timeout,
    )


# ============================================================
# 11. ALPACA AUTHENTICATION HEADERS
# ============================================================


def _alpaca_headers():
    """
    ------------------------------------------------------------
    BUILD ALPACA AUTHENTICATION HEADERS
    ------------------------------------------------------------

    Credentials are read from Django settings.

    They should originate from private environment variables,
    not from source code.
    ------------------------------------------------------------
    """

    api_key = (
        getattr(
            settings,
            "ALPACA_API_KEY_ID",
            "",
        )
        or
        ""
    )

    secret_key = (
        getattr(
            settings,
            "ALPACA_API_SECRET_KEY",
            "",
        )
        or
        ""
    )

    api_key = (
        str(api_key)
        .strip()
    )

    secret_key = (
        str(secret_key)
        .strip()
    )

    if not api_key:

        raise AlpacaServiceError(
            "ALPACA_API_KEY_ID is not configured."
        )

    if not secret_key:

        raise AlpacaServiceError(
            "ALPACA_API_SECRET_KEY is not configured."
        )

    return {

        "APCA-API-KEY-ID":
            api_key,

        "APCA-API-SECRET-KEY":
            secret_key,

        "Accept":
            "application/json",
    }


# ============================================================
# 12. GENERIC ALPACA GET REQUEST
# ============================================================


def _alpaca_get(
    base_url,
    path,
    params=None,
):
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

    url = (
        base_url.rstrip("/")
        +
        "/"
        +
        path.lstrip("/")
    )

    try:

        response = requests.get(
            url,
            headers=_alpaca_headers(),
            params=params or {},
            timeout=_request_timeout(),
        )

    except requests.Timeout as exc:

        raise AlpacaServiceError(
            (
                "The Alpaca request timed out. "
                "Please try again."
            )
        ) from exc

    except requests.ConnectionError as exc:

        raise AlpacaServiceError(
            (
                "MarketPulse could not connect to Alpaca. "
                "Check the internet connection and try again."
            )
        ) from exc

    except requests.RequestException as exc:

        raise AlpacaServiceError(
            (
                "An unexpected network error occurred while "
                "communicating with Alpaca."
            )
        ) from exc


    # ========================================================
    # HTTP ERROR HANDLING
    # ========================================================

    if not response.ok:

        message = ""

        try:

            error_data = (
                response.json()
                or
                {}
            )

            if isinstance(
                error_data,
                dict,
            ):

                message = (
                    error_data.get(
                        "message"
                    )
                    or
                    error_data.get(
                        "error"
                    )
                    or
                    ""
                )

        except ValueError:

            message = ""

        if response.status_code == 401:

            friendly_message = (
                "Alpaca authentication failed. "
                "Check the configured API credentials."
            )

        elif response.status_code == 403:

            friendly_message = (
                "Alpaca rejected this request because the "
                "account is not entitled to the requested "
                "market-data resource or feed."
            )

        elif response.status_code == 404:

            friendly_message = (
                "The requested Alpaca resource was not found."
            )

        elif response.status_code == 429:

            friendly_message = (
                "The Alpaca API rate limit was reached. "
                "Please wait briefly and try again."
            )

        elif response.status_code >= 500:

            friendly_message = (
                "Alpaca is temporarily unavailable. "
                "Please try again later."
            )

        else:

            friendly_message = (
                f"Alpaca returned HTTP "
                f"{response.status_code}."
            )

        if message:

            friendly_message += (
                f" {message}"
            )

        raise AlpacaServiceError(
            friendly_message
        )


    # ========================================================
    # JSON RESPONSE
    # ========================================================

    try:

        return response.json()

    except ValueError as exc:

        raise AlpacaServiceError(
            (
                "Alpaca returned a response that MarketPulse "
                "could not interpret as JSON."
            )
        ) from exc


# ============================================================
# 13. VALUE NORMALISATION HELPERS
# ============================================================


def _to_float(value):
    """
    Convert an API value into a float when possible.
    """

    if value is None:
        return None

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# ============================================================


def _to_int(value):
    """
    Convert an API value into an integer when possible.
    """

    if value is None:
        return None

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# ============================================================
# 14. NORMALISE ALPACA ASSET
# ============================================================


def _normalise_asset(asset):
    """
    Convert Alpaca's raw asset response into a predictable
    MarketPulse dictionary.
    """

    if not isinstance(
        asset,
        dict,
    ):

        return {}

    return {

        "id":
            asset.get(
                "id"
            ),

        "symbol":
            (
                asset.get(
                    "symbol"
                )
                or
                ""
            ).upper(),

        "name":
            (
                asset.get(
                    "name"
                )
                or
                ""
            ),

        "exchange":
            (
                asset.get(
                    "exchange"
                )
                or
                ""
            ),

        "asset_class":
            (
                asset.get(
                    "class"
                )
                or
                asset.get(
                    "asset_class"
                )
                or
                ""
            ),

        "status":
            (
                asset.get(
                    "status"
                )
                or
                ""
            ),

        "tradable":
            bool(
                asset.get(
                    "tradable",
                    False,
                )
            ),

        "marginable":
            bool(
                asset.get(
                    "marginable",
                    False,
                )
            ),

        "shortable":
            bool(
                asset.get(
                    "shortable",
                    False,
                )
            ),

        "fractionable":
            bool(
                asset.get(
                    "fractionable",
                    False,
                )
            ),

        "borrow_status":
            (
                asset.get(
                    "borrow_status"
                )
                or
                ""
            ),
    }


# ============================================================
# 15. NORMALISE ALPACA BAR
# ============================================================


def _normalise_bar(
    bar,
    symbol=None,
):
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

    if not isinstance(
        bar,
        dict,
    ):

        return None

    timestamp = (
        bar.get(
            "t"
        )
        or
        bar.get(
            "timestamp"
        )
    )

    date_value = None

    if timestamp:

        date_value = (
            str(
                timestamp
            )[:10]
        )

    return {

        "symbol":
            (
                symbol.upper()
                if symbol
                else None
            ),

        "timestamp":
            timestamp,

        "date":
            date_value,

        "open":
            _to_float(
                bar.get(
                    "o"
                )
                if "o" in bar
                else bar.get(
                    "open"
                )
            ),

        "high":
            _to_float(
                bar.get(
                    "h"
                )
                if "h" in bar
                else bar.get(
                    "high"
                )
            ),

        "low":
            _to_float(
                bar.get(
                    "l"
                )
                if "l" in bar
                else bar.get(
                    "low"
                )
            ),

        "close":
            _to_float(
                bar.get(
                    "c"
                )
                if "c" in bar
                else bar.get(
                    "close"
                )
            ),

        "volume":
            _to_int(
                bar.get(
                    "v"
                )
                if "v" in bar
                else bar.get(
                    "volume"
                )
            ),

        "trade_count":
            _to_int(
                bar.get(
                    "n"
                )
                if "n" in bar
                else bar.get(
                    "trade_count"
                )
            ),

        "vwap":
            _to_float(
                bar.get(
                    "vw"
                )
                if "vw" in bar
                else bar.get(
                    "vwap"
                )
            ),
    }


# ============================================================
# 16. NORMALISE ALPACA SNAPSHOT
# ============================================================


def _normalise_snapshot(
    raw_snapshot,
    feed=None,
):
    """
    Convert the Alpaca snapshot response into data that the
    Dashboard, Risk and Data tab can consume consistently.
    """

    if not isinstance(
        raw_snapshot,
        dict,
    ):

        raw_snapshot = {}

    latest_trade = (
        raw_snapshot.get(
            "latestTrade"
        )
        or
        raw_snapshot.get(
            "latest_trade"
        )
        or
        {}
    )

    latest_quote = (
        raw_snapshot.get(
            "latestQuote"
        )
        or
        raw_snapshot.get(
            "latest_quote"
        )
        or
        {}
    )

    minute_bar_raw = (
        raw_snapshot.get(
            "minuteBar"
        )
        or
        raw_snapshot.get(
            "minute_bar"
        )
        or
        {}
    )

    daily_bar_raw = (
        raw_snapshot.get(
            "dailyBar"
        )
        or
        raw_snapshot.get(
            "daily_bar"
        )
        or
        {}
    )

    previous_daily_bar_raw = (
        raw_snapshot.get(
            "prevDailyBar"
        )
        or
        raw_snapshot.get(
            "previous_daily_bar"
        )
        or
        {}
    )

    latest_price = _to_float(
        latest_trade.get(
            "p"
        )
        if "p" in latest_trade
        else latest_trade.get(
            "price"
        )
    )

    bid_price = _to_float(
        latest_quote.get(
            "bp"
        )
        if "bp" in latest_quote
        else latest_quote.get(
            "bid_price"
        )
    )

    ask_price = _to_float(
        latest_quote.get(
            "ap"
        )
        if "ap" in latest_quote
        else latest_quote.get(
            "ask_price"
        )
    )

    spread = None

    if (
        bid_price is not None
        and
        ask_price is not None
    ):

        spread = (
            ask_price
            -
            bid_price
        )

    daily_bar = (
        _normalise_bar(
            daily_bar_raw
        )
    )

    previous_daily_bar = (
        _normalise_bar(
            previous_daily_bar_raw
        )
    )

    minute_bar = (
        _normalise_bar(
            minute_bar_raw
        )
    )

    previous_close = (
        previous_daily_bar.get(
            "close"
        )
        if previous_daily_bar
        else None
    )

    daily_change = None

    daily_change_pct = None

    if (
        latest_price is not None
        and
        previous_close is not None
        and
        previous_close != 0
    ):

        daily_change = (
            latest_price
            -
            previous_close
        )

        daily_change_pct = (
            daily_change
            /
            previous_close
            *
            100
        )

    return {

        "feed":
            (
                feed
                or
                _data_feed()
            ),

        "latest_price":
            latest_price,

        "latest_trade_timestamp":
            (
                latest_trade.get(
                    "t"
                )
                or
                latest_trade.get(
                    "timestamp"
                )
            ),

        "bid_price":
            bid_price,

        "ask_price":
            ask_price,

        "spread":
            spread,

        "previous_close":
            previous_close,

        "daily_change":
            daily_change,

        "daily_change_pct":
            daily_change_pct,

        "minute_bar":
            minute_bar,

        "daily_bar":
            daily_bar,

        "previous_daily_bar":
            previous_daily_bar,
    }


# ============================================================
# 17. GET ACTIVE US EQUITIES
# ============================================================


def get_active_us_equities():
    """
    ------------------------------------------------------------
    GET ALPACA ACTIVE US EQUITY UNIVERSE
    ------------------------------------------------------------

    The complete universe is cached because downloading the
    full asset list for every search keystroke would be
    inefficient.
    ------------------------------------------------------------
    """

    cache_key = (
        "marketpulse_alpaca_active_us_equities"
    )

    cached_assets = cache.get(
        cache_key
    )

    if cached_assets is not None:

        return cached_assets

    response = _alpaca_get(
        _trading_base_url(),
        "/v2/assets",
        params={
            "status":
                "active",

            "asset_class":
                "us_equity",
        },
    )

    if not isinstance(
        response,
        list,
    ):

        raise AlpacaServiceError(
            (
                "Alpaca returned an unexpected asset "
                "response."
            )
        )

    assets = []

    for raw_asset in response:

        asset = (
            _normalise_asset(
                raw_asset
            )
        )

        if (
            asset
            and
            asset.get(
                "symbol"
            )
        ):

            assets.append(
                asset
            )

    cache_seconds = int(
        getattr(
            settings,
            "ALPACA_ASSET_CACHE_SECONDS",
            1800,
        )
    )

    cache.set(
        cache_key,
        assets,
        cache_seconds,
    )

    return assets


# ============================================================
# 18. SEARCH ALPACA ASSETS
# ============================================================


def search_assets(
    query,
    limit=12,
):
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

    query = (
        query
        or
        ""
    )

    query = (
        str(query)
        .strip()
        .upper()
    )

    if not query:

        return []

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError,
    ):

        limit = 12

    limit = max(
        1,
        min(
            limit,
            50,
        ),
    )

    assets = (
        get_active_us_equities()
    )

    ranked = []

    for asset in assets:

        symbol = (
            asset.get(
                "symbol",
                ""
            )
            .upper()
        )

        name = (
            asset.get(
                "name",
                ""
            )
            .upper()
        )

        score = None

        if symbol == query:

            score = 0

        elif symbol.startswith(
            query
        ):

            score = 1

        elif query in symbol:

            score = 2

        elif name.startswith(
            query
        ):

            score = 3

        elif query in name:

            score = 4

        if score is None:

            continue

        tradable_penalty = (
            0
            if asset.get(
                "tradable"
            )
            else 1
        )

        ranked.append(
            (
                score,
                tradable_penalty,
                len(
                    symbol
                ),
                symbol,
                asset,
            )
        )

    ranked.sort(
        key=lambda row: (
            row[0],
            row[1],
            row[2],
            row[3],
        )
    )

    return [
        row[4]
        for row in ranked[:limit]
    ]


# ============================================================
# 19. GET ONE ALPACA ASSET
# ============================================================


def get_asset(symbol):
    """
    Retrieve metadata for one Alpaca asset.
    """

    symbol = (
        symbol
        or
        ""
    )

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )

    if not symbol:

        raise AlpacaServiceError(
            "A symbol is required."
        )

    cache_key = (
        "marketpulse_alpaca_asset_"
        +
        symbol
    )

    cached_asset = (
        cache.get(
            cache_key
        )
    )

    if cached_asset is not None:

        return cached_asset

    response = _alpaca_get(
        _trading_base_url(),
        (
            "/v2/assets/"
            +
            quote(
                symbol,
                safe="",
            )
        ),
    )

    asset = (
        _normalise_asset(
            response
        )
    )

    if not asset:

        raise AlpacaServiceError(
            (
                f"Alpaca returned no asset information "
                f"for {symbol}."
            )
        )

    cache.set(
        cache_key,
        asset,
        1800,
    )

    return asset


# ============================================================
# 20. GET ONE STOCK SNAPSHOT
# ============================================================


def get_stock_snapshot(
    symbol,
):
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

    symbol = (
        symbol
        or
        ""
    )

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )

    if not symbol:

        raise AlpacaServiceError(
            "A symbol is required."
        )

    feed = (
        _data_feed()
    )

    cache_key = (
        "marketpulse_alpaca_snapshot_"
        +
        feed
        +
        "_"
        +
        symbol
    )

    cached_snapshot = (
        cache.get(
            cache_key
        )
    )

    if cached_snapshot is not None:

        return cached_snapshot

    response = _alpaca_get(
        _data_base_url(),
        (
            "/v2/stocks/"
            +
            quote(
                symbol,
                safe="",
            )
            +
            "/snapshot"
        ),
        params={
            "feed":
                feed,

            "currency":
                "USD",
        },
    )

    snapshot = (
        _normalise_snapshot(
            response,
            feed=feed,
        )
    )

    snapshot[
        "symbol"
    ] = symbol

    cache_seconds = int(
        getattr(
            settings,
            "ALPACA_SNAPSHOT_CACHE_SECONDS",
            15,
        )
    )

    cache.set(
        cache_key,
        snapshot,
        cache_seconds,
    )

    return snapshot


# ============================================================
# 21. GET MULTIPLE STOCK SNAPSHOTS
# ============================================================


def get_stock_snapshots(
    symbols,
):
    """
    ------------------------------------------------------------
    GET MULTIPLE ALPACA STOCK SNAPSHOTS
    ------------------------------------------------------------

    Useful for Dashboard benchmark data because multiple
    symbols can be requested together.
    ------------------------------------------------------------
    """

    if isinstance(
        symbols,
        str,
    ):

        symbols = (
            symbols.split(
                ","
            )
        )

    cleaned_symbols = []

    for symbol in symbols or []:

        symbol = (
            str(symbol)
            .strip()
            .upper()
        )

        if (
            symbol
            and
            symbol not in cleaned_symbols
        ):

            cleaned_symbols.append(
                symbol
            )

    if not cleaned_symbols:

        return {}

    # Prevent accidentally huge requests.

    cleaned_symbols = (
        cleaned_symbols[:50]
    )

    feed = (
        _data_feed()
    )

    response = _alpaca_get(
        _data_base_url(),
        "/v2/stocks/snapshots",
        params={
            "symbols":
                ",".join(
                    cleaned_symbols
                ),

            "feed":
                feed,

            "currency":
                "USD",
        },
    )

    if not isinstance(
        response,
        dict,
    ):

        raise AlpacaServiceError(
            (
                "Alpaca returned an unexpected multi-symbol "
                "snapshot response."
            )
        )

    snapshots = {}

    for symbol in cleaned_symbols:

        raw_snapshot = (
            response.get(
                symbol
            )
            or
            response.get(
                symbol.upper()
            )
        )

        if raw_snapshot is None:

            continue

        snapshot = (
            _normalise_snapshot(
                raw_snapshot,
                feed=feed,
            )
        )

        snapshot[
            "symbol"
        ] = symbol

        snapshots[
            symbol
        ] = snapshot

    return snapshots


# ============================================================
# 22. GET HISTORICAL BARS
# ============================================================


def get_historical_bars(
    symbol,
    start_date,
    end_date,
    timeframe="1Day",
    adjustment="raw",
    limit=10000,
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

    symbol = (
        symbol
        or
        ""
    )

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )

    if not symbol:

        raise AlpacaServiceError(
            "A symbol is required."
        )

    if not start_date:

        raise AlpacaServiceError(
            (
                "A start date is required for "
                "historical data."
            )
        )

    if not end_date:

        raise AlpacaServiceError(
            (
                "An end date is required for "
                "historical data."
            )
        )

    start_value = (
        start_date.isoformat()
        if hasattr(
            start_date,
            "isoformat",
        )
        else str(
            start_date
        )
    )

    end_value = (
        end_date.isoformat()
        if hasattr(
            end_date,
            "isoformat",
        )
        else str(
            end_date
        )
    )

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError,
    ):

        limit = 10000

    limit = max(
        1,
        min(
            limit,
            10000,
        ),
    )

    feed = (
        _data_feed()
    )

    all_bars = []

    page_token = None

    page_count = 0

    max_pages = 100

    while True:

        page_count += 1

        if page_count > max_pages:

            raise AlpacaServiceError(
                (
                    "Historical-data pagination exceeded "
                    "the MarketPulse safety limit."
                )
            )

        params = {

            "timeframe":
                timeframe,

            "start":
                start_value,

            "end":
                end_value,

            "limit":
                limit,

            "adjustment":
                adjustment,

            "feed":
                feed,

            "sort":
                "asc",
        }

        if page_token:

            params[
                "page_token"
            ] = page_token

        response = _alpaca_get(
            _data_base_url(),
            (
                "/v2/stocks/"
                +
                quote(
                    symbol,
                    safe="",
                )
                +
                "/bars"
            ),
            params=params,
        )

        if not isinstance(
            response,
            dict,
        ):

            raise AlpacaServiceError(
                (
                    "Alpaca returned an unexpected "
                    "historical-bars response."
                )
            )

        raw_bars = (
            response.get(
                "bars"
            )
            or
            []
        )

        for raw_bar in raw_bars:

            bar = (
                _normalise_bar(
                    raw_bar,
                    symbol=symbol,
                )
            )

            if not bar:

                continue

            bar[
                "provider"
            ] = "Alpaca"

            bar[
                "feed"
            ] = feed

            bar[
                "timeframe"
            ] = timeframe

            all_bars.append(
                bar
            )

        page_token = (
            response.get(
                "next_page_token"
            )
        )

        if not page_token:

            break

    return all_bars


# ============================================================
# 23. MARKET CONDITION HISTORY
# ============================================================


def get_market_condition_history(
    symbol,
    minimum_observations=60,
    initial_calendar_days=120,
    maximum_calendar_days=730,
    include_snapshot=True,
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

    symbol = (
        symbol
        or
        ""
    )

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )

    if not symbol:

        raise AlpacaServiceError(
            (
                "A symbol is required for Market Condition "
                "data retrieval."
            )
        )


    # ========================================================
    # 23.2 NORMALISE MINIMUM OBSERVATION COUNT
    # ========================================================

    try:

        minimum_observations = int(
            minimum_observations
        )

    except (
        TypeError,
        ValueError,
    ):

        minimum_observations = 60

    minimum_observations = max(
        60,
        minimum_observations,
    )


    # ========================================================
    # 23.3 NORMALISE INITIAL WINDOW
    # ========================================================

    try:

        initial_calendar_days = int(
            initial_calendar_days
        )

    except (
        TypeError,
        ValueError,
    ):

        initial_calendar_days = 120


    # Approximately two calendar days per required trading
    # observation provides a safe initial margin for weekends
    # and holidays.

    initial_calendar_days = max(
        initial_calendar_days,
        minimum_observations * 2,
    )


    # ========================================================
    # 23.4 NORMALISE MAXIMUM WINDOW
    # ========================================================

    try:

        maximum_calendar_days = int(
            maximum_calendar_days
        )

    except (
        TypeError,
        ValueError,
    ):

        maximum_calendar_days = 730

    maximum_calendar_days = max(
        initial_calendar_days,
        maximum_calendar_days,
    )


    # ========================================================
    # 23.5 DATE RANGE
    # ========================================================

    # Add one day so the upper boundary safely includes the
    # most recent available daily observation returned by
    # Alpaca.

    end_value = (
        timezone.localdate()
        +
        timedelta(
            days=1
        )
    )


    # ========================================================
    # 23.6 BUILD PROGRESSIVE SEARCH WINDOWS
    # ========================================================

    history_windows = []

    current_window = (
        initial_calendar_days
    )

    while True:

        history_windows.append(
            current_window
        )

        if (
            current_window
            >=
            maximum_calendar_days
        ):

            break


        # Expand progressively instead of making dozens of
        # small Alpaca requests.

        expanded_window = max(
            current_window + 60,
            int(
                current_window
                *
                1.75
            ),
        )


        current_window = min(
            expanded_window,
            maximum_calendar_days,
        )


    # ========================================================
    # 23.7 FETCH HISTORICAL BARS
    # ========================================================

    selected_bars = []

    selected_start = None

    calendar_days_used = None


    for calendar_days in history_windows:

        start_value = (
            end_value
            -
            timedelta(
                days=calendar_days
            )
        )


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Reuse the existing historical-data implementation.
        #
        # No direct requests.get() call is introduced here.
        # ----------------------------------------------------

        bars = (
            get_historical_bars(
                symbol=symbol,
                start_date=start_value,
                end_date=end_value,
                timeframe="1Day",
                adjustment="raw",
            )
        )


        # ====================================================
        # 23.8 CLEAN DAILY BARS
        # ====================================================

        # A valid analytical observation requires:
        #
        # - a date
        # - open
        # - high
        # - low
        # - close
        #
        # Volume may legitimately be zero in unusual cases,
        # so it is not used to reject the observation.

        valid_bars = []

        for bar in bars:

            if not bar.get(
                "date"
            ):

                continue


            if bar.get(
                "open"
            ) is None:

                continue


            if bar.get(
                "high"
            ) is None:

                continue


            if bar.get(
                "low"
            ) is None:

                continue


            if bar.get(
                "close"
            ) is None:

                continue


            valid_bars.append(
                bar
            )


        # ====================================================
        # 23.9 REMOVE DUPLICATE DAILY OBSERVATIONS
        # ====================================================

        # Historical data should contain one daily observation
        # per symbol/date before it is persisted to MarketData.

        bars_by_date = {}

        for bar in valid_bars:

            bars_by_date[
                bar[
                    "date"
                ]
            ] = bar


        valid_bars = [

            bars_by_date[
                bar_date
            ]

            for bar_date in sorted(
                bars_by_date
            )
        ]


        selected_bars = (
            valid_bars
        )

        selected_start = (
            start_value
        )

        calendar_days_used = (
            calendar_days
        )


        # Stop as soon as enough real trading observations are
        # available.

        if (
            len(
                selected_bars
            )
            >=
            minimum_observations
        ):

            break


    # ========================================================
    # 23.10 CURRENT / LIVE SNAPSHOT
    # ========================================================

    snapshot = None

    snapshot_error = None


    if include_snapshot:

        try:

            snapshot = (
                get_stock_snapshot(
                    symbol
                )
            )

        except AlpacaServiceError as exc:

            # Snapshot failure should not invalidate valid
            # historical data.

            snapshot_error = (
                str(exc)
            )


    # ========================================================
    # 23.11 RESULT STATUS
    # ========================================================

    observation_count = (
        len(
            selected_bars
        )
    )


    has_minimum_history = (

        observation_count
        >=
        minimum_observations

    )


    latest_bar = (

        selected_bars[-1]

        if selected_bars

        else None
    )


    earliest_bar = (

        selected_bars[0]

        if selected_bars

        else None
    )


    latest_price = None


    if snapshot:

        latest_price = (
            snapshot.get(
                "latest_price"
            )
        )


    # If a current trade is temporarily unavailable, use the
    # latest historical close as display context.

    if (
        latest_price is None
        and
        latest_bar
    ):

        latest_price = (
            latest_bar.get(
                "close"
            )
        )


    # ========================================================
    # 23.12 USER-FRIENDLY MESSAGE
    # ========================================================

    if has_minimum_history:

        message = (
            f"{observation_count} daily Alpaca observations "
            f"are available for {symbol}. "
            "The dataset is ready for Market Condition "
            "analysis."
        )

    elif observation_count:

        message = (
            f"Alpaca returned {observation_count} daily "
            f"observations for {symbol}. "
            f"At least {minimum_observations} observations "
            "are required for Market Condition analysis."
        )

    else:

        message = (
            f"Alpaca returned no usable daily historical "
            f"observations for {symbol}."
        )


    # ========================================================
    # 23.13 RETURN MARKET CONDITION DATA PACKAGE
    # ========================================================

    return {

        "symbol":
            symbol,


        # ----------------------------------------------------
        # Provenance
        # ----------------------------------------------------

        "provider":
            "Alpaca",

        "feed":
            _data_feed()
            .upper(),

        "timeframe":
            "1Day",


        # ----------------------------------------------------
        # Analytical requirement
        # ----------------------------------------------------

        "minimum_observations":
            minimum_observations,

        "count":
            observation_count,

        "has_minimum_history":
            has_minimum_history,


        # ----------------------------------------------------
        # Requested historical window
        # ----------------------------------------------------

        "calendar_days_used":
            calendar_days_used,

        "requested_start":
            (
                selected_start.isoformat()
                if selected_start
                else None
            ),

        "requested_end":
            end_value.isoformat(),


        # ----------------------------------------------------
        # Actual historical coverage
        # ----------------------------------------------------

        "earliest_date":
            (
                earliest_bar.get(
                    "date"
                )
                if earliest_bar
                else None
            ),

        "latest_date":
            (
                latest_bar.get(
                    "date"
                )
                if latest_bar
                else None
            ),


        # ----------------------------------------------------
        # Current/latest Alpaca market context
        # ----------------------------------------------------

        "latest_price":
            latest_price,

        "snapshot":
            snapshot,

        "snapshot_error":
            snapshot_error,


        # ----------------------------------------------------
        # Historical observations used by the importing layer
        # ----------------------------------------------------

        "bars":
            selected_bars,


        # ----------------------------------------------------
        # Display status
        # ----------------------------------------------------

        "message":
            message,
    }


# ============================================================
# 24. GET US MARKET CLOCK
# ============================================================


def get_market_clock():
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

    cache_key = (
        "marketpulse_alpaca_market_clock"
    )

    cached_clock = (
        cache.get(
            cache_key
        )
    )

    if cached_clock is not None:

        return cached_clock

    response = _alpaca_get(
        _trading_base_url(),
        "/v2/clock",
    )

    if not isinstance(
        response,
        dict,
    ):

        raise AlpacaServiceError(
            (
                "Alpaca returned an unexpected market "
                "clock response."
            )
        )

    market_clock = {

        "timestamp":
            response.get(
                "timestamp"
            ),

        "is_open":
            bool(
                response.get(
                    "is_open",
                    False,
                )
            ),

        "next_open":
            response.get(
                "next_open"
            ),

        "next_close":
            response.get(
                "next_close"
            ),
    }

    cache.set(
        cache_key,
        market_clock,
        30,
    )

    return market_clock


# ============================================================
# 25. DASHBOARD MARKET OVERVIEW
# ============================================================


def get_dashboard_market_overview(
    symbols=None,
):
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

    if symbols is None:

        symbols = [
            "SPY",
            "QQQ",
            "DIA",
            "IWM",
        ]

    snapshots = (
        get_stock_snapshots(
            symbols
        )
    )

    benchmark_names = {

        "SPY":
            "S&P 500 ETF",

        "QQQ":
            "Nasdaq-100 ETF",

        "DIA":
            "Dow Jones ETF",

        "IWM":
            "Russell 2000 ETF",
    }

    benchmarks = []

    for symbol in symbols:

        symbol = (
            str(symbol)
            .strip()
            .upper()
        )

        snapshot = (
            snapshots.get(
                symbol
            )
        )

        if not snapshot:

            benchmarks.append(
                {

                    "symbol":
                        symbol,

                    "name":
                        benchmark_names.get(
                            symbol,
                            symbol,
                        ),

                    "available":
                        False,

                    "latest_price":
                        None,

                    "previous_close":
                        None,

                    "change":
                        None,

                    "change_pct":
                        None,

                    "day_open":
                        None,

                    "day_high":
                        None,

                    "day_low":
                        None,

                    "day_volume":
                        None,
                }
            )

            continue

        daily_bar = (
            snapshot.get(
                "daily_bar"
            )
            or
            {}
        )

        benchmarks.append(
            {

                "symbol":
                    symbol,

                "name":
                    benchmark_names.get(
                        symbol,
                        symbol,
                    ),

                "available":
                    True,

                "latest_price":
                    snapshot.get(
                        "latest_price"
                    ),

                "previous_close":
                    snapshot.get(
                        "previous_close"
                    ),

                "change":
                    snapshot.get(
                        "daily_change"
                    ),

                "change_pct":
                    snapshot.get(
                        "daily_change_pct"
                    ),

                "day_open":
                    daily_bar.get(
                        "open"
                    ),

                "day_high":
                    daily_bar.get(
                        "high"
                    ),

                "day_low":
                    daily_bar.get(
                        "low"
                    ),

                "day_volume":
                    daily_bar.get(
                        "volume"
                    ),
            }
        )

    try:

        market_clock = (
            get_market_clock()
        )

    except AlpacaServiceError:

        market_clock = {

            "timestamp":
                None,

            "is_open":
                False,

            "next_open":
                None,

            "next_close":
                None,
        }

    return {

        "provider":
            "Alpaca",

        "feed":
            _data_feed()
            .upper(),

        "market_clock":
            market_clock,

        "benchmarks":
            benchmarks,

        "updated_at":
            (
                timezone.now()
                .isoformat()
            ),
    }


# ============================================================
# 26. DASHBOARD CHART HISTORY
# ============================================================


def get_chart_history(
    symbol="SPY",
    period="1M",
):
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

    symbol = (
        symbol
        or
        "SPY"
    )

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )

    if not symbol:

        symbol = "SPY"


    # ========================================================
    # 26.2 NORMALISE PERIOD
    # ========================================================

    period = (
        period
        or
        "1M"
    )

    period = (
        str(period)
        .strip()
        .upper()
    )


    # ========================================================
    # 26.3 PERIOD CONFIGURATION
    # ========================================================

    period_config = {

        "1D": {

            "calendar_days":
                7,

            "timeframe":
                "5Min",

            "max_points":
                120,

            "date_only":
                False,
        },

        "5D": {

            "calendar_days":
                14,

            "timeframe":
                "30Min",

            "max_points":
                100,

            "date_only":
                False,
        },

        "1M": {

            "calendar_days":
                60,

            "timeframe":
                "1Day",

            "max_points":
                30,

            "date_only":
                True,
        },

        "3M": {

            "calendar_days":
                140,

            "timeframe":
                "1Day",

            "max_points":
                70,

            "date_only":
                True,
        },
    }

    config = (
        period_config.get(
            period
        )
    )

    if config is None:

        raise AlpacaServiceError(
            (
                "Unsupported chart period. "
                "Use 1D, 5D, 1M or 3M."
            )
        )


    # ========================================================
    # 26.4 BUILD ALPACA DATE RANGE
    # ========================================================

    if config[
        "date_only"
    ]:

        end_value = (
            timezone.localdate()
            +
            timedelta(
                days=1
            )
        )

        start_value = (
            end_value
            -
            timedelta(
                days=config[
                    "calendar_days"
                ]
            )
        )

    else:

        end_value = (
            timezone.now()
        )

        start_value = (
            end_value
            -
            timedelta(
                days=config[
                    "calendar_days"
                ]
            )
        )


    # ========================================================
    # 26.5 REQUEST HISTORICAL BARS FROM ALPACA
    # ========================================================

    bars = (
        get_historical_bars(
            symbol=symbol,
            start_date=start_value,
            end_date=end_value,
            timeframe=config[
                "timeframe"
            ],
            adjustment="raw",
        )
    )


    # ========================================================
    # 26.6 KEEP LATEST REQUIRED OBSERVATIONS
    # ========================================================

    max_points = (
        config[
            "max_points"
        ]
    )

    if (
        max_points
        and
        len(
            bars
        )
        >
        max_points
    ):

        bars = (
            bars[
                -max_points:
            ]
        )


    # ========================================================
    # 26.7 BUILD CHART POINTS
    # ========================================================

    chart_points = []

    for bar in bars:

        timestamp = (
            bar.get(
                "timestamp"
            )
        )

        close_price = (
            bar.get(
                "close"
            )
        )

        if not timestamp:

            continue

        if close_price is None:

            continue

        chart_points.append(
            {

                "timestamp":
                    timestamp,

                "date":
                    bar.get(
                        "date"
                    ),

                "open":
                    bar.get(
                        "open"
                    ),

                "high":
                    bar.get(
                        "high"
                    ),

                "low":
                    bar.get(
                        "low"
                    ),

                "close":
                    close_price,

                "volume":
                    bar.get(
                        "volume"
                    ),
            }
        )


    # ========================================================
    # 26.8 STATUS MESSAGE
    # ========================================================

    if chart_points:

        message = (
            f"{len(chart_points)} historical "
            f"{config['timeframe']} bars were returned "
            f"from Alpaca."
        )

    else:

        message = (
            "Alpaca returned no historical bars "
            f"for {symbol} using the "
            f"{_data_feed().upper()} feed."
        )


    # ========================================================
    # 26.9 RETURN DASHBOARD DATA
    # ========================================================

    return {

        "symbol":
            symbol,

        "period":
            period,

        "timeframe":
            config[
                "timeframe"
            ],

        "provider":
            "Alpaca",

        "feed":
            (
                _data_feed()
                .upper()
            ),

        "requested_start":
            (
                start_value.isoformat()
                if hasattr(
                    start_value,
                    "isoformat",
                )
                else str(
                    start_value
                )
            ),

        "requested_end":
            (
                end_value.isoformat()
                if hasattr(
                    end_value,
                    "isoformat",
                )
                else str(
                    end_value
                )
            ),

        "points":
            chart_points,

        "count":
            len(
                chart_points
            ),

        "has_data":
            bool(
                chart_points
            ),

        "message":
            message,
    }


# ============================================================
# 27. TEST ALPACA CONNECTION
# ============================================================


def test_alpaca_connection():
    """
    ------------------------------------------------------------
    TEST ALPACA CONFIGURATION AND CONNECTION
    ------------------------------------------------------------

    This helper deliberately does not expose API credentials.

    It confirms only whether MarketPulse can authenticate
    successfully and retrieve Alpaca market-clock information.
    ------------------------------------------------------------
    """

    try:

        market_clock = (
            get_market_clock()
        )

        return {

            "success":
                True,

            "provider":
                "Alpaca",

            "feed":
                (
                    _data_feed()
                    .upper()
                ),

            "market_open":
                market_clock.get(
                    "is_open"
                ),

            "message":
                (
                    "MarketPulse connected successfully "
                    "to Alpaca."
                ),
        }

    except AlpacaServiceError as exc:

        return {

            "success":
                False,

            "provider":
                "Alpaca",

            "feed":
                None,

            "market_open":
                None,

            "message":
                str(
                    exc
                ),
        }