"""
============================================================
MARKETPULSE - DATA MANAGEMENT VIEWS
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
data_management/views.py
    ↓
templates/data_management/import.html
    ↓
Historical OHLCV + Detailed Market Condition workspace


============================================================
DATA PROVIDER ARCHITECTURE
============================================================

Alpaca
    ↓
Primary Market Data Provider
    ↓
Historical Daily Bars
    ↓
core.MarketData
    ↓
PostgreSQL
    ↓
MarketPulse Analytics


Yahoo Finance
    ↓
Legacy compatibility only
    ↓
Not exposed as the primary Data-tab provider


============================================================
MARKET CONDITION ARCHITECTURE
============================================================

The Market Condition feature belongs directly inside the
main Data workspace.

The user does NOT need to open a separate Market Condition
page.


Selected Market
    ↓
Run Market Condition Analysis
    ↓
data_management.views.market_condition()
    ↓
Refresh recent Alpaca historical daily bars
    ↓
core.MarketData
    ↓
Validate sufficient recent observations
    ↓
analysis_tools.analyzers.identify_market_regime()
    ↓
analysis_tools.models.MarketRegime
    ↓
PostgreSQL
    ↓
Redirect to Data tab
    ↓
#market-condition
    ↓
Detailed Market Condition panel


============================================================
WHY HISTORICAL DATA IS REQUIRED
============================================================

Market Condition is NOT calculated from one live price.

The internal Market Regime engine uses historical information
including:

- recent closing prices;
- daily returns;
- historical volatility;
- 20-period moving average;
- 60-period moving average;
- trend strength.

Therefore at least 60 usable historical observations are
required.


============================================================
ALPACA REFRESH BEHAVIOUR
============================================================

When the user clicks:

    Run Market Condition Analysis

MarketPulse attempts to refresh approximately one year of
recent daily Alpaca market data for the selected symbol.

The data is stored through:

    data_management.utils.import_market_data()

which uses the existing Alpaca service and MarketData
update-or-create workflow.

This means:

SPY
    ↓
Alpaca historical bars
    ↓
MarketData(symbol="SPY")
    ↓
identify_market_regime("SPY")
    ↓
MarketRegime(symbol="SPY")


MSFT
    ↓
Alpaca historical bars
    ↓
MarketData(symbol="MSFT")
    ↓
identify_market_regime("MSFT")
    ↓
MarketRegime(symbol="MSFT")


Each selected symbol therefore receives its own independent
Market Condition analysis.


============================================================
FAIL-SAFE BEHAVIOUR
============================================================

If Alpaca cannot be reached:

- MarketPulse does not immediately fail;
- stored PostgreSQL data is checked;
- if enough stored observations exist, analysis continues;
- otherwise the user receives a clear explanation.


============================================================
PURPOSE OF THE DATA TAB
============================================================

The Data tab is responsible for:

1. Importing historical market data from Alpaca.

2. Saving imported observations into core.MarketData.

3. Displaying historical:
   - Open
   - High
   - Low
   - Close
   - Volume

4. Showing:
   - Provider
   - Feed

5. Remembering the selected symbol.

6. Allowing the user to switch between imported datasets.

7. Displaying import history.

8. Loading the Strategy & Model Library.

9. Allowing the user to select a quantitative model.

10. Supplying historical market data to:
    - Strategy Builder
    - Backtesting
    - Risk Management
    - Strategy Robustness
    - Market Condition Analysis
    - Other internal analytics

11. Running Market Condition analysis inside the Data
    workspace.


============================================================
IMPORTANT ARCHITECTURE
============================================================

The old separate Analysis navigation tab is no longer
required.

analysis_tools remains an INTERNAL analytics engine.

User-facing location:

    Data
        ↓
    Detailed Market Condition


The route:

    data_management:market_condition

remains an ACTION ENDPOINT.

It:

1. Receives the selected symbol.
2. Refreshes recent historical data from Alpaca.
3. Checks analytical readiness.
4. Runs identify_market_regime().
5. Stores the MarketRegime result.
6. Redirects back to the Data workspace.


============================================================
DATA PROVENANCE
============================================================

Historical Provider:
    Alpaca

Default Feed:
    IEX

Historical observations:
    core.MarketData

Market Condition results:
    analysis_tools.models.MarketRegime

============================================================
"""


