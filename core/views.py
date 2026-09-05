"""
============================================================
CORE - HOME AND DASHBOARD VIEWS
============================================================

FRAMEWORK MAPPING:

MarketPulse
    ↓
marketpulse/urls.py
    ↓
core/views.py
    ↓
Dashboard
    ↓
PostgreSQL + Alpaca


DASHBOARD PURPOSE:

The Dashboard provides a quick overview of:

1. Current market information
2. Strategy activity
3. Backtest performance
4. Historical data health
5. Market-condition analysis
6. Active alerts


DATA SOURCES:

PostgreSQL
    ↓
Strategies
Backtests
Historical MarketData
Alerts
Market Regime results

Alpaca
    ↓
SPY
QQQ
DIA
IWM
Latest market snapshots


IMPORTANT:

The Dashboard is an overview.

Detailed analysis remains inside:

Data
    → Historical Data
    → Market Condition

Strategies
    → Backtesting
    → Strategy Robustness

Risk
    → Trade Risk Planner
    → Stress Testing


LIVE DASHBOARD DESIGN:

The first server-rendered page can include a current
market snapshot.

Later, JavaScript / React will call MarketPulse API
endpoints periodically so market information and the
market chart can refresh without reloading the page.

============================================================
"""


# ============================================================
# 1. PYTHON IMPORTS
# ============================================================

# Python's logging module allows unexpected provider failures
# to be recorded without crashing the complete Dashboard.
import logging


# ============================================================
# 2. DJANGO IMPORTS
# ============================================================

# login_required prevents unauthenticated users from opening
# the private MarketPulse Dashboard.
from django.contrib.auth.decorators import login_required


# Avg is used to calculate the average win rate across the
# current user's backtests.
from django.db.models import Avg


# render returns a Django template together with context data.
from django.shortcuts import render


# ============================================================
# 3. CORE MODEL IMPORTS
# ============================================================

# These models provide the main stored information displayed
# on the Dashboard.
from .models import (
    Alert,
    Backtest,
    MarketData,
    Strategy,
)


# ============================================================
# 4. MARKET CONDITION IMPORT
# ============================================================

# analysis_tools remains installed as MarketPulse's internal
# quantitative analytics layer.
#
# The old Analysis navigation tab can therefore disappear
# while these database models remain reusable elsewhere.
from analysis_tools.models import MarketRegime


# ============================================================
# 5. ALPACA SERVICE IMPORTS
# ============================================================

# Alpaca credentials remain on the Django server.
#
# Browser
#     ↓
# Django
#     ↓
# MarketPulse Alpaca service
#     ↓
# Alpaca API
#
# The API keys are therefore never inserted into HTML or
# browser-side JavaScript.
from data_management.services.alpaca import (
    AlpacaServiceError,
    get_stock_snapshot,
)


# ============================================================
# 6. LOGGER
# ============================================================

# A module-level logger gives us a safe place to record
# unexpected external-provider problems.
logger = logging.getLogger(__name__)


# ============================================================
# 7. DASHBOARD MARKET BENCHMARKS
# ============================================================

# These benchmark ETFs provide a simple overview of several
# important areas of the US equity market.
#
# SPY:
#     Broad large-cap US equities
#
# QQQ:
#     Nasdaq-100 / technology-heavy equities
#
# DIA:
#     Dow Jones large-cap equities
#
# IWM:
#     US small-cap equities
DASHBOARD_MARKET_SYMBOLS = (
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
)


# ============================================================
# 8. SAFE FLOAT CONVERSION
# ============================================================

def _to_float(
    value,
    default=None,
):
    """
    ------------------------------------------------------------
    CONVERT A VALUE TO FLOAT SAFELY
    ------------------------------------------------------------

    Database values and external API responses may contain:

    - Decimal
    - integer
    - float
    - numeric string
    - None

    Dashboard rendering should not fail simply because one
    provider value cannot be converted.
    ------------------------------------------------------------
    """

    if value is None:

        return default


    try:

        return float(value)


    except (
        TypeError,
        ValueError,
    ):

        return default


