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
Stress Testing


PURPOSE:

This module is responsible for taking historical market data
retrieved through the Alpaca service layer and storing it in
MarketPulse's MarketData database table.

The old implementation used yfinance directly.

The new implementation deliberately separates responsibilities:

data_management/services/alpaca.py
    = communicates with the external Alpaca API

data_management/utils.py
    = validates and stores the returned market data

core.MarketData
    = persistent historical OHLCV storage


This means other MarketPulse features do NOT need to contact
Alpaca independently.

They can simply read the historical data stored in PostgreSQL.

============================================================
"""


# ============================================================
# 1. PYTHON IMPORTS
# ============================================================

from datetime import date, datetime, timedelta

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)


# ============================================================
# 2. DJANGO IMPORTS
# ============================================================

from django.db import transaction

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

# All communication with the external Alpaca API should remain
# inside the Alpaca service layer.
#
# utils.py should not contain:
#
# - API keys
# - Alpaca authentication headers
# - external HTTP request code
#
# This is a cleaner service-oriented architecture.
from data_management.services.alpaca import (
    AlpacaServiceError,
    get_historical_bars,
)


# ============================================================
# 5. PRICE DECIMAL HELPER
# ============================================================

def _to_price_decimal(value):
    """
    ------------------------------------------------------------
    CONVERT MARKET PRICE TO DECIMAL
    ------------------------------------------------------------

    MarketData stores OHLC prices using Decimal values.

    Financial prices should not normally be stored using raw
    floating-point values because floating-point arithmetic can
    introduce small representation errors.

    MarketPulse stores prices to four decimal places.
    ------------------------------------------------------------
    """


    if value is None:

        raise ValueError(
            "Market price cannot be empty."
        )


    try:

        decimal_value = Decimal(
            str(value)
        )


        return decimal_value.quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP,
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
# 6. BAR VALUE HELPER
# ============================================================

def _get_bar_value(
    bar,
    *possible_keys,
):
    """
    ------------------------------------------------------------
    READ ONE VALUE FROM A MARKET BAR
    ------------------------------------------------------------

    The Alpaca service should normally return normalised names:

        open
        high
        low
        close
        volume
        timestamp

    This helper also accepts Alpaca's shorter raw field names:

        o
        h
        l
        c
        v
        t

    This makes the importer more defensive while the Alpaca
    integration is being developed.
    ------------------------------------------------------------
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
# 7. MARKET BAR DATE HELPER
# ============================================================

def _get_bar_date(bar):
    """
    ------------------------------------------------------------
    CONVERT ALPACA TIMESTAMP TO A DATE
    ------------------------------------------------------------

    MarketData stores one record per:

        symbol + date

    Alpaca can return timestamps such as:

        2026-09-01T04:00:00Z

    MarketPulse converts these into:

        2026-09-01
    ------------------------------------------------------------
    """


    value = _get_bar_value(

        bar,

        "date",

        "timestamp",

        "t",
    )


    if value is None:

        raise ValueError(
            "Historical market bar does not contain a date."
        )


    # --------------------------------------------------------
    # Already a datetime
    # --------------------------------------------------------

    if isinstance(
        value,
        datetime,
    ):

        return value.date()


    # --------------------------------------------------------
    # Already a date
    # --------------------------------------------------------

    if isinstance(
        value,
        date,
    ):

        return value


    # --------------------------------------------------------
    # String timestamp / date
    # --------------------------------------------------------

    value = str(
        value
    )


    parsed_datetime = (
        parse_datetime(
            value
        )
    )


    if parsed_datetime is not None:

        return (
            parsed_datetime.date()
        )


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
# 8. NORMALISE ONE ALPACA BAR
# ============================================================

def _normalise_market_bar(bar):
    """
    ------------------------------------------------------------
    NORMALISE ALPACA OHLCV DATA
    ------------------------------------------------------------

    Converts an Alpaca market-data record into the structure
    expected by core.MarketData.

    Output:

    {
        "date": date,
        "open_price": Decimal,
        "high_price": Decimal,
        "low_price": Decimal,
        "close_price": Decimal,
        "volume": int,
    }
    ------------------------------------------------------------
    """


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


    # --------------------------------------------------------
    # Required OHLC validation
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Volume normalisation
    # --------------------------------------------------------

    try:

        volume = int(
            volume or 0
        )


    except (
        ValueError,
        TypeError,
    ):

        volume = 0


    return {

        "date":
            _get_bar_date(
                bar
            ),

        "open_price":
            _to_price_decimal(
                open_price
            ),

        "high_price":
            _to_price_decimal(
                high_price
            ),

        "low_price":
            _to_price_decimal(
                low_price
            ),

        "close_price":
            _to_price_decimal(
                close_price
            ),

        "volume":
            volume,
    }


# ============================================================
# 9. IMPORT ALPACA HISTORICAL DATA
# ============================================================