# ============================================================
# 1. PYTHON IMPORTS
# ============================================================

from datetime import timedelta
from urllib.parse import urlencode


# ============================================================
# 2. DJANGO IMPORTS
# ============================================================

from django.conf import settings

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.shortcuts import (
    redirect,
    render,
)

from django.urls import reverse

from django.utils import timezone


# ============================================================
# 3. CORE MARKET DATA
# ============================================================

from core.models import MarketData


# ============================================================
# 4. DATA MANAGEMENT IMPORTS
# ============================================================

from .forms import DataImportForm

from .models import (
    DataImport,
    DataSource,
)

from .tasks import process_data_import

from .utils import import_market_data


# ============================================================
# 5. STRATEGY & MODEL LIBRARY
# ============================================================

from strategy_builder.library import (
    get_grouped_strategy_library,
)

from strategy_builder.models import (
    StrategyLibraryItem,
)


# ============================================================
# 6. INTERNAL ANALYTICS ENGINE
# ============================================================

from analysis_tools.analyzers import (
    identify_market_regime,
)

from analysis_tools.models import (
    MarketRegime,
)


# ============================================================
# 7. DATA WORKSPACE CONSTANTS
# ============================================================

# The Market Regime analyzer uses a 60-period moving average.
#
# Therefore the minimum must be 60 rather than 20.
MARKET_CONDITION_MINIMUM_OBSERVATIONS = 60


# The analyzer evaluates approximately the most recent
# 300 calendar days surrounding the latest stored observation.
#
# The Data view uses the same window when deciding whether the
# selected dataset is analytically ready.
MARKET_CONDITION_ANALYSIS_WINDOW_DAYS = 300


# When the user explicitly requests Market Condition analysis,
# MarketPulse refreshes approximately one year of recent daily
# Alpaca data.
#
# A year normally provides considerably more than the minimum
# 60 trading observations while remaining efficient for this
# educational application.
MARKET_CONDITION_REFRESH_DAYS = 365


# ============================================================
# 8. PRIVATE URL / REDIRECT HELPERS
# ============================================================

def _build_data_workspace_url(
    symbol="",
    anchor="market-condition",
):
    """
    Build a URL pointing to the main Data workspace.

    Example:

        /data/import/?symbol=SPY#market-condition
    """

    data_page_url = reverse(
        "data_management:import"
    )


    symbol = (
        str(
            symbol or ""
        )
        .strip()
        .upper()
    )


    if symbol:

        query_string = urlencode(
            {
                "symbol":
                    symbol,
            }
        )


        data_page_url = (
            f"{data_page_url}"
            f"?{query_string}"
        )


    if anchor:

        data_page_url = (
            f"{data_page_url}"
            f"#{anchor}"
        )


    return data_page_url


def _redirect_to_data_workspace(
    symbol="",
    anchor="market-condition",
):
    """
    Redirect to the main Data workspace.
    """

    return redirect(
        _build_data_workspace_url(
            symbol=symbol,
            anchor=anchor,
        )
    )


# ============================================================
# 9. MARKET CONDITION DATASET STATUS
# ============================================================

