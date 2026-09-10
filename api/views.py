"""
============================================================
MARKETPULSE - API ENDPOINTS
============================================================

FRAMEWORK MAPPING:

Browser / JavaScript / React
        ↓
Django REST Framework API
        ↓
Django ORM / Risk Calculator / MATLAB / Alpaca Service
        ↓
JSON Response


THIS API LAYER PROVIDES ACCESS TO:

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
# ============================================================

from django.conf import settings

from django.db.models import Avg

from django.utils import timezone


# ============================================================
# 2. DJANGO REST FRAMEWORK IMPORTS
# ============================================================

from rest_framework import (
    status,
    viewsets,
)

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)

from rest_framework.response import Response


# ============================================================
# 3. CORE MARKETPULSE IMPORTS
# ============================================================

from core.models import (
    Alert,
    Backtest,
    MarketData,
    Strategy,
)

from core.matlab_bridge import (
    run_matlab_operation,
)

from core.exceptions import (
    MatlabUnavailable,
)


# ============================================================
# 4. INTERNAL ANALYTICS IMPORTS
# ============================================================

# analysis_tools is an internal analytical layer.
#
# Detailed market-condition analysis belongs under the Data
# workflow while the Dashboard displays the latest result.

from analysis_tools.models import (
    MarketRegime,
)


# ============================================================
# 5. RISK MANAGEMENT IMPORTS
# ============================================================

from risk_management.calculators import (
    calculate_position_size,
    calculate_stop_loss,
)


# ============================================================
# 6. API SERIALIZERS
# ============================================================

from .serializers import (
    BacktestSerializer,
    MarketDataSerializer,
    StrategySerializer,
)


# ============================================================
# 7. ALPACA SERVICE IMPORTS
# ============================================================

# All direct communication with Alpaca remains inside the
# dedicated data-management service layer.
#
# This API layer never constructs Alpaca credentials itself.

from data_management.services.alpaca import (
    AlpacaServiceError,
    get_asset,
    get_chart_history,
    get_market_clock,
    get_stock_snapshot,
    search_assets,
)


# ============================================================
# 8. DASHBOARD CONFIGURATION
# ============================================================

DASHBOARD_BENCHMARKS = {

    "SPY":
        "S&P 500 ETF",

    "QQQ":
        "Nasdaq-100 ETF",

    "DIA":
        "Dow Jones ETF",

    "IWM":
        "Russell 2000 ETF",

}


# Maximum number of chart observations that can be requested.
DASHBOARD_MAX_CHART_ROWS = 250


# Default number of chart observations requested.
DASHBOARD_DEFAULT_CHART_ROWS = 60


# Browser automatic refresh interval.
DASHBOARD_REFRESH_SECONDS = 60


# ============================================================
# 8.1 SUPPORTED INTERACTIVE CHART PERIODS
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

SUPPORTED_CHART_PERIODS = {
    "1D",
    "5D",
    "1M",
    "3M",
}


# ============================================================
# 9. GENERAL DASHBOARD HELPERS
# ============================================================


# ============================================================
# 9.1 SAFE FLOAT CONVERSION
# ============================================================

def _safe_float(
    value,
):
    """
    Convert numeric values into JSON-friendly floats.

    Missing or invalid values return None.
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
# 9.2 CALCULATE PRICE CHANGE
# ============================================================

def _calculate_price_change(
    latest_price,
    previous_close,
):
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

    latest_price = (
        _safe_float(
            latest_price
        )
    )


    previous_close = (
        _safe_float(
            previous_close
        )
    )


    if (
        latest_price is None
        or
        previous_close is None
        or
        previous_close == 0
    ):

        return (
            None,
            None,
        )


    change = (
        latest_price
        -
        previous_close
    )


    change_percentage = (
        change
        /
        previous_close
        *
        100
    )


    return (
        change,
        change_percentage,
    )


# ============================================================
# 9.3 NORMALISE ONE ALPACA SNAPSHOT
# ============================================================

def _normalise_dashboard_snapshot(
    symbol,
    label,
    snapshot,
):
    """
    Convert one normalised Alpaca snapshot into a compact
    Dashboard-friendly JSON object.
    """

    snapshot = (
        snapshot
        or
        {}
    )


    daily_bar = (
        snapshot.get(
            "daily_bar"
        )
        or
        {}
    )


    latest_price = (
        _safe_float(
            snapshot.get(
                "latest_price"
            )
        )
    )


    previous_close = (
        _safe_float(
            snapshot.get(
                "previous_close"
            )
        )
    )


    daily_change = (
        _safe_float(
            snapshot.get(
                "daily_change"
            )
        )
    )


    daily_change_pct = (
        _safe_float(
            snapshot.get(
                "daily_change_pct"
            )
        )
    )


    # --------------------------------------------------------
    # FALLBACK CHANGE CALCULATION
    # --------------------------------------------------------

    if (
        daily_change is None
        or
        daily_change_pct is None
    ):

        (
            calculated_change,
            calculated_change_pct,
        ) = _calculate_price_change(
            latest_price,
            previous_close,
        )


        if daily_change is None:

            daily_change = (
                calculated_change
            )


        if daily_change_pct is None:

            daily_change_pct = (
                calculated_change_pct
            )


    return {

        "symbol":
            symbol,

        "label":
            label,

        "available":
            latest_price is not None,

        "latest_price":
            latest_price,

        "previous_close":
            previous_close,

        "change":
            daily_change,

        "change_pct":
            daily_change_pct,

        "bid":
            _safe_float(
                snapshot.get(
                    "bid_price"
                )
            ),

        "ask":
            _safe_float(
                snapshot.get(
                    "ask_price"
                )
            ),

        "spread":
            _safe_float(
                snapshot.get(
                    "spread"
                )
            ),

        "day_open":
            _safe_float(
                daily_bar.get(
                    "open"
                )
            ),

        "day_high":
            _safe_float(
                daily_bar.get(
                    "high"
                )
            ),

        "day_low":
            _safe_float(
                daily_bar.get(
                    "low"
                )
            ),

        "day_close":
            _safe_float(
                daily_bar.get(
                    "close"
                )
            ),

        "day_volume":
            daily_bar.get(
                "volume"
            ),

        "latest_trade_timestamp":
            snapshot.get(
                "latest_trade_timestamp"
            ),

    }


