"""
============================================================
MARKETPULSE - MARKET DATA IMPORT SERVICE
============================================================

FRAMEWORK MAPPING:

Alpaca Market Data API
        ↓
data_management/services/alpaca.py
        ↓
data_management/utils.py
        ↓
core.MarketData
        ↓
PostgreSQL
        ↓
Data Tab
Strategies
Backtesting
Market Condition
Risk


PURPOSE:

This module provides the provider-neutral historical market
data layer used by MarketPulse.

The module is responsible for:

1. Requesting historical bars through the Alpaca service.
2. Normalising external market-data records.
3. Persisting OHLCV observations in core.MarketData.
4. Updating existing rows instead of creating duplicates.
5. Checking whether enough historical observations exist for
   analytical features.
6. Refreshing recent historical data when required.
7. Ensuring Market Condition analysis has sufficient history.


IMPORTANT ARCHITECTURE:

External API communication belongs only inside:

    data_management/services/alpaca.py

This module does NOT contain:

- Alpaca API keys
- authentication headers
- requests.get()
- direct external HTTP calls


Instead:

services/alpaca.py
        ↓
get_historical_bars()
        ↓
utils.py
        ↓
MarketData


MARKET CONDITION FLOW:

User selects SPY
        ↓
data_management/views.py
        ↓
ensure_market_data_for_analysis("SPY")
        ↓
Enough stored data?
        ↓
NO
        ↓
import_market_data()
        ↓
Alpaca historical bars
        ↓
MarketData.update_or_create()
        ↓
PostgreSQL
        ↓
At least 60 observations?
        ↓
YES
        ↓
analysis_tools.analyzers.identify_market_regime()
        ↓
MarketRegime


WHY 60 OBSERVATIONS?

The current Market Condition classifier uses:

- recent returns
- annualised volatility
- 20-period moving average
- 60-period moving average
- trend strength

Therefore at least 60 historical observations are required.

============================================================
"""


# ============================================================
# 1. PYTHON IMPORTS
# ============================================================

from datetime import (
    date,
    datetime,
    timedelta,
)

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)


# ============================================================
# 2. DJANGO IMPORTS
# ============================================================

from django.db import transaction

from django.db.models import (
    Count,
    Max,
    Min,
)

from django.utils import timezone

from django.utils.dateparse import (
    parse_date,
    parse_datetime,
)


# ============================================================
# 3. MARKETPULSE MODEL IMPORT
# ============================================================

from core.models import MarketData


# ============================================================
# 4. ALPACA SERVICE IMPORT
# ============================================================

# All external Alpaca communication remains in:
#
# data_management/services/alpaca.py
#
#
# utils.py deliberately reuses this service rather than
# creating another API implementation.

from data_management.services.alpaca import (
    AlpacaServiceError,
    get_historical_bars,
)


# ============================================================
# 5. MARKET DATA CONSTANTS
# ============================================================

# Market Condition currently uses a 60-period moving average.
#
# Therefore fewer than 60 observations cannot produce the
# complete Market Condition analysis.

MARKET_CONDITION_MINIMUM_OBSERVATIONS = 60


# When MarketPulse needs to build an analytical dataset from
# Alpaca, request approximately one calendar year.
#
# A calendar year normally contains considerably more than
# 60 trading sessions while remaining a reasonable API
# request size.

ANALYSIS_HISTORY_LOOKBACK_DAYS = 365


# When sufficient history already exists, MarketPulse only
# needs to refresh a recent overlapping period rather than
# downloading the entire historical dataset again.

RECENT_REFRESH_LOOKBACK_DAYS = 30


# Daily historical market data is considered reasonably recent
# when the latest stored observation is within this many
# calendar days.
#
# Seven days handles weekends and many market holidays without
# repeatedly refreshing the API simply because today is not
# a trading session.

MARKET_DATA_STALE_AFTER_DAYS = 7


# ============================================================
# 6. SYMBOL NORMALISATION
# ============================================================

def _normalise_symbol(symbol):
    """
    Convert an asset symbol into MarketPulse's standard format.

    Examples:

        " spy "
            ↓
        "SPY"

        "msft"
            ↓
        "MSFT"
    """


    symbol = (
        str(
            symbol or ""
        )
        .strip()
        .upper()
    )


    if not symbol:

        raise ValueError(
            "A market symbol is required."
        )


    return symbol