def _get_market_condition_status(
    symbol,
):
    """
    Determine whether the selected symbol contains enough
    recent historical data for Market Regime Analysis.

    IMPORTANT:

    This does not simply count every MarketData row ever
    stored for the symbol.

    The analyzer itself uses a recent historical window.

    Therefore readiness is calculated against the same type
    of recent window.

    Returns:

        {
            "ready": True / False,
            "total_observations": int,
            "analysis_observations": int,
            "latest_record": MarketData or None,
            "latest_date": date or None,
            "analysis_start_date": date or None,
        }
    """

    symbol = (
        str(
            symbol or ""
        )
        .strip()
        .upper()
    )


    default_status = {

        "ready":
            False,

        "total_observations":
            0,

        "analysis_observations":
            0,

        "latest_record":
            None,

        "latest_date":
            None,

        "analysis_start_date":
            None,

    }


    if not symbol:

        return default_status


    symbol_data = (
        MarketData.objects
        .filter(
            symbol=symbol
        )
    )


    total_observations = (
        symbol_data.count()
    )


    latest_record = (
        symbol_data
        .order_by(
            "-date"
        )
        .first()
    )


    if latest_record is None:

        default_status[
            "total_observations"
        ] = total_observations

        return default_status


    latest_date = (
        latest_record.date
    )


    analysis_start_date = (

        latest_date

        -

        timedelta(
            days=
                MARKET_CONDITION_ANALYSIS_WINDOW_DAYS
        )
    )


    analysis_observations = (

        symbol_data

        .filter(
            date__gte=
                analysis_start_date,

            date__lte=
                latest_date,
        )

        .count()
    )


    return {

        "ready":
            (
                analysis_observations
                >=
                MARKET_CONDITION_MINIMUM_OBSERVATIONS
            ),

        "total_observations":
            total_observations,

        "analysis_observations":
            analysis_observations,

        "latest_record":
            latest_record,

        "latest_date":
            latest_date,

        "analysis_start_date":
            analysis_start_date,

    }


# ============================================================
# 10. ALPACA MARKET CONDITION REFRESH
# ============================================================