# ============================================================
# 9. BUILD ONE MARKET CARD
# ============================================================

def _build_market_card(
    symbol,
):
    """
    ------------------------------------------------------------
    BUILD ONE ALPACA MARKET SUMMARY CARD
    ------------------------------------------------------------

    Retrieves a normalised Alpaca stock snapshot for one
    benchmark symbol.

    External API failure does not cause the complete Dashboard
    to fail. Instead, an unavailable card is returned.
    ------------------------------------------------------------
    """


    # ========================================================
    # 9.1 DEFAULT / UNAVAILABLE STATE
    # ========================================================

    card = {

        "symbol":
            symbol,

        "latest_price":
            None,

        "previous_close":
            None,

        "daily_change":
            None,

        "daily_change_pct":
            None,

        "day_open":
            None,

        "day_high":
            None,

        "day_low":
            None,

        "day_volume":
            None,

        "feed":
            None,

        "timestamp":
            None,

        "available":
            False,

    }


    # ========================================================
    # 9.2 REQUEST ALPACA SNAPSHOT
    # ========================================================

    try:

        snapshot = (
            get_stock_snapshot(
                symbol
            )
            or
            {}
        )


        # The MarketPulse Alpaca service returns a normalised
        # daily_bar dictionary.
        daily_bar = (
            snapshot.get(
                "daily_bar"
            )
            or
            {}
        )


        # ====================================================
        # 9.3 PRICE INFORMATION
        # ====================================================

        latest_price = _to_float(
            snapshot.get(
                "latest_price"
            )
        )


        previous_close = _to_float(
            snapshot.get(
                "previous_close"
            )
        )


        daily_change = _to_float(
            snapshot.get(
                "daily_change"
            )
        )


        daily_change_pct = _to_float(
            snapshot.get(
                "daily_change_pct"
            )
        )


        # ====================================================
        # 9.4 CALCULATE CHANGE WHEN NECESSARY
        # ====================================================

        if (
            daily_change is None
            and
            latest_price is not None
            and
            previous_close is not None
        ):

            daily_change = (
                latest_price
                -
                previous_close
            )


        if (
            daily_change_pct is None
            and
            latest_price is not None
            and
            previous_close is not None
            and
            previous_close != 0
        ):

            daily_change_pct = (
                (
                    latest_price
                    -
                    previous_close
                )
                /
                previous_close
                *
                100
            )


        # ====================================================
        # 9.5 POPULATE SUCCESSFUL CARD
        # ====================================================

        card.update(
            {

                "latest_price":
                    latest_price,

                "previous_close":
                    previous_close,

                "daily_change":
                    daily_change,

                "daily_change_pct":
                    daily_change_pct,

                "day_open":
                    _to_float(
                        daily_bar.get(
                            "open"
                        )
                    ),

                "day_high":
                    _to_float(
                        daily_bar.get(
                            "high"
                        )
                    ),

                "day_low":
                    _to_float(
                        daily_bar.get(
                            "low"
                        )
                    ),

                "day_volume":
                    _to_float(
                        daily_bar.get(
                            "volume"
                        )
                    ),

                "feed":
                    snapshot.get(
                        "feed"
                    ),

                "timestamp":
                    snapshot.get(
                        "latest_trade_timestamp"
                    ),

                "available":
                    latest_price is not None,

            }
        )


    # ========================================================
    # 9.6 EXPECTED ALPACA FAILURE
    # ========================================================

    except AlpacaServiceError as exc:

        # External market-data failure should not make the
        # complete MarketPulse Dashboard unavailable.
        logger.warning(
            "Alpaca snapshot unavailable for %s: %s",
            symbol,
            exc,
        )


    # ========================================================
    # 9.7 UNEXPECTED FAILURE
    # ========================================================

    except Exception:

        # We still keep the Dashboard usable, but unlike a bare
        # 'pass', logging records the unexpected problem so it
        # can be diagnosed during development.
        logger.exception(
            "Unexpected error while building market card for %s.",
            symbol,
        )


    return card