# ============================================================
# 7. DATE NORMALISATION
# ============================================================

def _normalise_date_value(
    value,
    field_name,
):
    """
    Convert common date representations into datetime.date.

    Accepted:

    - datetime.date
    - datetime.datetime
    - ISO date string
    - ISO datetime string
    """


    if value is None:

        raise ValueError(
            f"{field_name} is required."
        )


    # --------------------------------------------------------
    # Datetime
    # --------------------------------------------------------

    if isinstance(
        value,
        datetime,
    ):

        return value.date()


    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    if isinstance(
        value,
        date,
    ):

        return value


    # --------------------------------------------------------
    # String
    # --------------------------------------------------------

    string_value = str(
        value
    ).strip()


    parsed_date = parse_date(
        string_value
    )


    if parsed_date is not None:

        return parsed_date


    parsed_datetime = parse_datetime(
        string_value
    )


    if parsed_datetime is not None:

        return parsed_datetime.date()


    raise ValueError(
        (
            f"MarketPulse could not interpret "
            f"{field_name}: {value}"
        )
    )


# ============================================================
# 8. PRICE DECIMAL HELPER
# ============================================================

def _to_price_decimal(value):
    """
    ========================================================
    CONVERT MARKET PRICE TO DECIMAL
    ========================================================

    MarketData stores OHLC prices using Decimal values.

    Financial values should not normally be persisted using
    raw floating-point values because binary floating-point
    arithmetic can introduce small representation errors.

    MarketPulse stores market prices to four decimal places.
    ========================================================
    """


    if value is None:

        raise ValueError(
            "Market price cannot be empty."
        )


    try:

        decimal_value = Decimal(
            str(
                value
            )
        )


        return decimal_value.quantize(

            Decimal(
                "0.0001"
            ),

            rounding=
                ROUND_HALF_UP,
        )


    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ) as error:

        raise ValueError(
            f"Invalid market price value: {value}"
        ) from error


# ============================================================
# 9. BAR VALUE HELPER
# ============================================================

def _get_bar_value(
    bar,
    *possible_keys,
):
    """
    ========================================================
    READ ONE VALUE FROM A MARKET BAR
    ========================================================

    The Alpaca service normally returns normalised names:

        open
        high
        low
        close
        volume
        timestamp


    This helper also accepts common alternative names:

        open_price
        high_price
        low_price
        close_price

    and Alpaca's short field names:

        o
        h
        l
        c
        v
        t


    This makes the persistence layer defensive without
    duplicating Alpaca API communication.
    ========================================================
    """


    for key in possible_keys:

        if key in bar:

            value = bar.get(
                key
            )


            if value is not None:

                return value


    return None


# ============================================================
# 10. MARKET BAR DATE HELPER
# ============================================================

def _get_bar_date(bar):
    """
    ========================================================
    CONVERT ALPACA TIMESTAMP TO DATE
    ========================================================

    MarketData stores one record per:

        symbol
        +
        date


    Alpaca may return:

        2026-09-01T04:00:00Z


    MarketPulse stores:

        2026-09-01
    ========================================================
    """


    value = _get_bar_value(

        bar,

        "date",

        "timestamp",

        "t",
    )


    if value is None:

        raise ValueError(
            (
                "Historical market bar does "
                "not contain a date."
            )
        )


    # --------------------------------------------------------
    # Already datetime
    # --------------------------------------------------------

    if isinstance(
        value,
        datetime,
    ):

        return value.date()


    # --------------------------------------------------------
    # Already date
    # --------------------------------------------------------

    if isinstance(
        value,
        date,
    ):

        return value


    # --------------------------------------------------------
    # Convert to string
    # --------------------------------------------------------

    value = str(
        value
    ).strip()


    # --------------------------------------------------------
    # ISO datetime
    # --------------------------------------------------------

    parsed_datetime = (
        parse_datetime(
            value
        )
    )


    if parsed_datetime is not None:

        return (
            parsed_datetime.date()
        )


    # --------------------------------------------------------
    # ISO date
    # --------------------------------------------------------

    parsed_date = (
        parse_date(
            value
        )
    )


    if parsed_date is not None:

        return parsed_date


    raise ValueError(
        (
            "MarketPulse could not interpret "
            f"historical bar date: {value}"
        )
    )