def _refresh_market_condition_data(
    symbol,
):
    """
    Refresh recent daily historical data from Alpaca before
    Market Condition analysis.

    This reuses the existing MarketPulse historical importer:

        import_market_data()

    which ultimately stores OHLCV observations through:

        MarketData.objects.update_or_create()

    Existing observations are therefore updated rather than
    duplicated.

    Returns the number of Alpaca records processed.
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


    end_date = (
        timezone.localdate()
    )


    start_date = (

        end_date

        -

        timedelta(
            days=
                MARKET_CONDITION_REFRESH_DAYS
        )
    )


    return import_market_data(

        symbol=symbol,

        start_date=start_date,

        end_date=end_date,

        timeframe="1Day",
    )


# ============================================================
# 11. HISTORICAL MARKET DATA IMPORT VIEW
# ============================================================

@login_required
def data_import(request):
    """
    Main MarketPulse Data workspace.

    Provides:

    - Alpaca historical import;
    - historical OHLCV display;
    - dataset switching;
    - model library;
    - import history;
    - Detailed Market Condition;
    - Market Condition readiness information.
    """


    # ========================================================
    # 11.1 ENSURE ALPACA DATA SOURCE EXISTS
    # ========================================================

    alpaca_source, _created = (
        DataSource.objects.update_or_create(

            name="Alpaca",

            defaults={

                "url":
                    "https://alpaca.markets/",

                "api_key_required":
                    True,

                "is_active":
                    True,

            },
        )
    )


    # ========================================================
    # 11.2 DISABLE LEGACY YAHOO FINANCE SOURCE
    # ========================================================

    DataSource.objects.filter(
        name="Yahoo Finance"
    ).update(
        is_active=False
    )


    # ========================================================
    # 11.3 BUILD HISTORICAL IMPORT FORM
    # ========================================================

    form = DataImportForm(

        request.POST or None,

        initial={

            "source":
                alpaca_source.pk,

        },
    )


    # ========================================================
    # 11.4 RESTRICT PROVIDER TO ALPACA
    # ========================================================

    if "source" in form.fields:

        form.fields[
            "source"
        ].queryset = (

            DataSource.objects

            .filter(
                pk=alpaca_source.pk,
                is_active=True,
            )
        )


        form.fields[
            "source"
        ].initial = (
            alpaca_source.pk
        )


    # ========================================================
    # 11.5 HANDLE MANUAL HISTORICAL IMPORT
    # ========================================================

    if (
        request.method == "POST"
        and
        form.is_valid()
    ):


        import_job = (
            form.save(
                commit=False
            )
        )


        # ----------------------------------------------------
        # Associate request with current user
        # ----------------------------------------------------

        import_job.user = (
            request.user
        )


        # ----------------------------------------------------
        # Alpaca is the enforced primary provider
        # ----------------------------------------------------

        import_job.source = (
            alpaca_source
        )


        # ----------------------------------------------------
        # Normalise symbol
        # ----------------------------------------------------

        import_job.symbol = (

            import_job.symbol

            .strip()

            .upper()
        )


        import_job.save()


        # ====================================================
        # 11.6 PROCESS IMPORT
        # ====================================================

        if getattr(
            settings,
            "USE_CELERY",
            False,
        ):

            process_data_import.delay(
                import_job.pk
            )


            messages.info(
                request,
                (
                    f"{import_job.symbol} historical market "
                    "data import from Alpaca has been submitted."
                ),
            )


        else:

            process_data_import(
                import_job.pk
            )


            import_job.refresh_from_db()


            if (
                import_job.status
                ==
                "completed"
            ):

                messages.success(
                    request,
                    (
                        f"{import_job.symbol} imported "
                        "successfully from Alpaca. "
                        f"{import_job.records_imported} "
                        "historical market observations "
                        "were processed."
                    ),
                )


            else:

                messages.error(
                    request,
                    (
                        f"{import_job.symbol} Alpaca import "
                        "failed. "
                        f"{import_job.error_message}"
                    ),
                )


        # ====================================================
        # 11.7 RETURN TO IMPORTED SYMBOL
        # ====================================================

        data_page_url = reverse(
            "data_management:import"
        )


        query_string = urlencode(
            {
                "symbol":
                    import_job.symbol,
            }
        )


        return redirect(
            f"{data_page_url}"
            f"?{query_string}"
        )


    # ========================================================
    # 12. DETERMINE DISPLAYED SYMBOL
    # ========================================================

    selected_symbol = (

        request.GET

        .get(
            "symbol",
            "",
        )

        .strip()

        .upper()
    )


    # ========================================================
    # 13. FALLBACK TO MOST RECENT COMPLETED IMPORT
    # ========================================================

    if not selected_symbol:

        latest_import = (

            DataImport.objects

            .filter(
                user=request.user,
                status="completed",
            )

            .order_by(
                "-created_at"
            )

            .first()
        )


        if latest_import:

            selected_symbol = (

                latest_import.symbol

                .strip()

                .upper()
            )


    # ========================================================
    # 14. FALLBACK TO MOST RECENT MARKETDATA SYMBOL
    # ========================================================

    if not selected_symbol:

        latest_market_record = (

            MarketData.objects

            .order_by(
                "-date"
            )

            .first()
        )


        if latest_market_record:

            selected_symbol = (

                latest_market_record.symbol

                .strip()

                .upper()
            )


    # ========================================================
    # 15. PREPARE HISTORICAL DATA VALUES
    # ========================================================

    market_data = (
        MarketData.objects.none()
    )


    total_records = 0

    earliest_record = None

    latest_record = None


    # ========================================================
    # 16. LOAD SELECTED HISTORICAL DATASET
    # ========================================================

    if selected_symbol:


        all_symbol_data = (

            MarketData.objects

            .filter(
                symbol=selected_symbol
            )
        )


        total_records = (
            all_symbol_data.count()
        )


        earliest_record = (

            all_symbol_data

            .order_by(
                "date"
            )

            .first()
        )


        latest_record = (

            all_symbol_data

            .order_by(
                "-date"
            )

            .first()
        )


        market_data = (

            all_symbol_data

            .order_by(
                "-date"
            )[:250]
        )


    # ========================================================
    # 17. AVAILABLE IMPORTED SYMBOLS
    # ========================================================

    available_symbols = (

        MarketData.objects

        .order_by(
            "symbol"
        )

        .values_list(
            "symbol",
            flat=True,
        )

        .distinct()
    )


    # ========================================================
    # 18. RECENT IMPORT HISTORY
    # ========================================================

    recent_imports = (

        DataImport.objects

        .filter(
            user=request.user
        )

        .select_related(
            "source"
        )

        .order_by(
            "-created_at"
        )[:10]
    )


    # ========================================================
    # 19. STRATEGY / MODEL LIBRARY
    # ========================================================

    strategy_categories = (
        get_grouped_strategy_library()
    )


    # ========================================================
    # 20. SELECTED MODEL
    # ========================================================

    selected_model_code = (

        request.GET

        .get(
            "model",
            "",
        )

        .strip()
    )


    selected_model = None


    if selected_model_code:

        selected_model = (

            StrategyLibraryItem.objects

            .filter(
                code=selected_model_code,
                is_active=True,
            )

            .first()
        )


    # ========================================================
    # 21. MODEL / DATASET STATUS
    # ========================================================

    dataset_available = bool(

        selected_symbol

        and

        total_records > 0

    )


    model_selected = (
        selected_model
        is not None
    )


    # ========================================================
    # 22. MARKET CONDITION READINESS
    # ========================================================

    market_condition_status = (
        _get_market_condition_status(
            selected_symbol
        )
    )


    market_condition_ready = (
        market_condition_status[
            "ready"
        ]
    )


    market_condition_observation_count = (
        market_condition_status[
            "analysis_observations"
        ]
    )


    # ========================================================
    # 23. LOAD SELECTED SYMBOL'S LATEST MARKET CONDITION
    # ========================================================

    latest_regime = None


    if selected_symbol:

        latest_regime = (

            MarketRegime.objects

            .filter(
                symbol=selected_symbol
            )

            .order_by(
                "-date",
                "-created_at",
            )

            .first()
        )


    # ========================================================
    # 24. DETERMINE WHETHER RESULT MATCHES LATEST DATA
    # ========================================================

    market_condition_is_current = False


    if (
        latest_regime
        and
        latest_record
    ):

        market_condition_is_current = (

            latest_regime.date
            ==
            latest_record.date

        )


    # ========================================================
    # 25. DATA PROVENANCE
    # ========================================================

    market_data_provider = (
        "Alpaca"
    )


    market_data_feed = (

        str(

            getattr(
                settings,
                "ALPACA_DATA_FEED",
                "iex",
            )

        )

        .upper()
    )


    # ========================================================
    # 26. TEMPLATE CONTEXT
    # ========================================================

    context = {


        # ====================================================
        # IMPORT FORM
        # ====================================================

        "form":
            form,


        # ====================================================
        # PROVIDER INFORMATION
        # ====================================================

        "market_data_provider":
            market_data_provider,

        "market_data_feed":
            market_data_feed,

        "alpaca_source":
            alpaca_source,


        # ====================================================
        # SELECTED DATASET
        # ====================================================

        "selected_symbol":
            selected_symbol,


        # ====================================================
        # HISTORICAL MARKET DATA
        # ====================================================

        "market_data":
            market_data,

        "total_records":
            total_records,

        "earliest_record":
            earliest_record,

        "latest_record":
            latest_record,

        "available_symbols":
            available_symbols,


        # ====================================================
        # IMPORT HISTORY
        # ====================================================

        "recent_imports":
            recent_imports,


        # ====================================================
        # STRATEGY / MODEL LIBRARY
        # ====================================================

        "strategy_categories":
            strategy_categories,

        "selected_model":
            selected_model,

        "model_selected":
            model_selected,

        "dataset_available":
            dataset_available,


        # ====================================================
        # MARKET CONDITION
        # ====================================================

        "latest_regime":
            latest_regime,

        "market_condition_ready":
            market_condition_ready,

        "market_condition_is_current":
            market_condition_is_current,

        "market_condition_minimum_observations":
            MARKET_CONDITION_MINIMUM_OBSERVATIONS,

        "market_condition_observation_count":
            market_condition_observation_count,

        "market_condition_latest_data_date":
            market_condition_status[
                "latest_date"
            ],

        "market_condition_analysis_start_date":
            market_condition_status[
                "analysis_start_date"
            ],

    }


    # ========================================================
    # 27. RENDER DATA WORKSPACE
    # ========================================================

    return render(
        request,
        "data_management/import.html",
        context,
    )


# ============================================================
# 28. IMPORT HISTORY VIEW
# ============================================================

@login_required
def import_history(request):
    """
    Display the authenticated user's historical import jobs.
    """


    imports = (

        DataImport.objects

        .filter(
            user=request.user
        )

        .select_related(
            "source"
        )

        .order_by(
            "-created_at"
        )
    )


    context = {

        "imports":
            imports,

        # Retained for compatibility with older templates.
        "jobs":
            imports,

    }


    return render(
        request,
        "data_management/history.html",
        context,
    )


# ============================================================
# 29. MARKET CONDITION ANALYSIS ACTION
# ============================================================

@login_required
def market_condition(request):
    """
    ============================================================
    MARKETPULSE - MARKET CONDITION ANALYSIS ACTION
    ============================================================

    FINAL WORKFLOW:

    Data tab
        ↓
    User selects symbol
        ↓
    Run Market Condition Analysis
        ↓
    POST
        ↓
    Refresh latest available daily Alpaca history
        ↓
    Save/update MarketData
        ↓
    Recalculate recent observation count
        ↓
    Require at least 60 observations
        ↓
    identify_market_regime(symbol)
        ↓
    MarketRegime saved
        ↓
    Redirect to:
    Data tab#market-condition


    IMPORTANT:

    Alpaca data is refreshed only when the user intentionally
    runs the analysis.

    Merely changing the symbol dropdown does NOT generate an
    external Alpaca request.
    ============================================================
    """


    # ========================================================
    # 29.1 READ SELECTED SYMBOL
    # ========================================================

    selected_symbol = (

        request.POST.get(
            "symbol"
        )

        or

        request.GET.get(
            "symbol"
        )

        or

        ""
    )


    selected_symbol = (

        selected_symbol

        .strip()

        .upper()
    )


    # ========================================================
    # 29.2 LEGACY GET REQUESTS
    # ========================================================

    if request.method != "POST":

        return _redirect_to_data_workspace(
            symbol=selected_symbol,
        )


    # ========================================================
    # 29.3 REQUIRE SYMBOL
    # ========================================================

    if not selected_symbol:

        messages.error(
            request,
            (
                "Please select a market dataset before "
                "running Market Condition analysis."
            ),
        )


        return _redirect_to_data_workspace()


    # ========================================================
    # 29.4 REFRESH RECENT ALPACA HISTORICAL DATA
    # ========================================================

    refresh_error = None

    refreshed_records = 0


    # Only attempt the external refresh when credentials are
    # configured.
    #
    # If credentials are unavailable, MarketPulse may still
    # analyse an already stored historical dataset.

    if getattr(
        settings,
        "ALPACA_CONFIGURED",
        False,
    ):

        try:

            refreshed_records = (
                _refresh_market_condition_data(
                    selected_symbol
                )
            )


        except Exception as error:

            refresh_error = str(
                error
            )


    else:

        refresh_error = (
            "Alpaca credentials are not configured."
        )


    # ========================================================
    # 29.5 CHECK DATA AGAIN AFTER REFRESH
    # ========================================================

    market_condition_status = (
        _get_market_condition_status(
            selected_symbol
        )
    )


    observation_count = (
        market_condition_status[
            "analysis_observations"
        ]
    )


    # ========================================================
    # 29.6 INSUFFICIENT DATA
    # ========================================================

    if not market_condition_status[
        "ready"
    ]:


        if refresh_error:

            messages.error(
                request,
                (
                    f"{selected_symbol} currently has "
                    f"{observation_count} usable recent "
                    "historical observations. "
                    f"At least "
                    f"{MARKET_CONDITION_MINIMUM_OBSERVATIONS} "
                    "are required. "
                    "MarketPulse also could not refresh "
                    "enough recent Alpaca data: "
                    f"{refresh_error}"
                ),
            )


        else:

            messages.error(
                request,
                (
                    f"{selected_symbol} currently has "
                    f"{observation_count} usable recent "
                    "historical observations. "
                    f"At least "
                    f"{MARKET_CONDITION_MINIMUM_OBSERVATIONS} "
                    "are required before MarketPulse can "
                    "calculate the Market Condition."
                ),
            )


        return _redirect_to_data_workspace(
            symbol=selected_symbol,
        )


    # ========================================================
    # 29.7 ALPACA FAILED BUT STORED DATA IS SUFFICIENT
    # ========================================================

    if refresh_error:

        messages.warning(
            request,
            (
                "MarketPulse could not refresh the latest "
                f"Alpaca data for {selected_symbol}. "
                "The Market Condition will therefore be "
                "calculated from the sufficient historical "
                "data already stored in PostgreSQL."
            ),
        )


    # ========================================================
    # 29.8 RUN MARKET REGIME ENGINE
    # ========================================================

    try:

        regime_result = (
            identify_market_regime(
                selected_symbol
            )
        )


        # ====================================================
        # SUCCESS
        # ====================================================

        if regime_result:


            if (
                refreshed_records
                and
                not refresh_error
            ):

                messages.success(
                    request,
                    (
                        f"{selected_symbol} market data was "
                        "refreshed from Alpaca and Market "
                        "Condition analysis completed "
                        "successfully."
                    ),
                )


            else:

                messages.success(
                    request,
                    (
                        "Market Condition analysis completed "
                        f"for {selected_symbol}."
                    ),
                )


        # ====================================================
        # ANALYZER RETURNED NONE
        # ====================================================

        else:

            messages.error(
                request,
                (
                    "MarketPulse received sufficient stored "
                    f"data for {selected_symbol}, but the "
                    "internal Market Regime engine could not "
                    "produce a classification. "
                    "Please check the historical dataset for "
                    "missing or invalid observations."
                ),
            )


    # ========================================================
    # ANALYTICAL / DATABASE ERROR
    # ========================================================

    except Exception as error:

        messages.error(
            request,
            (
                "Market Condition analysis could not be "
                f"completed for {selected_symbol}: {error}"
            ),
        )


    # ========================================================
    # 29.9 RETURN TO DETAILED MARKET CONDITION PANEL
    # ========================================================

    return _redirect_to_data_workspace(
        symbol=selected_symbol,
    )


# ============================================================
# 30. LEGACY MARKET CONDITION RESULTS ROUTE
# ============================================================

@login_required
def market_condition_results(request):
    """
    Compatibility route for older MarketPulse links.

    Previous versions used:

        /data/market-condition/results/

    The final application displays the result inside:

        Data
            ↓
        Detailed Market Condition

    Therefore this view only redirects.
    """


    # ========================================================
    # 30.1 READ OPTIONAL SYMBOL
    # ========================================================

    selected_symbol = (

        request.GET

        .get(
            "symbol",
            "",
        )

        .strip()

        .upper()
    )


    # ========================================================
    # 30.2 FALLBACK TO MOST RECENT MARKET REGIME
    # ========================================================

    if not selected_symbol:

        latest_regime = (

            MarketRegime.objects

            .order_by(
                "-date",
                "-created_at",
            )

            .first()
        )


        if latest_regime:

            selected_symbol = (

                latest_regime.symbol

                .strip()

                .upper()
            )


    # ========================================================
    # 30.3 REDIRECT TO FINAL DATA WORKSPACE
    # ========================================================

    return _redirect_to_data_workspace(
        symbol=selected_symbol,
    )