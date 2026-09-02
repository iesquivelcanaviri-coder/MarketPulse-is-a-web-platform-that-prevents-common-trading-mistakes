"""
============================================================
MARKETPULSE - ALPACA MARKET DATA SERVICE
============================================================

Framework mapping:

Browser / JavaScript / React
        ↓
MarketPulse Django API
        ↓
data_management.services.alpaca
        ↓
Alpaca REST APIs
        ↓
Normalised MarketPulse market data


PURPOSE:

This service isolates MarketPulse from Alpaca-specific API
implementation details.

It provides:

1. Active US-equity universe
2. Search by ticker or company name
3. Individual asset metadata
4. Latest stock snapshot
5. Latest trade
6. Latest bid / ask
7. Bid-ask spread
8. Current daily OHLCV
9. Previous daily OHLCV
10. Asset capabilities
11. Combined asset + market overview


IMPORTANT SECURITY RULE:

Alpaca credentials must remain on the Django server.

They must never be exposed through:

- HTML
- JavaScript
- React
- API JSON responses
- GitHub
- screenshots
- browser developer tools

The frontend communicates with MarketPulse.

MarketPulse communicates with Alpaca.
============================================================
"""

from __future__ import annotations


# ============================================================
# 1. IMPORTS
# ============================================================

from urllib.parse import quote

import requests

from django.conf import settings
from django.core.cache import cache


# ============================================================
# 2. CUSTOM SERVICE EXCEPTION
# ============================================================

class AlpacaServiceError(Exception):
    """
    Raised when MarketPulse cannot successfully communicate
    with Alpaca or receives invalid Alpaca configuration.
    """

    pass


# ============================================================
# 3. BASE URL NORMALISATION
# ============================================================

def _normalise_base_url(
    base_url,
):
    """
    ------------------------------------------------------------
    NORMALISE ALPACA BASE URL
    ------------------------------------------------------------

    MarketPulse expects base URLs such as:

        https://paper-api.alpaca.markets

        https://data.alpaca.markets

    However, this helper also safely handles configuration such
    as:

        https://paper-api.alpaca.markets/v2

    This prevents MarketPulse accidentally constructing:

        /v2/v2/assets

    The service itself is responsible for adding API versions.
    ------------------------------------------------------------
    """


    if not base_url:

        return ""


    base_url = (
        str(base_url)
        .strip()
        .rstrip("/")
    )


    if base_url.endswith(
        "/v2"
    ):

        base_url = (
            base_url[:-3]
            .rstrip("/")
        )


    return base_url


# ============================================================
# 4. TRADING API BASE URL
# ============================================================

def _trading_base_url():
    """
    Return the configured Alpaca paper/live trading API root.

    For this student project the intended value is:

        https://paper-api.alpaca.markets
    """


    base_url = (
        _normalise_base_url(
            settings.ALPACA_TRADING_BASE_URL
        )
    )


    if not base_url:

        raise AlpacaServiceError(
            "ALPACA_TRADING_BASE_URL is not configured."
        )


    return base_url


# ============================================================
# 5. MARKET DATA API BASE URL
# ============================================================

def _data_base_url():
    """
    Return the Alpaca market-data API root.

    Expected:

        https://data.alpaca.markets
    """


    base_url = (
        _normalise_base_url(
            settings.ALPACA_DATA_BASE_URL
        )
    )


    if not base_url:

        raise AlpacaServiceError(
            "ALPACA_DATA_BASE_URL is not configured."
        )


    return base_url


# ============================================================
# 6. AUTHENTICATION HEADERS
# ============================================================

