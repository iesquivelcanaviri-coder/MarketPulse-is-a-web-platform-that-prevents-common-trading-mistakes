"""
============================================================
MARKETPULSE - API ENDPOINTS
============================================================

FRAMEWORK MAPPING:

React / JavaScript Frontend
        ↓
Django REST Framework API
        ↓
Django ORM / Risk Calculator / MATLAB / Alpaca Service
        ↓
JSON Response


THIS API LAYER PROVIDES ACCESS TO:

1. Application health information
2. Historical MarketPulse market data
3. Dashboard market overview
4. Risk calculations
5. MATLAB integration
6. Alpaca asset search
7. Alpaca asset information
8. Alpaca current market snapshots
9. User strategies
10. Backtest results


DASHBOARD MARKET FLOW:

Dashboard
    ↓
MarketPulse API
    ↓
┌────────────────────────┬─────────────────────────┐
│                        │                         │
▼                        ▼                         ▼
Alpaca Snapshot     PostgreSQL MarketData    MarketRegime
│                        │                         │
▼                        ▼                         ▼
Live Benchmark      Historical Chart        Market Condition
Cards               / Data Health           Summary


DASHBOARD BENCHMARKS:

SPY
    Broad US large-cap market

QQQ
    Nasdaq-100 / technology-heavy market

DIA
    Dow Jones large-cap market

IWM
    US small-cap market


IMPORTANT SECURITY DESIGN:

The browser NEVER receives:

- ALPACA_API_KEY_ID
- ALPACA_API_SECRET_KEY

Instead:

Browser / React
        ↓
MarketPulse Django API
        ↓
Alpaca Service Layer
        ↓
Alpaca API


IMPORTANT DATA-PROVENANCE DESIGN:

Current / latest information:
    Alpaca

Historical chart information:
    PostgreSQL MarketData

Historical MarketData may still contain observations that were
previously imported from Yahoo Finance.

Until the historical importer is completely changed to Alpaca,
the API describes historical data as:

    "Stored MarketPulse data"

rather than incorrectly claiming that every historical row came
from Alpaca.

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

# analysis_tools is no longer a separate user-facing tab.
#
# It now acts as an internal analytics layer.
#
# The detailed Market Condition tool belongs under Data,
# while the Dashboard only displays its latest stored result.
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

# All communication with Alpaca stays inside the service layer.
#
# The API never builds Alpaca authentication headers itself.
from data_management.services.alpaca import (
    AlpacaServiceError,
    get_asset,
    get_stock_snapshot,
    search_assets,
)


# ============================================================
# 8. DASHBOARD CONFIGURATION
# ============================================================

# These four ETFs provide a compact illustration of several
# important segments of the US equity market.
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


# Maximum historical rows the Dashboard graph can request.
DASHBOARD_MAX_CHART_ROWS = 250


# Default graph window.
DASHBOARD_DEFAULT_CHART_ROWS = 60


# Suggested browser refresh interval.
#
# The future Dashboard JavaScript / React component can use
# this instead of hard-coding its own value.
DASHBOARD_REFRESH_SECONDS = 60


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
    Convert Decimal, string, integer or other numeric values
    into a JSON-friendly float.

    Missing or invalid numbers return None rather than causing
    the complete Dashboard API to fail.
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
    Calculate:

    - absolute price change
    - percentage price change

    Example:

    Latest:
        105

    Previous close:
        100

    Change:
        +5

    Percentage:
        +5%
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
    Convert one normalised Alpaca service response into a small,
    Dashboard-friendly object.

    The frontend therefore does not need to understand the
    original Alpaca JSON response structure.
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
    # FALLBACK CALCULATION
    # --------------------------------------------------------

    # Some provider responses may not already contain change
    # values.
    #
    # When possible, calculate them from latest price and the
    # previous close.
    if (
        daily_change is None
        or
        daily_change_pct is None
    ):

        (
            calculated_change,
            calculated_change_pct,
        ) = (
            _calculate_price_change(
                latest_price,
                previous_close,
            )
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
    Return a safe placeholder when one Alpaca request fails.

    A failure for one benchmark should never create a complete
    Dashboard HTTP 500 response.
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
# 9.5 GET HISTORICAL DASHBOARD GRAPH DATA
# ============================================================

def _get_dashboard_chart_data(
    symbol,
    limit,
):
    """
    Retrieve historical observations from PostgreSQL.

    The database query is intentionally separate from Alpaca's
    latest market snapshot.

    This gives MarketPulse:

    - reproducible historical data
    - stable backtesting inputs
    - less unnecessary external API traffic

    Until the Yahoo → Alpaca historical migration is completed,
    these rows should be described as stored MarketPulse data.
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


    # PostgreSQL query returns newest first.
    #
    # The graph needs chronological order.
    rows.reverse()


    return (
        MarketDataSerializer(
            rows,
            many=True,
        ).data
    )


# ============================================================
# 9.6 FIND BENCHMARKS WITH STORED HISTORY
# ============================================================

