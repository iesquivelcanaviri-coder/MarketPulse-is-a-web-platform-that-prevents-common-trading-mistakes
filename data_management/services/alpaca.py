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

1. Validate Alpaca configuration
2. Authenticate server-side requests
3. Search Alpaca's active US-equity universe
4. Retrieve asset information
5. Retrieve current stock snapshots
6. Retrieve multiple stock snapshots
7. Retrieve historical OHLCV bars
8. Retrieve US market clock information
9. Build the Dashboard market overview
10. Retrieve market history for Dashboard charts


SECURITY:

The browser NEVER receives:

- ALPACA_API_KEY_ID
- ALPACA_API_SECRET_KEY

Credentials remain inside Django settings and environment
variables.

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

    Views can catch this exception and display a friendly
    message instead of exposing raw API errors to the user.
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

    However, if /v2 or /v3 was accidentally included in the
    environment variable, this helper removes it.

    This prevents URLs such as:

        /v2/v2/assets

    from being created.
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

    For the current MarketPulse educational project this will
    normally be:

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

    return int(
        getattr(
            settings,
            "ALPACA_REQUEST_TIMEOUT",
            8,
        )
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

    This gives MarketPulse one place to manage:

    - authentication
    - timeouts
    - HTTP errors
    - connection failures
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

        return float(value)


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

        return int(value)


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
            asset.get("id"),

        "symbol":
            (
                asset.get("symbol")
                or
                ""
            ).upper(),

        "name":
            asset.get("name")
            or
            "",

        "exchange":
            asset.get("exchange")
            or
            "",

        "asset_class":
            asset.get("class")
            or
            asset.get("asset_class")
            or
            "",

        "status":
            asset.get("status")
            or
            "",

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
        bar.get("t")
        or
        bar.get("timestamp")
    )


    date_value = None


    if timestamp:

        date_value = (
            str(timestamp)[:10]
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
                bar.get("o")
                if "o" in bar
                else bar.get("open")
            ),

        "high":
            _to_float(
                bar.get("h")
                if "h" in bar
                else bar.get("high")
            ),

        "low":
            _to_float(
                bar.get("l")
                if "l" in bar
                else bar.get("low")
            ),

        "close":
            _to_float(
                bar.get("c")
                if "c" in bar
                else bar.get("close")
            ),

        "volume":
            _to_int(
                bar.get("v")
                if "v" in bar
                else bar.get("volume")
            ),

        "trade_count":
            _to_int(
                bar.get("n")
                if "n" in bar
                else bar.get(
                    "trade_count"
                )
            ),

        "vwap":
            _to_float(
                bar.get("vw")
                if "vw" in bar
                else bar.get("vwap")
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
    Dashboard and Risk tab can consume consistently.
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
        latest_trade.get("p")
        if "p" in latest_trade
        else latest_trade.get(
            "price"
        )
    )


    bid_price = _to_float(
        latest_quote.get("bp")
        if "bp" in latest_quote
        else latest_quote.get(
            "bid_price"
        )
    )


    ask_price = _to_float(
        latest_quote.get("ap")
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


    daily_bar = _normalise_bar(
        daily_bar_raw
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
            feed
            or
            _data_feed(),

        "latest_price":
            latest_price,

        "latest_trade_timestamp":
            latest_trade.get("t")
            or
            latest_trade.get(
                "timestamp"
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

        asset = _normalise_asset(
            raw_asset
        )


        if (
            asset
            and
            asset.get("symbol")
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

        limit = int(limit)

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


        # Tradable assets receive a small ranking preference.

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
                len(symbol),
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


    cached_asset = cache.get(
        cache_key
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


    asset = _normalise_asset(
        response
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


    feed = _data_feed()


    cache_key = (
        "marketpulse_alpaca_snapshot_"
        +
        feed
        +
        "_"
        +
        symbol
    )


    cached_snapshot = cache.get(
        cache_key
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


    snapshot["symbol"] = symbol


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

    This is useful for the Dashboard because SPY, QQQ, DIA
    and IWM can be requested together rather than requiring
    four separate HTTP requests.
    ------------------------------------------------------------
    """

    if isinstance(
        symbols,
        str,
    ):

        symbols = (
            symbols.split(",")
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


    # Prevent an accidentally huge request.

    cleaned_symbols = (
        cleaned_symbols[:50]
    )


    feed = _data_feed()


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
            response.get(symbol)
            or
            response.get(
                symbol.upper()
            )
        )


        if raw_snapshot is None:

            continue


        snapshot = _normalise_snapshot(
            raw_snapshot,
            feed=feed,
        )


        snapshot["symbol"] = (
            symbol
        )


        snapshots[symbol] = (
            snapshot
        )


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

    This function replaces the Yahoo Finance data-retrieval
    responsibility in MarketPulse.

    It can be used by:

        data_management/utils.py
            ↓
        MarketData
            ↓
        Data tab
        Strategies
        Market Condition
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
        else str(start_date)
    )


    end_value = (
        end_date.isoformat()
        if hasattr(
            end_date,
            "isoformat",
        )
        else str(end_date)
    )


    try:

        limit = int(limit)

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


    feed = _data_feed()


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

            bar = _normalise_bar(
                raw_bar,
                symbol=symbol,
            )


            if bar:

                bar["provider"] = (
                    "Alpaca"
                )


                bar["feed"] = (
                    feed
                )


                bar["timeframe"] = (
                    timeframe
                )


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
# 23. GET US MARKET CLOCK
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

    This is useful for the live Dashboard header.
    ------------------------------------------------------------
    """

    cache_key = (
        "marketpulse_alpaca_market_clock"
    )


    cached_clock = cache.get(
        cache_key
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


    # The market clock can be refreshed frequently while still
    # avoiding an unnecessary request on every page render.

    cache.set(
        cache_key,
        market_clock,
        30,
    )


    return market_clock


# ============================================================
# 24. DASHBOARD MARKET OVERVIEW
# ============================================================


def get_dashboard_market_overview(
    symbols=None,
):
    """
    ------------------------------------------------------------
    BUILD DASHBOARD MARKET OVERVIEW
    ------------------------------------------------------------

    The Dashboard uses a small benchmark set to give the user
    immediate context about the US equity market.

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
            timezone.now()
            .isoformat(),
    }


# ============================================================
# 25. DASHBOARD CHART HISTORY
# ============================================================


def get_chart_history(
    symbol="SPY",
    period="1M",
):
    """
    ------------------------------------------------------------
    GET DASHBOARD PRICE-CHART HISTORY
    ------------------------------------------------------------

    Supported periods:

        1D
        5D
        1M
        3M

    MarketPulse chooses a sensible Alpaca timeframe for each
    period so the graph remains readable.
    ------------------------------------------------------------
    """

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


    period_config = {

        "1D": {
            "days":
                1,

            "timeframe":
                "5Min",
        },

        "5D": {
            "days":
                7,

            "timeframe":
                "30Min",
        },

        "1M": {
            "days":
                35,

            "timeframe":
                "1Day",
        },

        "3M": {
            "days":
                100,

            "timeframe":
                "1Day",
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


    end_time = (
        timezone.now()
    )


    start_time = (
        end_time
        -
        timedelta(
            days=config[
                "days"
            ]
        )
    )


    bars = get_historical_bars(
        symbol=symbol,
        start_date=start_time,
        end_date=end_time,
        timeframe=config[
            "timeframe"
        ],
        adjustment="raw",
    )


    chart_points = []


    for bar in bars:

        if (
            bar.get(
                "timestamp"
            )
            and
            bar.get(
                "close"
            )
            is not None
        ):

            chart_points.append(
                {
                    "timestamp":
                        bar.get(
                            "timestamp"
                        ),

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
                        bar.get(
                            "close"
                        ),

                    "volume":
                        bar.get(
                            "volume"
                        ),
                }
            )


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
            _data_feed()
            .upper(),

        "points":
            chart_points,

        "count":
            len(
                chart_points
            ),
    }


# ============================================================
# 26. TEST ALPACA CONNECTION
# ============================================================


def test_alpaca_connection():
    """
    ------------------------------------------------------------
    TEST ALPACA CONFIGURATION AND CONNECTION
    ------------------------------------------------------------

    This helper deliberately does not expose API credentials.

    It simply confirms whether MarketPulse can authenticate
    with Alpaca and retrieve the US market clock.
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
                _data_feed()
                .upper(),

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
                str(exc),
        }