# ============================================================
# 10. BUILD MARKET OVERVIEW
# ============================================================

def _build_market_overview():
    """
    ------------------------------------------------------------
    BUILD ALL DASHBOARD MARKET CARDS
    ------------------------------------------------------------

    Returns one dictionary for each benchmark configured in
    DASHBOARD_MARKET_SYMBOLS.

    Alpaca snapshot caching is handled by the Alpaca service,
    so repeated requests within the configured cache period do
    not necessarily create another external API request.
    ------------------------------------------------------------
    """

    return [

        _build_market_card(
            symbol
        )

        for symbol in DASHBOARD_MARKET_SYMBOLS

    ]


# ============================================================
# 11. HOME PAGE
# ============================================================

def home(
    request,
):
    """
    Display the public MarketPulse home page.
    """

    return render(
        request,
        "home.html",
    )


# ============================================================
# 12. DASHBOARD
# ============================================================

@login_required
def dashboard(
    request,
):
    """
    ------------------------------------------------------------
    MARKETPULSE DASHBOARD
    ------------------------------------------------------------

    The Dashboard combines:

    - User strategy statistics
    - User backtest statistics
    - Historical market-data health
    - Latest market-condition analysis
    - Active user alerts
    - Current Alpaca benchmark snapshots

    Detailed tools remain in their specialist tabs.
    ------------------------------------------------------------
    """


    # ========================================================
    # 12.1 USER STRATEGIES
    # ========================================================

    strategies = (
        Strategy.objects
        .filter(
            user=request.user
        )
    )


    active_strategy_count = (
        strategies
        .filter(
            is_active=True
        )
        .count()
    )


    # ========================================================
    # 12.2 USER BACKTESTS
    # ========================================================

    backtests = (
        Backtest.objects
        .filter(
            strategy__user=request.user
        )
        .select_related(
            "strategy"
        )
        .order_by(
            "-created_at"
        )
    )


    backtest_count = (
        backtests.count()
    )


    latest_backtest = (
        backtests.first()
    )


    # ========================================================
    # 12.3 AVERAGE WIN RATE
    # ========================================================

    average_win_rate = (
        backtests.aggregate(
            value=Avg(
                "win_rate"
            )
        )["value"]
        or
        0
    )


    # Existing MarketPulse backtests store win_rate as a
    # decimal proportion.
    #
    # Example:
    #
    # 0.584
    #
    # becomes:
    #
    # 58.4%
    average_win_rate_pct = (
        float(
            average_win_rate
        )
        *
        100
    )


    # ========================================================
    # 12.4 HISTORICAL MARKET-DATA HEALTH
    # ========================================================

    # Total number of stored OHLCV observations.
    market_data_count = (
        MarketData.objects.count()
    )


    # Number of unique assets currently stored.
    market_symbol_count = (
        MarketData.objects
        .values(
            "symbol"
        )
        .distinct()
        .count()
    )


    # Most recent historical observation stored in PostgreSQL.
    latest_market_record = (
        MarketData.objects
        .order_by(
            "-date",
            "-id",
        )
        .values(
            "symbol",
            "date",
        )
        .first()
    )


    latest_market_symbol = (
        latest_market_record[
            "symbol"
        ]
        if latest_market_record
        else None
    )


    latest_market_date = (
        latest_market_record[
            "date"
        ]
        if latest_market_record
        else None
    )


    # ========================================================
    # 12.5 ACTIVE ALERTS
    # ========================================================

    # IMPORTANT:
    #
    # This view READS alerts.
    #
    # It does not yet generate alerts.
    #
    # Alert generation and resolution will be implemented as
    # a separate MarketPulse service so refreshing Dashboard
    # cannot accidentally create duplicate alert records.
    active_alerts = (
        Alert.objects
        .filter(
            user=request.user,
            is_active=True,
        )
        .order_by(
            "-created_at"
        )
    )


    active_alert_count = (
        active_alerts.count()
    )


    dashboard_alerts = (
        active_alerts[:5]
    )


    # ========================================================
    # 12.6 LATEST MARKET CONDITION
    # ========================================================

    # MarketRegime is global market analysis rather than
    # user-specific information, so we retrieve the most recent
    # stored regime result.
    latest_market_regime = (
        MarketRegime.objects
        .order_by(
            "-date",
            "-created_at",
        )
        .first()
    )


    # ========================================================
    # 12.7 CURRENT ALPACA MARKET OVERVIEW
    # ========================================================

    market_overview = (
        _build_market_overview()
    )


    # The provider is considered available if at least one
    # benchmark returned a valid latest price.
    alpaca_connected = any(

        card.get(
            "available",
            False,
        )

        for card in market_overview

    )


    # ========================================================
    # 12.8 DETECT ACTIVE MARKET-DATA FEED
    # ========================================================

    alpaca_feed = next(
        (

            card.get(
                "feed"
            )

            for card in market_overview

            if (
                card.get(
                    "available"
                )
                and
                card.get(
                    "feed"
                )
            )

        ),
        None,
    )


    # ========================================================
    # 12.9 LATEST ALPACA TIMESTAMP
    # ========================================================

    # For now we use the first successfully returned market
    # timestamp.
    #
    # Later, the live Dashboard API will return its own explicit
    # server update timestamp for automatic browser refresh.
    market_last_updated = next(
        (

            card.get(
                "timestamp"
            )

            for card in market_overview

            if card.get(
                "timestamp"
            )

        ),
        None,
    )


    # ========================================================
    # 12.10 DATA HEALTH STATUS
    # ========================================================

    # These simple flags allow the future template to show a
    # clear Data Health section.
    historical_data_available = (
        market_data_count > 0
    )


    market_symbols_available = (
        market_symbol_count > 0
    )


    # ========================================================
    # 12.11 TEMPLATE CONTEXT
    # ========================================================

    context = {


        # ----------------------------------------------------
        # STRATEGIES
        # ----------------------------------------------------

        "active_strategy_count":
            active_strategy_count,


        # ----------------------------------------------------
        # BACKTESTS
        # ----------------------------------------------------

        "backtest_count":
            backtest_count,

        "avg_win_rate":
            average_win_rate_pct,

        "latest_backtest":
            latest_backtest,


        # ----------------------------------------------------
        # HISTORICAL DATA
        # ----------------------------------------------------

        "market_data_count":
            market_data_count,

        "market_symbol_count":
            market_symbol_count,

        "latest_market_symbol":
            latest_market_symbol,

        "latest_market_date":
            latest_market_date,

        "historical_data_available":
            historical_data_available,

        "market_symbols_available":
            market_symbols_available,


        # ----------------------------------------------------
        # ALERTS
        # ----------------------------------------------------

        "alerts":
            dashboard_alerts,

        "active_alert_count":
            active_alert_count,


        # ----------------------------------------------------
        # MARKET CONDITION
        # ----------------------------------------------------

        "latest_market_regime":
            latest_market_regime,


        # ----------------------------------------------------
        # ALPACA MARKET OVERVIEW
        # ----------------------------------------------------

        "market_overview":
            market_overview,

        "alpaca_connected":
            alpaca_connected,

        "alpaca_feed":
            alpaca_feed,

        "market_last_updated":
            market_last_updated,

    }


    # ========================================================
    # 12.12 RENDER DASHBOARD
    # ========================================================

    return render(
        request,
        "dashboard.html",
        context,
    )