# ============================================================
# 11. NORMALISE ONE ALPACA BAR
# ============================================================

def _normalise_market_bar(bar):
    """
    ========================================================
    NORMALISE ALPACA OHLCV DATA
    ========================================================

    Convert an external market-data record into the structure
    expected by core.MarketData.


    OUTPUT:

    {
        "date": date,
        "open_price": Decimal,
        "high_price": Decimal,
        "low_price": Decimal,
        "close_price": Decimal,
        "volume": int,
    }
    ========================================================
    """


    if not isinstance(
        bar,
        dict,
    ):

        raise ValueError(
            (
                "Historical market bar must "
                "be a dictionary."
            )
        )


    # ========================================================
    # 11.1 READ PRICES
    # ========================================================

    open_price = _get_bar_value(

        bar,

        "open",

        "open_price",

        "o",
    )


    high_price = _get_bar_value(

        bar,

        "high",

        "high_price",

        "h",
    )


    low_price = _get_bar_value(

        bar,

        "low",

        "low_price",

        "l",
    )


    close_price = _get_bar_value(

        bar,

        "close",

        "close_price",

        "c",
    )


    volume = _get_bar_value(

        bar,

        "volume",

        "v",
    )


    # ========================================================
    # 11.2 REQUIRED OHLC VALIDATION
    # ========================================================

    if any(
        value is None
        for value in [
            open_price,
            high_price,
            low_price,
            close_price,
        ]
    ):

        raise ValueError(
            (
                "Historical Alpaca bar is missing "
                "one or more OHLC values."
            )
        )


    # ========================================================
    # 11.3 NORMALISE PRICES
    # ========================================================

    open_decimal = _to_price_decimal(
        open_price
    )


    high_decimal = _to_price_decimal(
        high_price
    )


    low_decimal = _to_price_decimal(
        low_price
    )


    close_decimal = _to_price_decimal(
        close_price
    )


    # ========================================================
    # 11.4 BASIC PRICE VALIDATION
    # ========================================================

    if any(
        price <= 0
        for price in [
            open_decimal,
            high_decimal,
            low_decimal,
            close_decimal,
        ]
    ):

        raise ValueError(
            (
                "Historical market prices "
                "must be greater than zero."
            )
        )


    # High should not be below low.
    if high_decimal < low_decimal:

        raise ValueError(
            (
                "Historical market bar contains "
                "a high price below its low price."
            )
        )


    # ========================================================
    # 11.5 VOLUME NORMALISATION
    # ========================================================

    try:

        volume = int(
            volume or 0
        )


    except (
        ValueError,
        TypeError,
        OverflowError,
    ):

        volume = 0


    # Negative market volume should never be stored.
    volume = max(
        0,
        volume,
    )


    # ========================================================
    # 11.6 RETURN NORMALISED BAR
    # ========================================================

    return {

        "date":
            _get_bar_date(
                bar
            ),

        "open_price":
            open_decimal,

        "high_price":
            high_decimal,

        "low_price":
            low_decimal,

        "close_price":
            close_decimal,

        "volume":
            volume,
    }


# ============================================================
# 12. STORED MARKET DATA STATUS
# ============================================================

def get_stored_market_data_status(
    symbol,
):
    """
    ========================================================
    GET STORED DATASET STATUS
    ========================================================

    Return information about the historical observations
    currently stored in core.MarketData for one symbol.


    Example:

    {
        "symbol": "SPY",
        "observation_count": 26,
        "earliest_date": date(...),
        "latest_date": date(...),
    }


    This helper is useful for:

    - Data tab
    - Market Condition
    - Risk
    - Backtesting
    - diagnostics
    ========================================================
    """


    symbol = _normalise_symbol(
        symbol
    )


    summary = (

        MarketData.objects

        .filter(
            symbol=symbol
        )

        .aggregate(

            observation_count=
                Count(
                    "pk"
                ),

            earliest_date=
                Min(
                    "date"
                ),

            latest_date=
                Max(
                    "date"
                ),
        )
    )


    return {

        "symbol":
            symbol,

        "observation_count":
            (
                summary[
                    "observation_count"
                ]
                or
                0
            ),

        "earliest_date":
            summary[
                "earliest_date"
            ],

        "latest_date":
            summary[
                "latest_date"
            ],
    }