def import_alpaca_market_data(
    symbol,
    start_date,
    end_date,
    timeframe="1Day",
):
    """
    ------------------------------------------------------------
    IMPORT HISTORICAL ALPACA MARKET DATA
    ------------------------------------------------------------

    Main MarketPulse historical-data importer.

    Workflow:

    User selects symbol and dates
            ↓
    Data tab
            ↓
    import_alpaca_market_data()
            ↓
    get_historical_bars()
            ↓
    Alpaca Historical Bars API
            ↓
    OHLCV records
            ↓
    MarketData.update_or_create()
            ↓
    PostgreSQL


    Parameters:

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


    Returns:

        Number of historical observations processed.
    ------------------------------------------------------------
    """


    # ========================================================
    # 9.1 NORMALISE SYMBOL
    # ========================================================

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )


    if not symbol:

        raise ValueError(
            "A market symbol is required."
        )


    # ========================================================
    # 9.2 VALIDATE DATE RANGE
    # ========================================================

    if not start_date:

        raise ValueError(
            "A start date is required."
        )


    if not end_date:

        raise ValueError(
            "An end date is required."
        )


    if start_date >= end_date:

        raise ValueError(
            (
                "The start date must be "
                "earlier than the end date."
            )
        )


    # ========================================================
    # 9.3 RETRIEVE ALPACA HISTORICAL BARS
    # ========================================================

    try:

        bars = get_historical_bars(

            symbol=symbol,

            start_date=start_date,

            end_date=end_date,

            timeframe=timeframe,
        )


    except AlpacaServiceError as error:

        raise ValueError(
            (
                f"Alpaca could not return historical "
                f"market data for {symbol}: {error}"
            )
        ) from error


    # ========================================================
    # 9.4 VERIFY DATA EXISTS
    # ========================================================

    if not bars:

        raise ValueError(
            (
                "No historical Alpaca market data "
                f"was returned for {symbol}."
            )
        )


    # ========================================================
    # 9.5 STORE DATA IN POSTGRESQL
    # ========================================================

    count = 0


    # transaction.atomic() means that the historical import
    # behaves as one database transaction.
    #
    # If a serious error occurs halfway through the operation,
    # Django can roll the transaction back rather than leaving
    # a partially processed dataset.
    with transaction.atomic():


        for bar in bars:


            normalised_bar = (
                _normalise_market_bar(
                    bar
                )
            )


            MarketData.objects.update_or_create(

                symbol=symbol,

                date=normalised_bar[
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
# 10. PROVIDER-NEUTRAL IMPORT FUNCTION
# ============================================================

def import_market_data(
    symbol,
    start_date,
    end_date,
    timeframe="1Day",
):
    """
    ------------------------------------------------------------
    MARKETPULSE MARKET DATA IMPORT
    ------------------------------------------------------------

    Provider-neutral entry point used by the rest of
    MarketPulse.

    Alpaca is now the PRIMARY historical-data provider.

    Keeping the public function name provider-neutral means
    that views and background tasks do not need to know how
    Alpaca itself works.

    This also makes the architecture easier to extend later.
    ------------------------------------------------------------
    """


    return import_alpaca_market_data(

        symbol=symbol,

        start_date=start_date,

        end_date=end_date,

        timeframe=timeframe,
    )


# ============================================================
# 11. TEMPORARY LEGACY COMPATIBILITY
# ============================================================

def import_yahoo_finance_data(
    symbol,
    start_date,
    end_date,
):
    """
    ------------------------------------------------------------
    TEMPORARY COMPATIBILITY WRAPPER
    ------------------------------------------------------------

    IMPORTANT:

    Despite the OLD function name, this function NO LONGER
    retrieves anything from Yahoo Finance.

    It now redirects to the Alpaca importer.

    Why keep it temporarily?

    Some existing MarketPulse files may still contain:

        from data_management.utils import (
            import_yahoo_finance_data
        )

    Removing the function immediately could therefore break
    tasks.py or another existing import.

    After tasks.py and views.py are updated to use:

        import_market_data()

    this compatibility function should be removed completely
    so that no Yahoo-specific naming remains in the final
    project.
    ------------------------------------------------------------
    """


    return import_market_data(

        symbol=symbol,

        start_date=start_date,

        end_date=end_date,

        timeframe="1Day",
    )


# ============================================================
# 12. PERIOD → DATE RANGE HELPER
# ============================================================

def _period_to_dates(period):
    """
    ------------------------------------------------------------
    CONVERT SIMPLE PERIOD TO START / END DATES
    ------------------------------------------------------------

    Preserves compatibility with the original get_latest_data()
    function.

    Examples:

        5d
        1mo
        3mo
        6mo
        1y
        2y
    ------------------------------------------------------------
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
            days=days
        )
    )


    return (
        start_date,
        end_date,
    )


# ============================================================
# 13. GET RECENT ALPACA DATA
# ============================================================

def get_latest_data(
    symbol,
    period="1mo",
):
    """
    ------------------------------------------------------------
    GET RECENT HISTORICAL MARKET DATA
    ------------------------------------------------------------

    This function preserves the same output structure used by
    the previous Yahoo implementation:

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

    The difference is that the underlying historical provider
    is now Alpaca rather than yfinance.
    ------------------------------------------------------------
    """


    symbol = (
        str(symbol)
        .strip()
        .upper()
    )


    if not symbol:

        return []


    start_date, end_date = (
        _period_to_dates(
            period
        )
    )


    try:

        bars = get_historical_bars(

            symbol=symbol,

            start_date=start_date,

            end_date=end_date,

            timeframe="1Day",
        )


    except AlpacaServiceError:

        return []


    if not bars:

        return []


    results = []


    for bar in bars:


        try:

            normalised_bar = (
                _normalise_market_bar(
                    bar
                )
            )


        except ValueError:

            # Skip malformed external records rather than
            # failing the entire latest-data request.
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


    # Keep output ordered chronologically.
    results.sort(
        key=lambda item:
            item["date"]
    )


    return results