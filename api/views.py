"""
============================================================
MARKETPULSE - API ENDPOINTS
============================================================

Framework mapping:

React / JavaScript Frontend
        ↓
Django REST Framework API
        ↓
Django ORM / Risk Calculator / MATLAB / Alpaca Service
        ↓
JSON Response


This API layer provides access to:

1. Application health information
2. Historical MarketPulse market data
3. Risk calculations
4. MATLAB integration
5. User strategies
6. Backtest results
7. Alpaca asset search
8. Alpaca current market snapshots


IMPORTANT SECURITY DESIGN:

The browser NEVER receives the Alpaca API key or secret.

Browser
    ↓
MarketPulse API
    ↓
Alpaca Service Layer
    ↓
Alpaca API

This keeps external API credentials on the Django server.
============================================================
"""


# ============================================================
# 1. DJANGO REST FRAMEWORK IMPORTS
# ============================================================

from rest_framework import (
    status,
    viewsets,
)

from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)

from rest_framework.response import Response


# ============================================================
# 2. CORE MARKETPULSE IMPORTS
# ============================================================

from core.models import (
    MarketData,
    Strategy,
    Backtest,
)

from core.matlab_bridge import (
    run_matlab_operation,
)

from core.exceptions import (
    MatlabUnavailable,
)


# ============================================================
# 3. RISK MANAGEMENT IMPORTS
# ============================================================

from risk_management.calculators import (
    calculate_position_size,
    calculate_stop_loss,
)


# ============================================================
# 4. API SERIALIZERS
# ============================================================

from .serializers import (
    MarketDataSerializer,
    StrategySerializer,
    BacktestSerializer,
)


# ============================================================
# 5. ALPACA MARKET DATA SERVICE
# ============================================================

from data_management.services.alpaca import (
    AlpacaServiceError,
    get_asset,
    get_stock_snapshot,
    search_assets,
)


# ============================================================
# 6. HEALTH CHECK
# ============================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """
    ------------------------------------------------------------
    HEALTH CHECK
    ------------------------------------------------------------

    A simple public endpoint that confirms that the
    MarketPulse Django REST API is running.

    Example:

    GET /api/health/

    Response:

    {
        "status": "ok",
        "application": "MarketPulse",
        "api": "Django REST Framework"
    }
    ------------------------------------------------------------
    """

    return Response(
        {
            "status": "ok",
            "application": "MarketPulse",
            "api": "Django REST Framework",
        }
    )


# ============================================================
# 7. HISTORICAL MARKET DATA
# ============================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def market_latest(request):
    """
    ------------------------------------------------------------
    HISTORICAL MARKET DATA
    ------------------------------------------------------------

    Returns historical OHLCV records stored inside the
    MarketPulse PostgreSQL database.

    This data normally originates from the Data tab.

    Example:

    GET /api/market/latest/?symbol=AAPL&limit=60

    The limit is restricted to a maximum of 250 records so
    that one request cannot accidentally return an
    unnecessarily large dataset.
    ------------------------------------------------------------
    """

    # --------------------------------------------------------
    # Get requested symbol
    # --------------------------------------------------------

    symbol = (
        request.query_params
        .get(
            "symbol",
            "AAPL",
        )
        .strip()
        .upper()
    )


    # --------------------------------------------------------
    # Validate requested row limit
    # --------------------------------------------------------

    try:

        limit = int(
            request.query_params.get(
                "limit",
                60,
            )
        )


        # Minimum = 1
        # Maximum = 250
        limit = min(
            max(
                limit,
                1,
            ),
            250,
        )


    except ValueError:

        limit = 60


    # --------------------------------------------------------
    # Retrieve newest database rows
    # --------------------------------------------------------

    rows = list(
        MarketData.objects
        .filter(
            symbol=symbol
        )
        .order_by("-date")[:limit]
    )


    # Reverse the rows so the response is chronological.
    rows.reverse()


    return Response(
        MarketDataSerializer(
            rows,
            many=True,
        ).data
    )


# ============================================================
# 8. POSITION SIZE RISK API
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def risk_position_size(request):
    """
    ------------------------------------------------------------
    BASIC POSITION-SIZE CALCULATOR
    ------------------------------------------------------------

    Existing MarketPulse API calculation.

    Required JSON values:

    account_balance
    risk_percentage
    stop_loss_pct
    entry_price

    Returns:

    position_size
    stop_loss_price
    ------------------------------------------------------------
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
                    str(error),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