def _get_dashboard_chart_symbols():
    """
    Return benchmark symbols that already have historical rows
    in MarketData.

    Example:

    Alpaca current snapshot:
        SPY available

    MarketData:
        SPY not imported

    Result:
        live card available
        historical graph unavailable
    """

    stored_symbols = set(
        MarketData.objects
        .filter(
            symbol__in=
                list(
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
    Retrieve the most recent MarketRegime result for a symbol.

    The Dashboard only displays the latest result.

    The complete Market Condition workflow remains under Data.
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
# 9.8 GET DATA HEALTH
# ============================================================

def _get_dashboard_data_health():
    """
    Summarise the current PostgreSQL MarketData storage layer.

    This gives the Dashboard useful information such as:

    - number of stored symbols
    - total OHLCV rows
    - earliest stored observation
    - latest stored observation
    - possible stale data
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


    days_since_latest_data = (
        None
    )


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

        # Historical source is deliberately not labelled
        # "Alpaca" yet because legacy Yahoo imports may exist.
        "historical_provider":
            "Stored MarketPulse data",

    }


# ============================================================
# 9.9 SERIALISE ONE ALERT SAFELY
# ============================================================

def _serialise_dashboard_alert(
    alert,
):
    """
    Convert an Alert model instance into a small object suitable
    for the Dashboard API.

    The helper deliberately uses safe attribute lookup so this
    API remains compatible while the Alert model is improved
    during the next Dashboard step.
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

        "is_active":
            bool(
                getattr(
                    alert,
                    "is_active",
                    True,
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
    Return active database Alert records.

    This is separate from generated Dashboard notices.

    ALERT:
        persistent database object

    NOTICE:
        generated explanation of current application state
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
            float(
                average_win_rate
            )
            *
            100,

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
    Return recent user backtests for the Dashboard's
    Recent Activity area.
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
# 9.13 BUILD MARKET BREADTH SUMMARY
# ============================================================

def _build_benchmark_market_summary(
    benchmark_results,
):
    """
    Summarise the direction of the benchmark cards.

    This is descriptive only.

    It is NOT:

    - an investment recommendation
    - a trading signal
    - a market forecast
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


    average_change_pct = (
        None
    )


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


    # --------------------------------------------------------
    # USER-FRIENDLY MARKET DIRECTION
    # --------------------------------------------------------

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
    Generate helpful current-state notices.

    These are intentionally separate from core.Alert.

    Persistent Alert:
        saved in PostgreSQL

    Dashboard Notice:
        generated from the current state of MarketPulse
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
                        "win-rate and strategy result information."
                    ),

                "destination":
                    "/strategy/",

            }
        )


    # --------------------------------------------------------
    # NO HISTORICAL DATA FOR SELECTED CHART
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
                        f"No stored {selected_symbol} "
                        "historical chart data"
                    ),

                "message":
                    (
                        "Current Alpaca snapshot information may "
                        "still be available, but historical data "
                        "must be imported before MarketPulse can "
                        "draw the full historical graph."
                    ),

                "destination":
                    (
                        "/data/import/"
                        f"?symbol={selected_symbol}"
                    ),

            }
        )


    # --------------------------------------------------------
    # POSSIBLY STALE HISTORICAL DATA
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
                    "Historical market data may be stale",

                "message":
                    (
                        "The most recent stored historical "
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
                    "Some current market data is unavailable",

                "message":
                    (
                        "MarketPulse retrieved some benchmark "
                        "snapshots from Alpaca successfully, but "
                        "one or more requests were unavailable."
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
                        "benchmark snapshots. Stored historical "
                        "data remains available."
                    ),

                "destination":
                    "/dashboard/",

            }
        )


    # --------------------------------------------------------
    # PERSISTENT ALERTS REQUIRE ATTENTION
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
                        "alert(s) are currently stored for your "
                        "account."
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
# 11. HISTORICAL MARKET DATA API
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
    ------------------------------------------------------------
    DASHBOARD MARKET OVERVIEW
    ------------------------------------------------------------

    Example:

    GET /api/dashboard/market-overview/

    GET /api/dashboard/market-overview/?symbol=SPY

    GET /api/dashboard/market-overview/?symbol=QQQ&limit=90


    RESPONSE INCLUDES:

    - Alpaca provider status
    - SPY snapshot
    - QQQ snapshot
    - DIA snapshot
    - IWM snapshot
    - benchmark market direction
    - PostgreSQL historical graph data
    - latest Market Condition
    - Dashboard user statistics
    - persistent alerts
    - generated notices
    - recent backtests
    - historical data-health summary
    - refresh configuration
    ------------------------------------------------------------
    """


    # ========================================================
    # 12.1 SELECT GRAPH BENCHMARK
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
    # 12.2 VALIDATE GRAPH LIMIT
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
    # 12.3 GET CURRENT ALPACA BENCHMARK SNAPSHOTS
    # ========================================================

    benchmark_results = []

    provider_errors = []


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

                    "symbol":
                        symbol,

                    "message":
                        str(
                            error
                        ),

                }
            )


    # ========================================================
    # 12.4 DETERMINE PROVIDER STATUS
    # ========================================================

    if not provider_errors:

        provider_status = (
            "connected"
        )


    elif (
        len(
            provider_errors
        )
        <
        len(
            DASHBOARD_BENCHMARKS
        )
    ):

        provider_status = (
            "partial"
        )


    else:

        provider_status = (
            "unavailable"
        )


    # ========================================================
    # 12.5 GET STORED HISTORICAL GRAPH
    # ========================================================

    chart_rows = (
        _get_dashboard_chart_data(
            symbol=
                selected_symbol,

            limit=
                chart_limit,
        )
    )


    available_chart_symbols = (
        _get_dashboard_chart_symbols()
    )


    # ========================================================
    # 12.6 GET LATEST MARKET CONDITION
    # ========================================================

    market_condition = (
        _get_latest_market_condition(
            selected_symbol
        )
    )


    # ========================================================
    # 12.7 GET DATA HEALTH
    # ========================================================

    data_health = (
        _get_dashboard_data_health()
    )


    # ========================================================
    # 12.8 GET USER SUMMARY
    # ========================================================

    user_summary = (
        _get_dashboard_user_summary(
            request.user
        )
    )


    # ========================================================
    # 12.9 GET ACTIVE PERSISTENT ALERTS
    # ========================================================

    active_alerts = (
        _get_dashboard_alerts(
            request.user,
            limit=5,
        )
    )


    # ========================================================
    # 12.10 GET RECENT BACKTEST ACTIVITY
    # ========================================================

    recent_backtests = (
        _get_recent_backtests(
            request.user,
            limit=5,
        )
    )


    # ========================================================
    # 12.11 BUILD MARKET DIRECTION SUMMARY
    # ========================================================

    market_summary = (
        _build_benchmark_market_summary(
            benchmark_results
        )
    )


    # ========================================================
    # 12.12 BUILD USEFUL DASHBOARD NOTICES
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
    # 12.13 GRAPH STATUS MESSAGE
    # ========================================================

    chart_message = (
        None
    )


    if not chart_rows:

        chart_message = (
            f"No historical {selected_symbol} observations "
            "are currently stored in MarketPulse. Import this "
            "asset in the Data tab to populate the historical "
            "market graph."
        )


    # ========================================================
    # 12.14 RETURN COMPLETE DASHBOARD RESPONSE
    # ========================================================

    return Response(
        {

            "application":
                "MarketPulse",


            # ------------------------------------------------
            # FRONTEND REFRESH CONFIGURATION
            # ------------------------------------------------

            "refresh": {

                "automatic":
                    True,

                "interval_seconds":
                    DASHBOARD_REFRESH_SECONDS,

            },


            # ------------------------------------------------
            # CURRENT MARKET PROVIDER
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
                    "Current market snapshots",

            },


            # ------------------------------------------------
            # BENCHMARK CARDS
            # ------------------------------------------------

            "benchmarks":
                benchmark_results,


            # ------------------------------------------------
            # BENCHMARK MARKET DIRECTION
            # ------------------------------------------------

            "market_summary":
                market_summary,


            # ------------------------------------------------
            # HISTORICAL MARKET GRAPH
            # ------------------------------------------------

            "chart": {

                "symbol":
                    selected_symbol,

                "label":
                    DASHBOARD_BENCHMARKS[
                        selected_symbol
                    ],

                "limit":
                    chart_limit,

                "has_data":
                    bool(
                        chart_rows
                    ),

                "available_symbols":
                    available_chart_symbols,

                "supported_symbols":
                    list(
                        DASHBOARD_BENCHMARKS.keys()
                    ),

                "storage":
                    "MarketPulse PostgreSQL",

                "historical_provider":
                    "Stored MarketPulse data",

                "message":
                    chart_message,

                "rows":
                    chart_rows,

            },


            # ------------------------------------------------
            # LATEST STORED MARKET CONDITION
            # ------------------------------------------------

            "market_condition":
                market_condition,


            # ------------------------------------------------
            # MARKETPULSE USER METRICS
            # ------------------------------------------------

            "user_summary":
                user_summary,


            # ------------------------------------------------
            # PERSISTENT DATABASE ALERTS
            # ------------------------------------------------

            "alerts":
                active_alerts,


            # ------------------------------------------------
            # AUTOMATIC CURRENT-STATE NOTICES
            # ------------------------------------------------

            "notices":
                notices,


            # ------------------------------------------------
            # RECENT USER ACTIVITY
            # ------------------------------------------------

            "recent_backtests":
                recent_backtests,


            # ------------------------------------------------
            # DATABASE / HISTORICAL DATA HEALTH
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
    Basic position-size calculation.

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
    Search the Alpaca asset universe.

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
    Return Alpaca asset metadata.

    Example:

    GET /api/alpaca/assets/AAPL/
    """

    symbol = (
        symbol
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
    Return:

    - asset metadata
    - latest trade
    - latest quote
    - daily bar
    - previous-close information

    Example:

    GET /api/alpaca/stocks/AAPL/snapshot/
    """

    symbol = (
        symbol
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
# 18. STRATEGY API
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
# 19. BACKTEST API
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