# ============================================================
# 9.4 EMPTY BENCHMARK SNAPSHOT
# ============================================================

def _empty_dashboard_snapshot(
    symbol,
    label,
):
    """
    Return a safe placeholder when one benchmark request fails.
    """

    return {

        "symbol":
            symbol,

        "label":
            label,

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

        "bid":
            None,

        "ask":
            None,

        "spread":
            None,

        "day_open":
            None,

        "day_high":
            None,

        "day_low":
            None,

        "day_close":
            None,

        "day_volume":
            None,

        "latest_trade_timestamp":
            None,

    }


# ============================================================
# 9.5 GET STORED POSTGRESQL CHART DATA
# ============================================================

def _get_dashboard_chart_data(
    symbol,
    limit,
):
    """
    Retrieve historical observations stored in PostgreSQL.

    This is now primarily the Dashboard fallback source.

    Alpaca Historical Market Data is preferred for the live
    interactive chart.
    """

    rows = list(

        MarketData.objects

        .filter(
            symbol=symbol
        )

        .order_by(
            "-date"
        )[:limit]

    )


    # Database query returns newest first.
    #
    # Charting requires oldest → newest.
    rows.reverse()


    return (
        MarketDataSerializer(
            rows,
            many=True,
        ).data
    )


# ============================================================
# 9.5A GET ALPACA DASHBOARD CHART HISTORY
# ============================================================