# ============================================================
# 9. MATLAB RISK API
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def matlab_risk(request):
    """
    ------------------------------------------------------------
    MATLAB RISK BRIDGE
    ------------------------------------------------------------

    Sends risk-analysis parameters to the existing
    MarketPulse MATLAB integration.

    If MATLAB is unavailable, the API returns HTTP 503.
    ------------------------------------------------------------
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
                    str(error),
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============================================================
# 10. ALPACA ASSET SEARCH
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alpaca_asset_search(request):
    """
    ------------------------------------------------------------
    SEARCH ALPACA ASSET UNIVERSE
    ------------------------------------------------------------

    Searches Alpaca's active US-equity universe.

    Search can use:

    - ticker symbol
    - company / asset name


    Examples:

    GET /api/alpaca/assets/search/?q=AAPL

    GET /api/alpaca/assets/search/?q=Microsoft

    GET /api/alpaca/assets/search/?q=NVIDIA


    Example response:

    {
        "query": "Microsoft",
        "count": 1,
        "provider": "Alpaca",
        "results": [
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "exchange": "NASDAQ",
                "tradable": true,
                ...
            }
        ]
    }


    The Alpaca credentials remain entirely on the server.
    ------------------------------------------------------------
    """

    # --------------------------------------------------------
    # Read search text
    # --------------------------------------------------------

    query = (
        request.query_params
        .get(
            "q",
            "",
        )
        .strip()
    )


    # --------------------------------------------------------
    # Empty queries return an empty result set
    # --------------------------------------------------------

    if not query:

        return Response(
            {
                "query": "",
                "count": 0,
                "provider": "Alpaca",
                "results": [],
            }
        )


    # --------------------------------------------------------
    # Limit very large query strings
    # --------------------------------------------------------

    if len(query) > 100:

        return Response(
            {
                "error":
                    "Search query is too long.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


    try:

        # ----------------------------------------------------
        # Search Alpaca through the service layer
        # ----------------------------------------------------

        results = search_assets(
            query=query,
            limit=12,
        )


        return Response(
            {
                "query":
                    query,

                "count":
                    len(results),

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
                    str(error),

                "provider":
                    "Alpaca",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============================================================
# 11. ALPACA ASSET DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alpaca_asset_detail(
    request,
    symbol,
):
    """
    ------------------------------------------------------------
    ALPACA ASSET INFORMATION
    ------------------------------------------------------------

    Retrieves Alpaca metadata for a single asset.

    Example:

    GET /api/alpaca/assets/AAPL/


    Information can include:

    - symbol
    - company / asset name
    - exchange
    - active status
    - tradability
    - margin availability
    - shortability
    - fractional trading capability


    This is useful when MarketPulse needs information about
    an asset without requesting a full market-data snapshot.
    ------------------------------------------------------------
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
            status=status.HTTP_400_BAD_REQUEST,
        )


    try:

        asset = get_asset(
            symbol
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
                    str(error),

                "provider":
                    "Alpaca",

                "symbol":
                    symbol,
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============================================================
# 12. ALPACA LIVE / LATEST STOCK SNAPSHOT
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alpaca_stock_snapshot(
    request,
    symbol,
):
    """
    ------------------------------------------------------------
    ALPACA STOCK SNAPSHOT
    ------------------------------------------------------------

    Retrieves both:

    1. Alpaca asset metadata
    2. Alpaca latest stock-market snapshot


    Alpaca's stock snapshot can provide:

    - latest trade
    - latest quote
    - bid price
    - ask price
    - spread
    - latest minute bar
    - current daily bar
    - previous daily bar


    Example:

    GET /api/alpaca/stocks/AAPL/snapshot/


    MarketPulse uses this endpoint to populate the Risk tab
    without exposing Alpaca credentials to browser JavaScript.
    ------------------------------------------------------------
    """

    # --------------------------------------------------------
    # Normalise ticker
    # --------------------------------------------------------

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
            status=status.HTTP_400_BAD_REQUEST,
        )


    try:

        # ----------------------------------------------------
        # Retrieve asset metadata
        # ----------------------------------------------------

        asset = get_asset(
            symbol
        )


        # ----------------------------------------------------
        # Retrieve latest market snapshot
        # ----------------------------------------------------

        snapshot = (
            get_stock_snapshot(
                symbol
            )
        )


        # ----------------------------------------------------
        # Return a normalised MarketPulse response
        # ----------------------------------------------------

        return Response(
            {
                "provider":
                    "Alpaca",

                "asset":
                    asset,

                "snapshot":
                    snapshot,
            }
        )


    except AlpacaServiceError as error:

        return Response(
            {
                "error":
                    str(error),

                "provider":
                    "Alpaca",

                "symbol":
                    symbol,
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============================================================
# 13. STRATEGY API
# ============================================================

class StrategyViewSet(
    viewsets.ModelViewSet
):
    """
    ------------------------------------------------------------
    USER STRATEGY API
    ------------------------------------------------------------

    Provides authenticated CRUD access to strategies belonging
    only to the logged-in MarketPulse user.
    ------------------------------------------------------------
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
                user=self.request.user
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
            user=self.request.user
        )


# ============================================================
# 14. BACKTEST API
# ============================================================

class BacktestViewSet(
    viewsets.ReadOnlyModelViewSet
):
    """
    ------------------------------------------------------------
    USER BACKTEST API
    ------------------------------------------------------------

    Provides read-only access to backtests belonging to the
    logged-in user's strategies.
    ------------------------------------------------------------
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