# ============================================================
# 13. IMPORT ALPACA HISTORICAL DATA
# ============================================================

def import_alpaca_market_data(
    symbol,
    start_date,
    end_date,
    timeframe="1Day",
):
    """
    ========================================================
    IMPORT HISTORICAL ALPACA MARKET DATA
    ========================================================

    Main MarketPulse historical-data persistence function.


    WORKFLOW:

    User / feature requests data
            ↓
    import_alpaca_market_data()
            ↓
    get_historical_bars()
            ↓
    services/alpaca.py
            ↓
    Alpaca Historical Bars API
            ↓
    normalised OHLCV
            ↓
    MarketData.update_or_create()
            ↓
    PostgreSQL


    PARAMETERS:

    symbol
        Example:
            AAPL

    start_date
        First requested historical date.

    end_date
        Final requested historical date.

    timeframe
        Default:
            1Day


    RETURN:

        Number of valid market bars processed.


    IMPORTANT:

    MarketData.update_or_create() prevents repeated refreshes
    from creating duplicate rows for the same:

        symbol + date
    ========================================================
    """


    # ========================================================
    # 13.1 NORMALISE SYMBOL
    # ========================================================

    symbol = _normalise_symbol(
        symbol
    )


    # ========================================================
    # 13.2 NORMALISE DATES
    # ========================================================

    start_date = _normalise_date_value(

        start_date,

        "start date",
    )


    end_date = _normalise_date_value(

        end_date,

        "end date",
    )


    # ========================================================
    # 13.3 VALIDATE RANGE
    # ========================================================

    if start_date >= end_date:

        raise ValueError(
            (
                "The start date must be "
                "earlier than the end date."
            )
        )


    # ========================================================
    # 13.4 RETRIEVE ALPACA HISTORICAL BARS
    # ========================================================

    try:

        bars = get_historical_bars(

            symbol=
                symbol,

            start_date=
                start_date,

            end_date=
                end_date,

            timeframe=
                timeframe,
        )


    except AlpacaServiceError as error:

        raise ValueError(
            (
                f"Alpaca could not return historical "
                f"market data for {symbol}: {error}"
            )
        ) from error


    # ========================================================
    # 13.5 VERIFY DATA EXISTS
    # ========================================================

    if not bars:

        raise ValueError(
            (
                "No historical Alpaca market data "
                f"was returned for {symbol}."
            )
        )


    # ========================================================
    # 13.6 NORMALISE BARS BEFORE DATABASE TRANSACTION
    # ========================================================

    normalised_bars = []


    for bar in bars:

        try:

            normalised_bar = (
                _normalise_market_bar(
                    bar
                )
            )


        except ValueError:

            # A malformed provider row should not necessarily
            # invalidate every other valid observation returned
            # by the same historical request.
            continue


        # Keep only records inside the requested period.
        #
        # This also protects against unexpected provider rows.

        if (
            normalised_bar[
                "date"
            ]
            <
            start_date

            or

            normalised_bar[
                "date"
            ]
            >
            end_date
        ):

            continue


        normalised_bars.append(
            normalised_bar
        )


    if not normalised_bars:

        raise ValueError(
            (
                f"Alpaca returned data for {symbol}, "
                "but MarketPulse could not process any "
                "valid historical observations."
            )
        )


    # ========================================================
    # 13.7 STORE DATA IN DATABASE
    # ========================================================

    count = 0


    with transaction.atomic():


        for normalised_bar in normalised_bars:


            MarketData.objects.update_or_create(

                symbol=
                    symbol,

                date=
                    normalised_bar[
                        "date"
                    ],

                defaults={

                    "open_price":
                        normalised_bar[
                            "open_price"
                        ],

                    "high_price":
                        normalised_bar[
                            "high_price"
                        ],

                    "low_price":
                        normalised_bar[
                            "low_price"
                        ],

                    "close_price":
                        normalised_bar[
                            "close_price"
                        ],

                    "volume":
                        normalised_bar[
                            "volume"
                        ],
                },
            )


            count += 1


    return count