def _get_alpaca_dashboard_history(
    symbol,
    period="1M",
    limit=DASHBOARD_DEFAULT_CHART_ROWS,
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
    # --------------------------------------------------------

    symbol = (
        symbol
        or
        "SPY"
    )


    symbol = (
        str(
            symbol
        )
        .strip()
        .upper()
    )


    # --------------------------------------------------------
    # NORMALISE PERIOD
    # --------------------------------------------------------

    period = (
        period
        or
        "1M"
    )


    period = (
        str(
            period
        )
        .strip()
        .upper()
    )


    if period not in SUPPORTED_CHART_PERIODS:

        period = (
            "1M"
        )


    # --------------------------------------------------------
    # NORMALISE LIMIT
    # --------------------------------------------------------

    try:

        limit = int(
            limit
        )


    except (
        TypeError,
        ValueError,
    ):

        limit = (
            DASHBOARD_DEFAULT_CHART_ROWS
        )


    limit = min(
        max(
            limit,
            1,
        ),
        DASHBOARD_MAX_CHART_ROWS,
    )


    # --------------------------------------------------------
    # REQUEST ALPACA HISTORY
    # --------------------------------------------------------

    alpaca_history = (
        get_chart_history(
            symbol=symbol,
            period=period,
        )
    )


    raw_points = (
        alpaca_history.get(
            "points"
        )
        or
        []
    )


    points = (
        raw_points[
            -limit:
        ]
    )


    # --------------------------------------------------------
    # BUILD DATABASE-COMPATIBLE ROWS
    # --------------------------------------------------------

    rows = []


    for point in points:

        rows.append(
            {

                "date":
                    point.get(
                        "date"
                    ),

                "open_price":
                    point.get(
                        "open"
                    ),

                "high_price":
                    point.get(
                        "high"
                    ),

                "low_price":
                    point.get(
                        "low"
                    ),

                "close_price":
                    point.get(
                        "close"
                    ),

                "volume":
                    point.get(
                        "volume"
                    ),

            }
        )


    has_data = bool(
        points
    )


    message = None


    if not has_data:

        message = (
            f"No Alpaca historical bars were returned "
            f"for {symbol}."
        )


    return {

        "symbol":
            symbol,

        "period":
            alpaca_history.get(
                "period",
                period,
            ),

        "timeframe":
            alpaca_history.get(
                "timeframe"
            ),

        "provider":
            alpaca_history.get(
                "provider",
                "Alpaca",
            ),

        "feed":
            alpaca_history.get(
                "feed",
                getattr(
                    settings,
                    "ALPACA_DATA_FEED",
                    "iex",
                ),
            ),

        "has_data":
            has_data,

        "count":
            len(
                points
            ),

        "message":
            message,

        "points":
            points,

        "rows":
            rows,

        "first_bar_date":
            (
                points[0].get(
                    "date"
                )
                if points
                else None
            ),

        "last_bar_date":
            (
                points[-1].get(
                    "date"
                )
                if points
                else None
            ),

    }


# ============================================================
# 9.6 FIND BENCHMARKS WITH STORED HISTORY
# ============================================================

def _get_dashboard_chart_symbols():
    """
    Return benchmark symbols with stored MarketData rows.

    This describes PostgreSQL availability only.

    Alpaca historical data may be available even when the
    symbol has not been imported into PostgreSQL.
    """

    stored_symbols = set(

        MarketData.objects

        .filter(
            symbol__in=list(
                DASHBOARD_BENCHMARKS.keys()
            )
        )

        .values_list(
            "symbol",
            flat=True,
        )

        .distinct()

    )


    return [

        symbol

        for symbol
        in DASHBOARD_BENCHMARKS

        if symbol in stored_symbols

    ]


# ============================================================
# 9.7 GET LATEST MARKET CONDITION
# ============================================================

def _get_latest_market_condition(
    symbol,
):
    """
    Retrieve the newest stored MarketRegime result.
    """

    regime = (

        MarketRegime.objects

        .filter(
            symbol=symbol
        )

        .order_by(
            "-date",
            "-created_at",
        )

        .first()

    )


    if regime is None:

        return None


    try:

        display_name = (
            regime.get_regime_display()
        )


    except AttributeError:

        display_name = (
            regime.regime
        )


    return {

        "symbol":
            regime.symbol,

        "date":
            regime.date,

        "regime":
            regime.regime,

        "display":
            display_name,

        "confidence":
            _safe_float(
                regime.confidence
            ),

        "volatility":
            _safe_float(
                regime.volatility
            ),

        "trend_strength":
            _safe_float(
                regime.trend_strength
            ),

    }


# ============================================================
# 9.8 GET DATABASE DATA HEALTH
# ============================================================

def _get_dashboard_data_health():
    """
    Summarise the PostgreSQL MarketData persistence layer.
    """

    total_rows = (
        MarketData.objects
        .count()
    )


    symbol_count = (

        MarketData.objects

        .values(
            "symbol"
        )

        .distinct()

        .count()

    )


    latest_date = (

        MarketData.objects

        .order_by(
            "-date"
        )

        .values_list(
            "date",
            flat=True,
        )

        .first()

    )


    earliest_date = (

        MarketData.objects

        .order_by(
            "date"
        )

        .values_list(
            "date",
            flat=True,
        )

        .first()

    )


    symbols = list(

        MarketData.objects

        .order_by(
            "symbol"
        )

        .values_list(
            "symbol",
            flat=True,
        )

        .distinct()[:20]

    )


    days_since_latest_data = None


    if latest_date is not None:

        days_since_latest_data = (

            timezone.localdate()
            -
            latest_date

        ).days


    return {

        "database":
            "PostgreSQL",

        "historical_storage":
            "MarketPulse MarketData",

        "total_market_rows":
            total_rows,

        "stored_symbols":
            symbol_count,

        "symbols":
            symbols,

        "earliest_stored_date":
            earliest_date,

        "latest_stored_date":
            latest_date,

        "days_since_latest_data":
            days_since_latest_data,

        "historical_provider":
            "Stored MarketPulse data",

    }


# ============================================================
# 9.9 SERIALISE ONE ALERT
# ============================================================

def _serialise_dashboard_alert(
    alert,
):
    """
    Convert one persistent Alert model instance into JSON.
    """

    title = (

        getattr(
            alert,
            "title",
            None,
        )

        or

        getattr(
            alert,
            "alert_type",
            None,
        )

        or

        "MarketPulse Alert"

    )


    message = (

        getattr(
            alert,
            "message",
            None,
        )

        or

        getattr(
            alert,
            "description",
            None,
        )

        or

        str(
            alert
        )

    )


    severity = (

        getattr(
            alert,
            "severity",
            None,
        )

        or

        "warning"

    )


    destination = (

        getattr(
            alert,
            "action_url",
            None,
        )

        or

        getattr(
            alert,
            "destination",
            None,
        )

        or

        getattr(
            alert,
            "url",
            None,
        )

    )


    return {

        "id":
            alert.pk,

        "title":
            str(
                title
            ),

        "message":
            str(
                message
            ),

        "severity":
            str(
                severity
            ),

        "alert_type":
            getattr(
                alert,
                "alert_type",
                None,
            ),

        "is_active":
            bool(
                getattr(
                    alert,
                    "is_active",
                    True,
                )
            ),

        "is_read":
            bool(
                getattr(
                    alert,
                    "is_read",
                    False,
                )
            ),

        "destination":
            destination,

        "created_at":
            getattr(
                alert,
                "created_at",
                None,
            ),

    }


# ============================================================
# 9.10 GET ACTIVE USER ALERTS
# ============================================================

def _get_dashboard_alerts(
    user,
    limit=5,
):
    """
    Return active persistent Alert records.

    Alert:
        persisted event/notification

    Notice:
        generated current-state explanation
    """

    alerts = (

        Alert.objects

        .filter(
            user=user,
            is_active=True,
        )

        .order_by(
            "-created_at"
        )[:limit]

    )


    return [

        _serialise_dashboard_alert(
            alert
        )

        for alert
        in alerts

    ]


# ============================================================
# 9.11 GET USER DASHBOARD SUMMARY
# ============================================================

def _get_dashboard_user_summary(
    user,
):
    """
    Build user-specific Dashboard statistics.
    """

    strategies = (
        Strategy.objects
        .filter(
            user=user
        )
    )


    backtests = (
        Backtest.objects
        .filter(
            strategy__user=user
        )
    )


    average_win_rate = (

        backtests

        .aggregate(
            value=Avg(
                "win_rate"
            )
        )

        .get(
            "value"
        )

        or
        0

    )


    active_alert_count = (

        Alert.objects

        .filter(
            user=user,
            is_active=True,
        )

        .count()

    )


    return {

        "active_strategies":
            strategies
            .filter(
                is_active=True
            )
            .count(),

        "total_strategies":
            strategies.count(),

        "completed_backtests":
            backtests.count(),

        "average_win_rate_pct":
            (
                float(
                    average_win_rate
                )
                *
                100
            ),

        "historical_observations":
            MarketData.objects
            .count(),

        "active_alerts":
            active_alert_count,

    }


# ============================================================
# 9.12 GET RECENT BACKTESTS
# ============================================================

def _get_recent_backtests(
    user,
    limit=5,
):
    """
    Return recent user backtests.
    """

    backtests = (

        Backtest.objects

        .filter(
            strategy__user=user
        )

        .select_related(
            "strategy"
        )

        .order_by(
            "-created_at"
        )[:limit]

    )


    return (
        BacktestSerializer(
            backtests,
            many=True,
        ).data
    )


# ============================================================
# 9.13 BUILD BENCHMARK MARKET SUMMARY
# ============================================================

def _build_benchmark_market_summary(
    benchmark_results,
):
    """
    Describe current direction across Dashboard benchmarks.

    This is descriptive market context, not a forecast or
    investment recommendation.
    """

    available = 0

    advancing = 0

    declining = 0

    unchanged = 0

    percentage_changes = []


    for benchmark in benchmark_results:

        if not benchmark.get(
            "available"
        ):

            continue


        change_pct = (
            _safe_float(
                benchmark.get(
                    "change_pct"
                )
            )
        )


        if change_pct is None:

            continue


        available += 1


        percentage_changes.append(
            change_pct
        )


        if change_pct > 0:

            advancing += 1


        elif change_pct < 0:

            declining += 1


        else:

            unchanged += 1


    average_change_pct = None


    if percentage_changes:

        average_change_pct = (

            sum(
                percentage_changes
            )

            /

            len(
                percentage_changes
            )

        )


    if available == 0:

        direction = (
            "unavailable"
        )


        message = (
            "Current benchmark market data is unavailable."
        )


    elif advancing > declining:

        direction = (
            "mostly_positive"
        )


        message = (
            f"{advancing} of {available} available benchmark "
            "ETFs are above their previous close."
        )


    elif declining > advancing:

        direction = (
            "mostly_negative"
        )


        message = (
            f"{declining} of {available} available benchmark "
            "ETFs are below their previous close."
        )


    else:

        direction = (
            "mixed"
        )


        message = (
            "The displayed benchmark ETFs currently show "
            "mixed market direction."
        )


    return {

        "available_benchmarks":
            available,

        "advancing":
            advancing,

        "declining":
            declining,

        "unchanged":
            unchanged,

        "average_change_pct":
            average_change_pct,

        "direction":
            direction,

        "message":
            message,

    }


# ============================================================
# 9.14 BUILD DASHBOARD NOTICES
# ============================================================

def _build_dashboard_notices(
    user_summary,
    data_health,
    chart_rows,
    selected_symbol,
    provider_status,
):
    """
    Generate useful Dashboard notices.

    These are separate from persistent Alert records.
    """

    notices = []


    # --------------------------------------------------------
    # NO ACTIVE STRATEGIES
    # --------------------------------------------------------

    if (
        user_summary[
            "active_strategies"
        ]
        ==
        0
    ):

        notices.append(
            {

                "level":
                    "info",

                "code":
                    "NO_ACTIVE_STRATEGIES",

                "title":
                    "No active strategies",

                "message":
                    (
                        "Create or activate a strategy to begin "
                        "backtesting and strategy validation."
                    ),

                "destination":
                    "/strategy/",

            }
        )


    # --------------------------------------------------------
    # NO BACKTESTS
    # --------------------------------------------------------

    if (
        user_summary[
            "completed_backtests"
        ]
        ==
        0
    ):

        notices.append(
            {

                "level":
                    "info",

                "code":
                    "NO_BACKTESTS",

                "title":
                    "No backtests completed",

                "message":
                    (
                        "Run a backtest to populate performance, "
                        "win-rate and strategy results."
                    ),

                "destination":
                    "/strategy/",

            }
        )


    # --------------------------------------------------------
    # NO CHART HISTORY
    # --------------------------------------------------------

    if not chart_rows:

        notices.append(
            {

                "level":
                    "warning",

                "code":
                    "NO_CHART_HISTORY",

                "title":
                    (
                        f"No {selected_symbol} "
                        "historical chart data"
                    ),

                "message":
                    (
                        "MarketPulse could not obtain historical "
                        "chart observations for this asset."
                    ),

                "destination":
                    (
                        "/data/import/"
                        f"?symbol={selected_symbol}"
                    ),

            }
        )


    # --------------------------------------------------------
    # STORED DATA MAY BE STALE
    # --------------------------------------------------------

    days_since_latest_data = (
        data_health.get(
            "days_since_latest_data"
        )
    )


    if (
        days_since_latest_data is not None
        and
        days_since_latest_data > 4
    ):

        notices.append(
            {

                "level":
                    "warning",

                "code":
                    "HISTORICAL_DATA_STALE",

                "title":
                    "Stored historical data may be stale",

                "message":
                    (
                        "The most recent PostgreSQL MarketData "
                        f"observation is {days_since_latest_data} "
                        "days old."
                    ),

                "destination":
                    "/data/import/",

            }
        )


    # --------------------------------------------------------
    # PARTIAL ALPACA CONNECTIVITY
    # --------------------------------------------------------

    if provider_status == "partial":

        notices.append(
            {

                "level":
                    "warning",

                "code":
                    "ALPACA_PARTIAL",

                "title":
                    "Some Alpaca information is unavailable",

                "message":
                    (
                        "MarketPulse retrieved some Alpaca "
                        "information successfully, but one or "
                        "more provider components were "
                        "unavailable."
                    ),

                "destination":
                    "/dashboard/",

            }
        )


    # --------------------------------------------------------
    # ALPACA UNAVAILABLE
    # --------------------------------------------------------

    elif provider_status == "unavailable":

        notices.append(
            {

                "level":
                    "danger",

                "code":
                    "ALPACA_UNAVAILABLE",

                "title":
                    "Current Alpaca market data is unavailable",

                "message":
                    (
                        "MarketPulse could not retrieve current "
                        "market information. Stored PostgreSQL "
                        "data may still remain available."
                    ),

                "destination":
                    "/dashboard/",

            }
        )


    # --------------------------------------------------------
    # ACTIVE ALERTS
    # --------------------------------------------------------

    if (
        user_summary[
            "active_alerts"
        ]
        >
        0
    ):

        notices.append(
            {

                "level":
                    "warning",

                "code":
                    "ACTIVE_ALERTS",

                "title":
                    "MarketPulse alerts require attention",

                "message":
                    (
                        f"{user_summary['active_alerts']} active "
                        "alert(s) are stored for your account."
                    ),

                "destination":
                    "/dashboard/",

            }
        )


    return notices


# ============================================================
# 10. API HEALTH CHECK
# ============================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """
    Example:

        GET /api/health/
    """

    return Response(
        {

            "status":
                "ok",

            "application":
                "MarketPulse",

            "api":
                "Django REST Framework",

            "timestamp":
                timezone.now(),

        }
    )


# ============================================================
# 11. STORED HISTORICAL MARKET DATA API
# ============================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def market_latest(request):
    """
    Return OHLCV observations stored in PostgreSQL.

    Example:

        GET /api/market/latest/?symbol=AAPL&limit=60
    """

    symbol = (

        request.query_params

        .get(
            "symbol",
            "AAPL",
        )

        .strip()

        .upper()

    )


    try:

        limit = int(

            request.query_params.get(
                "limit",
                60,
            )

        )


        limit = min(
            max(
                limit,
                1,
            ),
            250,
        )


    except (
        TypeError,
        ValueError,
    ):

        limit = 60


    rows = list(

        MarketData.objects

        .filter(
            symbol=symbol
        )

        .order_by(
            "-date"
        )[:limit]

    )


    rows.reverse()


    return Response(
        {

            "symbol":
                symbol,

            "count":
                len(
                    rows
                ),

            "storage":
                "MarketPulse PostgreSQL",

            "historical_provider":
                "Stored MarketPulse data",

            "rows":
                MarketDataSerializer(
                    rows,
                    many=True,
                ).data,

        }
    )


# ============================================================
# 12. DASHBOARD MARKET OVERVIEW API
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_market_overview(request):
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
    # ========================================================

    selected_symbol = (

        request.query_params

        .get(
            "symbol",
            "SPY",
        )

        .strip()

        .upper()

    )


    if (
        selected_symbol
        not in
        DASHBOARD_BENCHMARKS
    ):

        selected_symbol = (
            "SPY"
        )


    # ========================================================
    # 12.2 SELECT CHART PERIOD
    # ========================================================

    chart_period = (

        request.query_params

        .get(
            "period",
            "1M",
        )

        .strip()

        .upper()

    )


    if chart_period not in SUPPORTED_CHART_PERIODS:

        chart_period = (
            "1M"
        )


    # ========================================================
    # 12.3 VALIDATE CHART LIMIT
    # ========================================================

    try:

        chart_limit = int(

            request.query_params.get(
                "limit",
                DASHBOARD_DEFAULT_CHART_ROWS,
            )

        )


        chart_limit = min(
            max(
                chart_limit,
                1,
            ),
            DASHBOARD_MAX_CHART_ROWS,
        )


    except (
        TypeError,
        ValueError,
    ):

        chart_limit = (
            DASHBOARD_DEFAULT_CHART_ROWS
        )


    # ========================================================
    # 12.4 PROVIDER ERROR STORAGE
    # ========================================================

    provider_errors = []


    # ========================================================
    # 12.5 GET CURRENT BENCHMARK SNAPSHOTS
    # ========================================================

    benchmark_results = []


    for (
        symbol,
        label,
    ) in DASHBOARD_BENCHMARKS.items():

        try:

            snapshot = (
                get_stock_snapshot(
                    symbol
                )
            )


            benchmark_results.append(
                _normalise_dashboard_snapshot(
                    symbol=symbol,
                    label=label,
                    snapshot=snapshot,
                )
            )


        except AlpacaServiceError as error:

            benchmark_results.append(
                _empty_dashboard_snapshot(
                    symbol=symbol,
                    label=label,
                )
            )


            provider_errors.append(
                {

                    "component":
                        "snapshot",

                    "symbol":
                        symbol,

                    "message":
                        str(
                            error
                        ),

                }
            )


    # ========================================================
    # 12.6 GET MARKET CLOCK
    # ========================================================

    try:

        raw_market_clock = (
            get_market_clock()
        )


        market_clock = {

            "available":
                True,

            "timestamp":
                raw_market_clock.get(
                    "timestamp"
                ),

            "is_open":
                raw_market_clock.get(
                    "is_open"
                ),

            "next_open":
                raw_market_clock.get(
                    "next_open"
                ),

            "next_close":
                raw_market_clock.get(
                    "next_close"
                ),

            "message":
                None,

        }


    except AlpacaServiceError as error:

        market_clock = {

            "available":
                False,

            "timestamp":
                None,

            "is_open":
                None,

            "next_open":
                None,

            "next_close":
                None,

            "message":
                str(
                    error
                ),

        }


        provider_errors.append(
            {

                "component":
                    "market_clock",

                "symbol":
                    None,

                "message":
                    str(
                        error
                    ),

            }
        )


    # ========================================================
    # 12.7 GET ALPACA HISTORICAL CHART
    # ========================================================

    alpaca_history_error = None


    try:

        history = (
            _get_alpaca_dashboard_history(

                symbol=
                    selected_symbol,

                period=
                    chart_period,

                limit=
                    chart_limit,

            )
        )


    except AlpacaServiceError as error:

        alpaca_history_error = (
            str(
                error
            )
        )


        history = {

            "symbol":
                selected_symbol,

            "period":
                chart_period,

            "timeframe":
                None,

            "provider":
                "Alpaca",

            "feed":
                getattr(
                    settings,
                    "ALPACA_DATA_FEED",
                    "iex",
                ),

            "has_data":
                False,

            "count":
                0,

            "message":
                alpaca_history_error,

            "points":
                [],

            "rows":
                [],

            "first_bar_date":
                None,

            "last_bar_date":
                None,

        }


        provider_errors.append(
            {

                "component":
                    "historical_bars",

                "symbol":
                    selected_symbol,

                "message":
                    alpaca_history_error,

            }
        )


    # ========================================================
    # 12.8 GET POSTGRESQL FALLBACK
    # ========================================================

    stored_chart_rows = (
        _get_dashboard_chart_data(

            symbol=
                selected_symbol,

            limit=
                chart_limit,

        )
    )


    # ========================================================
    # 12.9 SELECT CHART SOURCE
    # ========================================================

    if history.get(
        "has_data"
    ):

        chart_rows = (
            history.get(
                "rows",
                [],
            )
        )


        chart_points = (
            history.get(
                "points",
                [],
            )
        )


        chart_provider = (
            "Alpaca"
        )


        chart_storage = (
            "Alpaca Market Data API"
        )


        chart_fallback_used = (
            False
        )


        chart_message = (
            None
        )


    elif stored_chart_rows:

        chart_rows = (
            stored_chart_rows
        )


        chart_points = []


        for row in stored_chart_rows:

            chart_points.append(
                {

                    "timestamp":
                        None,

                    "date":
                        row.get(
                            "date"
                        ),

                    "open":
                        _safe_float(
                            row.get(
                                "open_price"
                            )
                        ),

                    "high":
                        _safe_float(
                            row.get(
                                "high_price"
                            )
                        ),

                    "low":
                        _safe_float(
                            row.get(
                                "low_price"
                            )
                        ),

                    "close":
                        _safe_float(
                            row.get(
                                "close_price"
                            )
                        ),

                    "volume":
                        row.get(
                            "volume"
                        ),

                }
            )


        chart_provider = (
            "Stored MarketPulse data"
        )


        chart_storage = (
            "MarketPulse PostgreSQL"
        )


        chart_fallback_used = (
            True
        )


        chart_message = (
            "Alpaca historical bars were unavailable, so "
            "MarketPulse is displaying stored PostgreSQL "
            "historical data instead."
        )


        history = {

            "symbol":
                selected_symbol,

            "period":
                chart_period,

            "timeframe":
                None,

            "provider":
                "Stored MarketPulse data",

            "feed":
                None,

            "has_data":
                True,

            "count":
                len(
                    chart_points
                ),

            "message":
                chart_message,

            "points":
                chart_points,

            "rows":
                chart_rows,

            "first_bar_date":
                (
                    chart_points[0]
                    .get(
                        "date"
                    )
                    if chart_points
                    else None
                ),

            "last_bar_date":
                (
                    chart_points[-1]
                    .get(
                        "date"
                    )
                    if chart_points
                    else None
                ),

            "fallback_used":
                True,

            "alpaca_error":
                alpaca_history_error,

        }


    else:

        chart_rows = []

        chart_points = []


        chart_provider = (
            "Unavailable"
        )


        chart_storage = (
            None
        )


        chart_fallback_used = (
            False
        )


        chart_message = (

            history.get(
                "message"
            )

            or

            (
                f"No historical {selected_symbol} bars "
                "are currently available."
            )

        )


    # ========================================================
    # 12.10 AVAILABLE CHART SYMBOLS
    # ========================================================

    # Alpaca can provide these benchmark charts even when no
    # corresponding MarketData row exists in PostgreSQL.

    available_chart_symbols = (
        list(
            DASHBOARD_BENCHMARKS.keys()
        )
    )


    stored_chart_symbols = (
        _get_dashboard_chart_symbols()
    )


    # ========================================================
    # 12.11 DETERMINE PROVIDER STATUS
    # ========================================================

    available_benchmark_count = sum(

        1

        for benchmark
        in benchmark_results

        if benchmark.get(
            "available"
        )

    )


    if (
        available_benchmark_count
        ==
        0
        and
        not history.get(
            "has_data"
        )
    ):

        provider_status = (
            "unavailable"
        )


    elif (
        available_benchmark_count
        <
        len(
            DASHBOARD_BENCHMARKS
        )
        or
        not market_clock.get(
            "available"
        )
        or
        chart_provider != "Alpaca"
    ):

        provider_status = (
            "partial"
        )


    else:

        provider_status = (
            "connected"
        )


    # ========================================================
    # 12.12 GET MARKET CONDITION
    # ========================================================

    market_condition = (
        _get_latest_market_condition(
            selected_symbol
        )
    )


    # ========================================================
    # 12.13 GET DATA HEALTH
    # ========================================================

    data_health = (
        _get_dashboard_data_health()
    )


    # ========================================================
    # 12.14 GET USER SUMMARY
    # ========================================================

    user_summary = (
        _get_dashboard_user_summary(
            request.user
        )
    )


    # ========================================================
    # 12.15 GET USER ALERTS
    # ========================================================

    active_alerts = (
        _get_dashboard_alerts(
            request.user,
            limit=5,
        )
    )


    # ========================================================
    # 12.16 GET RECENT BACKTESTS
    # ========================================================

    recent_backtests = (
        _get_recent_backtests(
            request.user,
            limit=5,
        )
    )


    # ========================================================
    # 12.17 BUILD MARKET SUMMARY
    # ========================================================

    market_summary = (
        _build_benchmark_market_summary(
            benchmark_results
        )
    )


    # ========================================================
    # 12.18 BUILD NOTICES
    # ========================================================

    notices = (
        _build_dashboard_notices(

            user_summary=
                user_summary,

            data_health=
                data_health,

            chart_rows=
                chart_rows,

            selected_symbol=
                selected_symbol,

            provider_status=
                provider_status,

        )
    )


    # ========================================================
    # 12.19 RETURN DASHBOARD RESPONSE
    # ========================================================

    return Response(
        {

            "application":
                "MarketPulse",


            # ------------------------------------------------
            # REFRESH CONFIGURATION
            # ------------------------------------------------

            "refresh": {

                "automatic":
                    True,

                "interval_seconds":
                    DASHBOARD_REFRESH_SECONDS,

            },


            # ------------------------------------------------
            # PROVIDER
            # ------------------------------------------------

            "provider": {

                "name":
                    "Alpaca",

                "feed":
                    getattr(
                        settings,
                        "ALPACA_DATA_FEED",
                        "iex",
                    ),

                "status":
                    provider_status,

                "purpose":
                    (
                        "Current market snapshots and "
                        "historical chart data"
                    ),

            },


            # ------------------------------------------------
            # MARKET CLOCK
            # ------------------------------------------------

            "market_clock":
                market_clock,


            # ------------------------------------------------
            # BENCHMARK CARDS
            # ------------------------------------------------

            "benchmarks":
                benchmark_results,


            # ------------------------------------------------
            # MARKET BREADTH
            # ------------------------------------------------

            "market_summary":
                market_summary,


            # ------------------------------------------------
            # PREFERRED HISTORICAL STRUCTURE
            # ------------------------------------------------

            "history":
                history,


            # ------------------------------------------------
            # DASHBOARD CHART COMPATIBILITY STRUCTURE
            # ------------------------------------------------

            "chart": {

                "symbol":
                    selected_symbol,

                "label":
                    DASHBOARD_BENCHMARKS[
                        selected_symbol
                    ],

                "period":
                    chart_period,

                "limit":
                    chart_limit,

                "has_data":
                    bool(
                        chart_points
                    ),

                "count":
                    len(
                        chart_points
                    ),

                "available_symbols":
                    available_chart_symbols,

                "stored_symbols":
                    stored_chart_symbols,

                "supported_symbols":
                    list(
                        DASHBOARD_BENCHMARKS.keys()
                    ),

                "provider":
                    chart_provider,

                "storage":
                    chart_storage,

                "fallback_used":
                    chart_fallback_used,

                "message":
                    chart_message,

                "rows":
                    chart_rows,

                "points":
                    chart_points,

            },


            # ------------------------------------------------
            # MARKET CONDITION
            # ------------------------------------------------

            "market_condition":
                market_condition,


            # ------------------------------------------------
            # USER SUMMARY
            # ------------------------------------------------

            "user_summary":
                user_summary,


            # ------------------------------------------------
            # PERSISTENT ALERT EVENTS
            # ------------------------------------------------

            "alerts":
                active_alerts,


            # ------------------------------------------------
            # GENERATED NOTICES
            # ------------------------------------------------

            "notices":
                notices,


            # ------------------------------------------------
            # RECENT USER ACTIVITY
            # ------------------------------------------------

            "recent_backtests":
                recent_backtests,


            # ------------------------------------------------
            # POSTGRESQL DATA HEALTH
            # ------------------------------------------------

            "data_health":
                data_health,


            # ------------------------------------------------
            # NON-FATAL PROVIDER ERRORS
            # ------------------------------------------------

            "provider_errors":
                provider_errors,


            # ------------------------------------------------
            # RESPONSE TIMESTAMP
            # ------------------------------------------------

            "updated_at":
                timezone.now(),

        }
    )


# ============================================================
# 13. POSITION SIZE RISK API
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def risk_position_size(request):
    """
    Calculate basic position sizing and stop-loss information.

    Required JSON:

        account_balance
        risk_percentage
        stop_loss_pct
        entry_price
    """

    try:

        position_size = (
            calculate_position_size(

                request.data[
                    "account_balance"
                ],

                request.data[
                    "risk_percentage"
                ],

                request.data[
                    "stop_loss_pct"
                ],

                request.data[
                    "entry_price"
                ],

            )
        )


        stop_loss_price = (
            calculate_stop_loss(

                request.data[
                    "entry_price"
                ],

                request.data[
                    "stop_loss_pct"
                ],

            )
        )


        return Response(
            {

                "position_size":
                    position_size,

                "stop_loss_price":
                    stop_loss_price,

            }
        )


    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:

        return Response(
            {

                "error":
                    str(
                        error
                    ),

            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )


# ============================================================
# 14. MATLAB RISK API
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def matlab_risk(request):
    """
    Run the optional MATLAB risk bridge.
    """

    try:

        result = (
            run_matlab_operation(
                "risk",
                dict(
                    request.data
                ),
            )
        )


        return Response(
            result
        )


    except MatlabUnavailable as error:

        return Response(
            {

                "error":
                    str(
                        error
                    ),

            },
            status=
                status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============================================================
# 15. ALPACA ASSET SEARCH
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alpaca_asset_search(request):
    """
    Search Alpaca's active US equity universe.

    Examples:

        GET /api/alpaca/assets/search/?q=AAPL

        GET /api/alpaca/assets/search/?q=Microsoft
    """

    query = (

        request.query_params

        .get(
            "q",
            "",
        )

        .strip()

    )


    if not query:

        return Response(
            {

                "query":
                    "",

                "count":
                    0,

                "provider":
                    "Alpaca",

                "results":
                    [],

            }
        )


    if len(
        query
    ) > 100:

        return Response(
            {

                "error":
                    "Search query is too long.",

            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )


    try:

        results = (
            search_assets(
                query=query,
                limit=12,
            )
        )


        return Response(
            {

                "query":
                    query,

                "count":
                    len(
                        results
                    ),

                "provider":
                    "Alpaca",

                "results":
                    results,

            }
        )


    except AlpacaServiceError as error:

        return Response(
            {

                "error":
                    str(
                        error
                    ),

                "provider":
                    "Alpaca",

            },
            status=
                status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============================================================
# 16. ALPACA ASSET DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alpaca_asset_detail(
    request,
    symbol,
):
    """
    Return Alpaca metadata for one asset.

    Example:

        GET /api/alpaca/assets/AAPL/
    """

    symbol = (

        str(
            symbol
        )

        .strip()

        .upper()

    )


    if not symbol:

        return Response(
            {

                "error":
                    "A symbol is required.",

            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )


    try:

        asset = (
            get_asset(
                symbol
            )
        )


        return Response(
            {

                "provider":
                    "Alpaca",

                "asset":
                    asset,

            }
        )


    except AlpacaServiceError as error:

        return Response(
            {

                "error":
                    str(
                        error
                    ),

                "provider":
                    "Alpaca",

                "symbol":
                    symbol,

            },
            status=
                status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============================================================
# 17. ALPACA CURRENT STOCK SNAPSHOT
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alpaca_stock_snapshot(
    request,
    symbol,
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

    symbol = (

        str(
            symbol
        )

        .strip()

        .upper()

    )


    if not symbol:

        return Response(
            {

                "error":
                    "A stock symbol is required.",

            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )


    try:

        asset = (
            get_asset(
                symbol
            )
        )


        snapshot = (
            get_stock_snapshot(
                symbol
            )
        )


        return Response(
            {

                "provider":
                    "Alpaca",

                "feed":
                    getattr(
                        settings,
                        "ALPACA_DATA_FEED",
                        "iex",
                    ),

                "asset":
                    asset,

                "snapshot":
                    snapshot,

                "updated_at":
                    timezone.now(),

            }
        )


    except AlpacaServiceError as error:

        return Response(
            {

                "error":
                    str(
                        error
                    ),

                "provider":
                    "Alpaca",

                "symbol":
                    symbol,

            },
            status=
                status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============================================================
# 18. ALPACA STOCK HISTORY
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alpaca_stock_history(
    request,
    symbol,
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

    symbol = (

        str(
            symbol
            or
            ""
        )

        .strip()

        .upper()

    )


    if not symbol:

        return Response(
            {

                "error":
                    "A stock symbol is required.",

            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )


    # Prevent unreasonable URL values.
    if len(
        symbol
    ) > 20:

        return Response(
            {

                "error":
                    "The supplied market symbol is too long.",

            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )


    # ========================================================
    # 18.2 NORMALISE PERIOD
    # ========================================================

    period = (

        request.query_params

        .get(
            "period",
            "1M",
        )

        .strip()

        .upper()

    )


    if period not in SUPPORTED_CHART_PERIODS:

        period = (
            "1M"
        )


    # ========================================================
    # 18.3 REQUEST ALPACA HISTORY
    # ========================================================

    try:

        history = (
            get_chart_history(
                symbol=symbol,
                period=period,
            )
        )


        points = (
            history.get(
                "points"
            )
            or
            []
        )


        # ====================================================
        # 18.4 RETURN PROFESSIONAL-CHART RESPONSE
        # ====================================================

        return Response(
            {

                "provider":
                    "Alpaca",

                "feed":
                    history.get(
                        "feed",
                        getattr(
                            settings,
                            "ALPACA_DATA_FEED",
                            "iex",
                        ),
                    ),

                "symbol":
                    symbol,

                "period":
                    period,

                "timeframe":
                    history.get(
                        "timeframe"
                    ),

                "has_data":
                    bool(
                        points
                    ),

                "count":
                    len(
                        points
                    ),

                # --------------------------------------------
                # Preferred chart structure
                # --------------------------------------------

                "points":
                    points,


                # --------------------------------------------
                # Full original service result
                # --------------------------------------------

                "history":
                    history,


                # --------------------------------------------
                # Chart capabilities
                # --------------------------------------------

                "chart_capabilities": {

                    "candlestick":
                        True,

                    "line":
                        True,

                    "heikin_ashi":
                        True,

                    "volume":
                        True,

                    # Requires additional implementation.
                    "volume_profile":
                        False,

                    # Requires futures contract data.
                    "futures_curve":
                        False,

                },


                "updated_at":
                    timezone.now(),

            }
        )


    except AlpacaServiceError as error:

        return Response(
            {

                "provider":
                    "Alpaca",

                "symbol":
                    symbol,

                "period":
                    period,

                "has_data":
                    False,

                "count":
                    0,

                "points":
                    [],

                "error":
                    str(
                        error
                    ),

                "chart_capabilities": {

                    "candlestick":
                        True,

                    "line":
                        True,

                    "heikin_ashi":
                        True,

                    "volume":
                        True,

                    "volume_profile":
                        False,

                    "futures_curve":
                        False,

                },

            },
            status=
                status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============================================================
# 19. STRATEGY API
# ============================================================

class StrategyViewSet(
    viewsets.ModelViewSet
):
    """
    Authenticated CRUD access to strategies belonging only to
    the currently logged-in user.
    """

    serializer_class = (
        StrategySerializer
    )


    permission_classes = [
        IsAuthenticated
    ]


    def get_queryset(self):

        return (

            Strategy.objects

            .filter(
                user=
                    self.request.user
            )

            .order_by(
                "-created_at"
            )

        )


    def perform_create(
        self,
        serializer,
    ):

        serializer.save(
            user=
                self.request.user
        )


# ============================================================
# 20. BACKTEST API
# ============================================================

class BacktestViewSet(
    viewsets.ReadOnlyModelViewSet
):
    """
    Read-only API access to backtests belonging to strategies
    owned by the current user.
    """

    serializer_class = (
        BacktestSerializer
    )


    permission_classes = [
        IsAuthenticated
    ]


    def get_queryset(self):

        return (

            Backtest.objects

            .filter(
                strategy__user=
                    self.request.user
            )

            .select_related(
                "strategy"
            )

            .order_by(
                "-created_at"
            )

        )