def _alpaca_headers():
    """
    ------------------------------------------------------------
    ALPACA AUTHENTICATION
    ------------------------------------------------------------

    Credentials come from Django settings.

    Django settings should load them from the private .env file.

    They are never returned to the frontend.
    ------------------------------------------------------------
    """


    api_key = (
        getattr(
            settings,
            "ALPACA_API_KEY_ID",
            "",
        )
        .strip()
    )


    secret_key = (
        getattr(
            settings,
            "ALPACA_API_SECRET_KEY",
            "",
        )
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
# 7. GENERIC ALPACA GET REQUEST
# ============================================================

def _alpaca_get(
    url,
    params=None,
):
    """
    ------------------------------------------------------------
    PERFORM AUTHENTICATED ALPACA GET REQUEST
    ------------------------------------------------------------

    Features:

    - authentication headers
    - timeout protection
    - HTTP validation
    - JSON validation
    - useful MarketPulse error messages
    ------------------------------------------------------------
    """


    try:

        response = requests.get(
            url,
            headers=_alpaca_headers(),
            params=params or {},
            timeout=10,
        )


        response.raise_for_status()


        try:

            return response.json()


        except ValueError as exc:

            raise AlpacaServiceError(
                "Alpaca returned a response that was not valid JSON."
            ) from exc


    except requests.Timeout as exc:

        raise AlpacaServiceError(
            "Alpaca did not respond before the request timed out."
        ) from exc


    except requests.ConnectionError as exc:

        raise AlpacaServiceError(
            "MarketPulse could not connect to Alpaca."
        ) from exc


    except requests.HTTPError as exc:

        status_code = None


        if (
            exc.response
            is not None
        ):

            status_code = (
                exc.response.status_code
            )


        error_message = (
            "MarketPulse could not retrieve data from Alpaca."
        )


        if status_code == 401:

            error_message = (
                "Alpaca rejected the API credentials. "
                "Check that the Alpaca key ID and secret key "
                "are valid."
            )


        elif status_code == 403:

            error_message = (
                "Alpaca denied access to this market-data "
                "resource. Check the selected data feed and "
                "your Alpaca subscription."
            )


        elif status_code == 404:

            error_message = (
                "The requested Alpaca asset or endpoint "
                "could not be found."
            )


        elif status_code == 429:

            error_message = (
                "The Alpaca API rate limit was reached. "
                "Please wait briefly and try again."
            )


        elif (
            exc.response
            is not None
        ):

            try:

                alpaca_error = (
                    exc.response.json()
                )


                api_message = (
                    alpaca_error.get(
                        "message"
                    )
                )


                if api_message:

                    error_message = (
                        f"Alpaca error: {api_message}"
                    )


            except ValueError:

                pass


        raise AlpacaServiceError(
            error_message
        ) from exc


    except requests.RequestException as exc:

        raise AlpacaServiceError(
            "An unexpected network error occurred "
            "while communicating with Alpaca."
        ) from exc


# ============================================================
# 8. NORMALISE ASSET DATA
# ============================================================

def _normalise_asset(
    asset,
):
    """
    Convert Alpaca's Asset object into the smaller,
    consistent structure used by MarketPulse.
    """


    if not asset:

        return None


    return {

        "id":
            asset.get(
                "id"
            ),

        "symbol":
            asset.get(
                "symbol"
            ),

        "name":
            asset.get(
                "name"
            ),

        "exchange":
            asset.get(
                "exchange"
            ),

        "status":
            asset.get(
                "status"
            ),

        "asset_class":
            asset.get(
                "class"
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

        "easy_to_borrow":
            bool(
                asset.get(
                    "easy_to_borrow",
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

        "maintenance_margin_requirement":
            asset.get(
                "maintenance_margin_requirement"
            ),

        "initial_margin_requirement":
            asset.get(
                "initial_margin_requirement"
            ),

        "borrow_status":
            asset.get(
                "borrow_status"
            ),

        "attributes":
            asset.get(
                "attributes",
                [],
            ),
    }


# ============================================================
# 9. GET ACTIVE US EQUITY UNIVERSE
# ============================================================

def get_active_us_equities(
    force_refresh=False,
):
    """
    ------------------------------------------------------------
    GET ALPACA ACTIVE US EQUITIES
    ------------------------------------------------------------

    Alpaca's assets endpoint acts as the master instrument
    catalogue.

    MarketPulse retrieves active US equities and caches the
    complete result for 30 minutes.

    This is considerably more efficient than sending an
    external Alpaca request every time somebody types one
    character into the Risk asset search.
    ------------------------------------------------------------
    """


    cache_key = (
        "marketpulse_alpaca_active_us_equities"
    )


    if not force_refresh:

        cached_assets = (
            cache.get(
                cache_key
            )
        )


        if (
            cached_assets
            is not None
        ):

            return cached_assets


    url = (
        f"{_trading_base_url()}"
        f"/v2/assets"
    )


    raw_assets = (
        _alpaca_get(
            url,
            params={
                "status":
                    "active",

                "asset_class":
                    "us_equity",
            },
        )
    )


    if not isinstance(
        raw_assets,
        list,
    ):

        raise AlpacaServiceError(
            "Alpaca returned an unexpected asset-list response."
        )


    assets = []


    for raw_asset in raw_assets:

        asset = (
            _normalise_asset(
                raw_asset
            )
        )


        if (
            not asset
            or
            not asset.get(
                "symbol"
            )
        ):

            continue


        assets.append(
            asset
        )


    # --------------------------------------------------------
    # Sort alphabetically for predictable searches
    # --------------------------------------------------------

    assets.sort(
        key=lambda asset:
            asset["symbol"]
    )


    # --------------------------------------------------------
    # Cache master universe for 30 minutes
    # --------------------------------------------------------

    cache.set(
        cache_key,
        assets,
        60 * 30,
    )


    return assets


# ============================================================
# 10. SEARCH ALPACA ASSETS
# ============================================================

def search_assets(
    query,
    limit=12,
):
    """
    ------------------------------------------------------------
    SEARCH ACTIVE ALPACA ASSETS
    ------------------------------------------------------------

    Search using:

    - exact ticker
    - ticker prefix
    - ticker contains
    - company / asset name

    Examples:

        AAPL
            → Apple

        MICROSOFT
            → MSFT

        MICRO
            → Microsoft and other matching names


    Search ranking:

    1. exact symbol
    2. symbol prefix
    3. company name prefix
    4. symbol/name contains
    ------------------------------------------------------------
    """


    query = (
        str(query or "")
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


    exact_symbol = []

    symbol_prefix = []

    name_prefix = []

    contains = []


    for asset in assets:

        symbol = (
            asset.get(
                "symbol",
                "",
            )
            .upper()
        )


        name = (
            asset.get(
                "name",
                "",
            )
            .upper()
        )


        if symbol == query:

            exact_symbol.append(
                asset
            )


        elif symbol.startswith(
            query
        ):

            symbol_prefix.append(
                asset
            )


        elif name.startswith(
            query
        ):

            name_prefix.append(
                asset
            )


        elif (
            query in symbol
            or
            query in name
        ):

            contains.append(
                asset
            )


    results = (

        exact_symbol
        +
        symbol_prefix
        +
        name_prefix
        +
        contains
    )


    return results[:limit]


# ============================================================
# 11. GET ONE ALPACA ASSET
# ============================================================

def get_asset(
    symbol,
    force_refresh=False,
):
    """
    ------------------------------------------------------------
    GET INDIVIDUAL ASSET METADATA
    ------------------------------------------------------------

    Returns information such as:

    - symbol
    - company / asset name
    - exchange
    - active status
    - tradability
    - marginability
    - shortability
    - fractional availability
    ------------------------------------------------------------
    """


    symbol = (
        str(symbol or "")
        .strip()
        .upper()
    )


    if not symbol:

        raise AlpacaServiceError(
            "A stock symbol is required."
        )


    cache_key = (
        f"marketpulse_alpaca_asset_{symbol}"
    )


    if not force_refresh:

        cached_asset = (
            cache.get(
                cache_key
            )
        )


        if (
            cached_asset
            is not None
        ):

            return cached_asset


    encoded_symbol = quote(
        symbol,
        safe="",
    )


    url = (
        f"{_trading_base_url()}"
        f"/v2/assets/"
        f"{encoded_symbol}"
    )


    raw_asset = (
        _alpaca_get(
            url
        )
    )


    asset = (
        _normalise_asset(
            raw_asset
        )
    )


    if (
        not asset
        or
        not asset.get(
            "symbol"
        )
    ):

        raise AlpacaServiceError(
            f"Alpaca returned no valid asset information "
            f"for {symbol}."
        )


    # Asset metadata changes much less frequently
    # than market prices.
    cache.set(
        cache_key,
        asset,
        60 * 30,
    )


    return asset


# ============================================================
# 12. NORMALISE MARKET BAR
# ============================================================

def _normalise_bar(
    bar,
):
    """
    Convert Alpaca's compact bar field names into descriptive
    MarketPulse field names.
    """


    bar = (
        bar
        or {}
    )


    return {

        "open":
            bar.get(
                "o"
            ),

        "high":
            bar.get(
                "h"
            ),

        "low":
            bar.get(
                "l"
            ),

        "close":
            bar.get(
                "c"
            ),

        "volume":
            bar.get(
                "v"
            ),

        "trade_count":
            bar.get(
                "n"
            ),

        "vwap":
            bar.get(
                "vw"
            ),

        "timestamp":
            bar.get(
                "t"
            ),
    }


# ============================================================
# 13. GET LATEST STOCK SNAPSHOT
# ============================================================

def get_stock_snapshot(
    symbol,
    force_refresh=False,
):
    """
    ------------------------------------------------------------
    GET ALPACA STOCK SNAPSHOT
    ------------------------------------------------------------

    One Alpaca snapshot request can provide:

    - latest trade
    - latest quote
    - minute bar
    - current daily bar
    - previous daily bar

    This is more efficient than making separate API calls for
    each of those items.
    ------------------------------------------------------------
    """


    symbol = (
        str(symbol or "")
        .strip()
        .upper()
    )


    if not symbol:

        raise AlpacaServiceError(
            "A stock symbol is required."
        )


    data_feed = (
        getattr(
            settings,
            "ALPACA_DATA_FEED",
            "iex",
        )
        .strip()
        .lower()
    )


    allowed_feeds = {
        "iex",
        "sip",
        "delayed_sip",
        "boats",
        "overnight",
        "otc",
    }


    if (
        data_feed
        not in allowed_feeds
    ):

        raise AlpacaServiceError(
            (
                "Invalid ALPACA_DATA_FEED configuration: "
                f"{data_feed}"
            )
        )


    cache_key = (
        "marketpulse_alpaca_snapshot_"
        f"{data_feed}_{symbol}"
    )


    if not force_refresh:

        cached_snapshot = (
            cache.get(
                cache_key
            )
        )


        if (
            cached_snapshot
            is not None
        ):

            return cached_snapshot


    encoded_symbol = quote(
        symbol,
        safe="",
    )


    url = (
        f"{_data_base_url()}"
        f"/v2/stocks/"
        f"{encoded_symbol}"
        f"/snapshot"
    )


    raw = (
        _alpaca_get(
            url,
            params={
                "feed":
                    data_feed,

                "currency":
                    "USD",
            },
        )
    )


    if not isinstance(
        raw,
        dict,
    ):

        raise AlpacaServiceError(
            "Alpaca returned an unexpected snapshot response."
        )


    # ========================================================
    # ALPACA RESPONSE SECTIONS
    # ========================================================

    latest_trade = (
        raw.get(
            "latestTrade"
        )
        or {}
    )


    latest_quote = (
        raw.get(
            "latestQuote"
        )
        or {}
    )


    minute_bar = (
        raw.get(
            "minuteBar"
        )
        or {}
    )


    daily_bar = (
        raw.get(
            "dailyBar"
        )
        or {}
    )


    previous_daily_bar = (
        raw.get(
            "prevDailyBar"
        )
        or {}
    )


    # ========================================================
    # LATEST TRADE
    # ========================================================

    latest_price = (
        latest_trade.get(
            "p"
        )
    )


    # ========================================================
    # BID / ASK
    # ========================================================

    bid_price = (
        latest_quote.get(
            "bp"
        )
    )


    ask_price = (
        latest_quote.get(
            "ap"
        )
    )


    bid_size = (
        latest_quote.get(
            "bs"
        )
    )


    ask_size = (
        latest_quote.get(
            "as"
        )
    )


    spread = None

    spread_percentage = None

    midpoint = None


    if (
        bid_price is not None
        and
        ask_price is not None
    ):

        bid_price_float = float(
            bid_price
        )

        ask_price_float = float(
            ask_price
        )


        spread = (
            ask_price_float
            -
            bid_price_float
        )


        midpoint = (

            bid_price_float
            +
            ask_price_float

        ) / 2


        if midpoint > 0:

            spread_percentage = (

                spread
                /
                midpoint
                *
                100
            )


    # ========================================================
    # DAILY CHANGE
    # ========================================================

    previous_close = (
        previous_daily_bar.get(
            "c"
        )
    )


    daily_change = None

    daily_change_pct = None


    if (
        latest_price is not None
        and
        previous_close not in (
            None,
            0,
        )
    ):

        latest_price_float = (
            float(
                latest_price
            )
        )


        previous_close_float = (
            float(
                previous_close
            )
        )


        daily_change = (

            latest_price_float
            -
            previous_close_float
        )


        daily_change_pct = (

            daily_change
            /
            previous_close_float
            *
            100
        )


    # ========================================================
    # NORMALISED MARKETPULSE SNAPSHOT
    # ========================================================

    snapshot = {

        # ----------------------------------------------------
        # Provenance
        # ----------------------------------------------------

        "symbol":
            symbol,

        "provider":
            "Alpaca",

        "feed":
            data_feed.upper(),

        "currency":
            "USD",


        # ----------------------------------------------------
        # Latest trade
        # ----------------------------------------------------

        "latest_price":
            latest_price,

        "latest_trade_size":
            latest_trade.get(
                "s"
            ),

        "latest_trade_timestamp":
            latest_trade.get(
                "t"
            ),

        "latest_trade_exchange":
            latest_trade.get(
                "x"
            ),


        # ----------------------------------------------------
        # Latest quote
        # ----------------------------------------------------

        "bid_price":
            bid_price,

        "bid_size":
            bid_size,

        "ask_price":
            ask_price,

        "ask_size":
            ask_size,

        "quote_timestamp":
            latest_quote.get(
                "t"
            ),

        "quote_exchange_bid":
            latest_quote.get(
                "bx"
            ),

        "quote_exchange_ask":
            latest_quote.get(
                "ax"
            ),

        "spread":
            (
                round(
                    spread,
                    6,
                )
                if spread is not None
                else None
            ),

        "spread_percentage":
            (
                round(
                    spread_percentage,
                    4,
                )
                if spread_percentage
                is not None
                else None
            ),

        "midpoint":
            (
                round(
                    midpoint,
                    6,
                )
                if midpoint is not None
                else None
            ),


        # ----------------------------------------------------
        # Current movement
        # ----------------------------------------------------

        "previous_close":
            previous_close,

        "daily_change":
            (
                round(
                    daily_change,
                    4,
                )
                if daily_change
                is not None
                else None
            ),

        "daily_change_pct":
            (
                round(
                    daily_change_pct,
                    2,
                )
                if daily_change_pct
                is not None
                else None
            ),


        # ----------------------------------------------------
        # OHLCV
        # ----------------------------------------------------

        "minute_bar":
            _normalise_bar(
                minute_bar
            ),

        "daily_bar":
            _normalise_bar(
                daily_bar
            ),

        "previous_daily_bar":
            _normalise_bar(
                previous_daily_bar
            ),
    }


    # --------------------------------------------------------
    # Keep price data relatively fresh
    # --------------------------------------------------------

    cache.set(
        cache_key,
        snapshot,
        15,
    )


    return snapshot


# ============================================================
# 14. GET COMPLETE ASSET MARKET OVERVIEW
# ============================================================

def get_asset_market_overview(
    symbol,
    force_refresh=False,
):
    """
    ------------------------------------------------------------
    COMPLETE MARKETPULSE ASSET OVERVIEW
    ------------------------------------------------------------

    Combines:

        Alpaca Asset API
                +
        Alpaca Market Data Snapshot
                ↓
        One MarketPulse object


    This is especially useful for:

    - Risk tab
    - Data tab
    - Strategy selection
    - dashboards
    - React components
    ------------------------------------------------------------
    """


    symbol = (
        str(symbol or "")
        .strip()
        .upper()
    )


    asset = (
        get_asset(
            symbol,
            force_refresh=force_refresh,
        )
    )


    snapshot = (
        get_stock_snapshot(
            symbol,
            force_refresh=force_refresh,
        )
    )


    return {

        "asset":
            asset,

        "market":
            snapshot,

        "source":
            {
                "provider":
                    "Alpaca",

                "feed":
                    snapshot.get(
                        "feed"
                    ),

                "asset_api":
                    "Trading API",

                "market_data_api":
                    "Market Data API",
            },
    }


# ============================================================
# 15. CONNECTION TEST
# ============================================================

def test_alpaca_connection():
    """
    ------------------------------------------------------------
    SAFE CONNECTION TEST
    ------------------------------------------------------------

    Tests the Alpaca integration without exposing API keys.

    AAPL is used simply because it is a widely available
    US-equity symbol.

    Returns only safe diagnostic information.
    ------------------------------------------------------------
    """


    try:

        asset = (
            get_asset(
                "AAPL",
                force_refresh=True,
            )
        )


        snapshot = (
            get_stock_snapshot(
                "AAPL",
                force_refresh=True,
            )
        )


        return {

            "success":
                True,

            "provider":
                "Alpaca",

            "feed":
                snapshot.get(
                    "feed"
                ),

            "symbol":
                asset.get(
                    "symbol"
                ),

            "asset_name":
                asset.get(
                    "name"
                ),

            "exchange":
                asset.get(
                    "exchange"
                ),

            "latest_price_available":
                (
                    snapshot.get(
                        "latest_price"
                    )
                    is not None
                ),
        }


    except AlpacaServiceError as error:

        return {

            "success":
                False,

            "error":
                str(error),
        }