# ============================================================
# 14. PROVIDER-NEUTRAL IMPORT FUNCTION
# ============================================================

def import_market_data(
    symbol,
    start_date,
    end_date,
    timeframe="1Day",
):
    """
    ========================================================
    MARKETPULSE MARKET DATA IMPORT
    ========================================================

    Provider-neutral public entry point.

    Other MarketPulse modules should use:

        import_market_data()

    rather than calling:

        get_historical_bars()

    directly.


    CURRENT IMPLEMENTATION:

        import_market_data()
                ↓
        import_alpaca_market_data()
                ↓
        get_historical_bars()
                ↓
        Alpaca


    WHY PROVIDER-NEUTRAL?

    Views, tasks and analytical features should not need to
    know which external provider supplies the historical data.

    If the provider changes in the future, the rest of the
    MarketPulse application can continue using:

        import_market_data()
    ========================================================
    """


    return import_alpaca_market_data(

        symbol=
            symbol,

        start_date=
            start_date,

        end_date=
            end_date,

        timeframe=
            timeframe,
    )


# ============================================================
# 15. ENSURE MARKET DATA FOR ANALYSIS
# ============================================================

def ensure_market_data_for_analysis(
    symbol,
    minimum_observations=MARKET_CONDITION_MINIMUM_OBSERVATIONS,
    force_refresh=False,
):
    """
    ========================================================
    ENSURE SUFFICIENT HISTORICAL DATA FOR ANALYSIS
    ========================================================

    This is the function Market Condition should call BEFORE:

        identify_market_regime(symbol)


    PURPOSE:

    Market Condition needs enough historical observations to
    calculate the 60-period moving average.

    Instead of implementing another Alpaca request inside
    views.py, this function reuses:

        import_market_data()


    WORKFLOW:

    Selected ticker
            ↓
    Check MarketData
            ↓
    Enough observations?
            ↓
        NO
            ↓
    Fetch approximately one year from Alpaca
            ↓
    update_or_create MarketData
            ↓
    Count again
            ↓
    At least 60?
            ↓
        YES
            ↓
    Ready for identify_market_regime()


    EXISTING DATASET:

    If sufficient history already exists but it has become
    stale, only the recent period is refreshed.

    force_refresh=True can be used when the user explicitly
    clicks:

        Run Market Condition Analysis

    This refreshes recent data while avoiding an unnecessary
    full-year import.


    RETURNS:

    {
        "symbol": "SPY",
        "minimum_observations": 60,
        "observation_count_before": 26,
        "observation_count": 252,
        "earliest_date": ...,
        "latest_date": ...,
        "refreshed": True,
        "records_processed": 252,
        "analysis_ready": True,
    }
    ========================================================
    """


    # ========================================================
    # 15.1 NORMALISE SYMBOL
    # ========================================================

    symbol = _normalise_symbol(
        symbol
    )


    # ========================================================
    # 15.2 NORMALISE MINIMUM OBSERVATION REQUIREMENT
    # ========================================================

    try:

        minimum_observations = int(
            minimum_observations
        )


    except (
        TypeError,
        ValueError,
    ):

        minimum_observations = (
            MARKET_CONDITION_MINIMUM_OBSERVATIONS
        )


    minimum_observations = max(
        2,
        minimum_observations,
    )


    # ========================================================
    # 15.3 CURRENT STORED STATUS
    # ========================================================

    before = (
        get_stored_market_data_status(
            symbol
        )
    )


    observation_count_before = (
        before[
            "observation_count"
        ]
    )


    latest_stored_date = (
        before[
            "latest_date"
        ]
    )


    # ========================================================
    # 15.4 DETERMINE WHETHER MORE HISTORY IS REQUIRED
    # ========================================================

    needs_more_history = (

        observation_count_before
        <
        minimum_observations
    )


    # ========================================================
    # 15.5 DETERMINE WHETHER STORED DATA IS STALE
    # ========================================================

    today = (
        timezone.localdate()
    )


    if latest_stored_date is None:

        data_is_stale = True


    else:

        age_in_days = (

            today
            -
            latest_stored_date

        ).days


        data_is_stale = (

            age_in_days
            >
            MARKET_DATA_STALE_AFTER_DAYS
        )


    # ========================================================
    # 15.6 DETERMINE WHETHER TO CONTACT ALPACA
    # ========================================================

    should_refresh = (

        needs_more_history

        or

        data_is_stale

        or

        force_refresh
    )


    records_processed = 0


    # ========================================================
    # 15.7 REFRESH / EXTEND HISTORICAL DATASET
    # ========================================================

    if should_refresh:


        # ----------------------------------------------------
        # Not enough data:
        #
        # Request approximately one year so the analyzer has
        # substantially more than the 60 observations required
        # under normal circumstances.
        # ----------------------------------------------------

        if needs_more_history:

            refresh_start_date = (

                today

                -
                timedelta(
                    days=
                        ANALYSIS_HISTORY_LOOKBACK_DAYS
                )
            )


        # ----------------------------------------------------
        # Sufficient history already exists:
        #
        # Refresh only a recent overlapping window.
        #
        # update_or_create() means existing days are safely
        # updated rather than duplicated.
        # ----------------------------------------------------

        else:

            refresh_start_date = (

                today

                -
                timedelta(
                    days=
                        RECENT_REFRESH_LOOKBACK_DAYS
                )
            )


            # If the latest stored observation is older than
            # our standard refresh window, start slightly
            # before that observation so the missing period
            # can be recovered.

            if (
                latest_stored_date
                is not None

                and

                latest_stored_date
                <
                refresh_start_date
            ):

                refresh_start_date = (

                    latest_stored_date

                    -
                    timedelta(
                        days=7
                    )
                )


        # ----------------------------------------------------
        # Ensure the range contains at least one full day.
        # ----------------------------------------------------

        if refresh_start_date >= today:

            refresh_start_date = (

                today

                -
                timedelta(
                    days=1
                )
            )


        # ----------------------------------------------------
        # Reuse the EXISTING provider-neutral importer.
        #
        # IMPORTANT:
        #
        # No direct Alpaca request is implemented here.
        # ----------------------------------------------------

        records_processed = (
            import_market_data(

                symbol=
                    symbol,

                start_date=
                    refresh_start_date,

                end_date=
                    today,

                timeframe=
                    "1Day",
            )
        )


    # ========================================================
    # 15.8 RECHECK STORED DATA AFTER REFRESH
    # ========================================================

    after = (
        get_stored_market_data_status(
            symbol
        )
    )


    observation_count = (
        after[
            "observation_count"
        ]
    )


    # ========================================================
    # 15.9 ANALYSIS READINESS
    # ========================================================

    analysis_ready = (

        observation_count
        >=
        minimum_observations
    )


    # ========================================================
    # 15.10 RETURN STRUCTURED STATUS
    # ========================================================

    return {

        "symbol":
            symbol,

        "minimum_observations":
            minimum_observations,

        "observation_count_before":
            observation_count_before,

        "observation_count":
            observation_count,

        "earliest_date":
            after[
                "earliest_date"
            ],

        "latest_date":
            after[
                "latest_date"
            ],

        "refreshed":
            should_refresh,

        "records_processed":
            records_processed,

        "analysis_ready":
            analysis_ready,
    }


# ============================================================
# 16. MARKET CONDITION DATA HELPER
# ============================================================

def prepare_market_condition_data(
    symbol,
    force_refresh=False,
):
    """
    ========================================================
    PREPARE DATA FOR MARKET CONDITION
    ========================================================

    Convenience wrapper specifically for Market Condition.

    This keeps the minimum-observation requirement in one
    central location instead of repeating:

        60

    throughout multiple views.


    USE FROM data_management/views.py:

        data_status = prepare_market_condition_data(
            selected_symbol,
            force_refresh=True,
        )

        if data_status["analysis_ready"]:
            regime = identify_market_regime(
                selected_symbol
            )


    This function does NOT run the analytical model itself.

    Responsibility remains separated:

        utils.py
            = obtain + store data

        analysis_tools/analyzers.py
            = analyse stored data
    ========================================================
    """


    return ensure_market_data_for_analysis(

        symbol=
            symbol,

        minimum_observations=
            MARKET_CONDITION_MINIMUM_OBSERVATIONS,

        force_refresh=
            force_refresh,
    )


# ============================================================
# 17. TEMPORARY LEGACY COMPATIBILITY
# ============================================================

def import_yahoo_finance_data(
    symbol,
    start_date,
    end_date,
):
    """
    ========================================================
    TEMPORARY COMPATIBILITY WRAPPER
    ========================================================

    IMPORTANT:

    Despite this OLD function name, this function does NOT
    contact Yahoo Finance.

    It redirects to MarketPulse's current provider-neutral
    importer:

        import_market_data()
            ↓
        Alpaca


    WHY KEEP IT TEMPORARILY?

    Existing files may still contain:

        from data_management.utils import (
            import_yahoo_finance_data
        )

    Removing this compatibility function immediately could
    create ImportError exceptions in older code.

    Once the whole project uses:

        import_market_data()

    this wrapper can safely be removed.
    ========================================================
    """


    return import_market_data(

        symbol=
            symbol,

        start_date=
            start_date,

        end_date=
            end_date,

        timeframe=
            "1Day",
    )


# ============================================================
# 18. PERIOD → DATE RANGE HELPER
# ============================================================

def _period_to_dates(period):
    """
    ========================================================
    CONVERT SIMPLE PERIOD TO START / END DATES
    ========================================================

    Preserves compatibility with get_latest_data().


    EXAMPLES:

        5d
        1mo
        3mo
        6mo
        1y
        2y
        5y
    ========================================================
    """


    end_date = (
        timezone.localdate()
    )


    period_days = {

        "5d":
            5,

        "1mo":
            31,

        "3mo":
            93,

        "6mo":
            186,

        "1y":
            366,

        "2y":
            732,

        "5y":
            1830,
    }


    days = (
        period_days.get(
            period,
            31,
        )
    )


    start_date = (

        end_date

        -
        timedelta(
            days=
                days
        )
    )


    return (
        start_date,
        end_date,
    )


# ============================================================
# 19. GET RECENT ALPACA DATA
# ============================================================

def get_latest_data(
    symbol,
    period="1mo",
):
    """
    ========================================================
    GET RECENT HISTORICAL MARKET DATA
    ========================================================

    Return recent Alpaca historical market data without
    persisting it.


    OUTPUT:

    [
        {
            "date": "2026-08-01",
            "open": 100.00,
            "high": 105.00,
            "low": 99.00,
            "close": 104.00,
            "volume": 1000000
        }
    ]


    IMPORTANT:

    This function is useful when a feature needs a temporary
    historical series.

    If data must become part of MarketPulse's persistent
    analytical dataset, use:

        import_market_data()

    or:

        ensure_market_data_for_analysis()

    instead.
    ========================================================
    """


    try:

        symbol = _normalise_symbol(
            symbol
        )


    except ValueError:

        return []


    start_date, end_date = (
        _period_to_dates(
            period
        )
    )


    # ========================================================
    # 19.1 REQUEST ALPACA DATA THROUGH SERVICE LAYER
    # ========================================================

    try:

        bars = get_historical_bars(

            symbol=
                symbol,

            start_date=
                start_date,

            end_date=
                end_date,

            timeframe=
                "1Day",
        )


    except AlpacaServiceError:

        return []


    if not bars:

        return []


    # ========================================================
    # 19.2 NORMALISE RESULT
    # ========================================================

    results = []


    for bar in bars:


        try:

            normalised_bar = (
                _normalise_market_bar(
                    bar
                )
            )


        except ValueError:

            # Skip malformed provider records.
            continue


        results.append(
            {

                "date":
                    normalised_bar[
                        "date"
                    ].isoformat(),

                "open":
                    float(
                        normalised_bar[
                            "open_price"
                        ]
                    ),

                "high":
                    float(
                        normalised_bar[
                            "high_price"
                        ]
                    ),

                "low":
                    float(
                        normalised_bar[
                            "low_price"
                        ]
                    ),

                "close":
                    float(
                        normalised_bar[
                            "close_price"
                        ]
                    ),

                "volume":
                    normalised_bar[
                        "volume"
                    ],
            }
        )


    # ========================================================
    # 19.3 CHRONOLOGICAL ORDER
    # ========================================================

    results.sort(
        key=lambda item:
            item[
                "date"
            ]
    )


    return results