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
data_management/tasks.py
    ↓
DataImport
    ↓
core.MarketData
    ↓
data_management/views.py
    ↓
templates/data_management/import.html
    ↓
Historical OHLCV table


DATA PROVIDER ARCHITECTURE:

Alpaca
    ↓
Primary Market Data Provider
    ↓
Historical Bars
    +
Latest Market Information
    ↓
MarketPulse


Yahoo Finance
    ↓
Legacy / fallback provider only
    ↓
Not exposed as the primary Data-tab provider


STRATEGY / MODEL FLOW:

StrategyLibraryItem
    ↓
strategy_builder/library.py
    ↓
data_management/views.py
    ↓
templates/data_management/import.html
    ↓
User selects imported dataset
    +
User selects model
    ↓
Future Model Runner


MARKET CONDITION FLOW:

Alpaca Historical Data
    ↓
core.MarketData
    ↓
analysis_tools/analyzers.py
    ↓
identify_market_regime()
    ↓
analysis_tools.models.MarketRegime
    ↓
data_management.views.market_condition
    ↓
templates/data_management/market_condition.html


PURPOSE OF THE DATA TAB:

The Data tab is responsible for:

1. Importing historical market data from Alpaca.
2. Saving imported observations into core.MarketData.
3. Displaying historical OHLCV data:
   - Date
   - Open
   - High
   - Low
   - Close
   - Volume
4. Showing the market-data provider and feed.
5. Remembering the most recently imported symbol.
6. Allowing the user to switch between imported symbols.
7. Displaying recent import history.
8. Loading the MarketPulse Strategy & Model Library.
9. Allowing the user to select a quantitative model.
10. Providing historical data to:
    - Strategy Builder
    - Backtesting
    - Risk Management
    - Strategy Robustness
    - Market Condition Analysis
    - Stress Testing
    - Model Runner
11. Providing Market Condition / Market Regime analysis.


IMPORTANT ARCHITECTURE:

The old separate Analysis tab is no longer exposed
through the user interface.

analysis_tools remains an INTERNAL analytics engine.

The user-facing location for Market Regime Analysis is:

Data
    ↓
Market Condition


DATA PROVENANCE:

MarketPulse should clearly identify:

Provider:
    Alpaca

Feed:
    IEX by default

Historical observations are persisted in PostgreSQL
through core.MarketData so analysis and backtesting
remain reproducible.

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

# Django settings provide access to MarketPulse configuration.
#
# This includes:
#
# - USE_CELERY
# - ALPACA_DATA_FEED
#
# Alpaca credentials themselves remain in environment
# variables and must never be exposed in templates.
from django.conf import settings


# Django messages allow MarketPulse to display:
#
# - Success messages
# - Information messages
# - Validation errors
# - Import failures
from django.contrib import messages


# Only authenticated users should be able to:
#
# - Import market data
# - Inspect stored datasets
# - Run Market Condition analysis
from django.contrib.auth.decorators import login_required


# redirect:
# Sends the user to another Django URL.
#
# render:
# Combines a template with context data.
from django.shortcuts import redirect, render


# reverse converts a named Django route into its URL.
#
# Example:
#
# data_management:import
#
# becomes:
#
# /data/import/
from django.urls import reverse


# ============================================================
# 2. CORE MARKET DATA IMPORT
# ============================================================

# MarketData is MarketPulse's persistent historical
# OHLCV storage layer.
#
# The external provider supplies the original observations,
# while MarketPulse stores them in PostgreSQL for:
#
# - Backtesting
# - Risk calculations
# - Market Condition analysis
# - Strategy testing
# - Stress testing
from core.models import MarketData


# ============================================================
# 3. DATA MANAGEMENT IMPORTS
# ============================================================

# DataImportForm validates the historical-data request.
#
# Typical fields include:
#
# - Source
# - Symbol
# - Start date
# - End date
from .forms import DataImportForm


# DataSource:
# Identifies the external provider associated with an import.
#
# DataImport:
# Provides an audit/history record for each import request.
from .models import (
    DataImport,
    DataSource,
)


# process_data_import connects the DataImport record
# to the actual historical-data import process.
#
# TARGET ARCHITECTURE:
#
# DataImport
#     ↓
# process_data_import()
#     ↓
# Alpaca historical bars
#     ↓
# core.MarketData
from .tasks import process_data_import


# ============================================================
# 4. STRATEGY & MODEL LIBRARY IMPORTS
# ============================================================

# Groups StrategyLibraryItem objects by category.
#
# Example groups:
#
# - Stochastic Models
# - Time-Series Models
# - Machine Learning Models
# - Factor Models
# - Portfolio Optimisation
# - Derivatives Pricing
# - Monte Carlo / Simulation
from strategy_builder.library import (
    get_grouped_strategy_library,
)


# StrategyLibraryItem stores metadata describing each
# quantitative model available inside MarketPulse.
from strategy_builder.models import (
    StrategyLibraryItem,
)


# ============================================================
# 5. INTERNAL ANALYTICS ENGINE IMPORTS
# ============================================================

# analysis_tools is no longer a separate user-facing tab.
#
# Instead, it acts as an internal analytics engine.
#
# Market Regime Analysis is presented to the user as:
#
# Data
#     ↓
# Market Condition
from analysis_tools.analyzers import (
    identify_market_regime,
)


# MarketRegime stores calculated Market Condition results.
from analysis_tools.models import (
    MarketRegime,
)


# ============================================================
# 6. HISTORICAL MARKET DATA IMPORT VIEW
# ============================================================

@login_required
def data_import(request):
    """
    ============================================================
    HISTORICAL MARKET DATA + MODEL SELECTION
    ============================================================

    PRIMARY DATA PROVIDER:

        Alpaca


    FRAMEWORK FLOW:

    Browser
        ↓
    DataImportForm
        ↓
    data_import()
        ↓
    DataImport database record
        ↓
    process_data_import()
        ↓
    Alpaca Historical Market Data
        ↓
    core.MarketData
        ↓
    PostgreSQL
        ↓
    import.html
        ↓
    Historical OHLCV table


    MODEL SELECTION FLOW:

    StrategyLibraryItem
        ↓
    get_grouped_strategy_library()
        ↓
    data_import()
        ↓
    import.html
        ↓
    User selects model
        ↓
    selected_model
        ↓
    Future Model Runner


    OHLCV:

    O = Open
    H = High
    L = Low
    C = Close
    V = Volume

    ============================================================
    """


    # ========================================================
    # 6.1 ENSURE ALPACA DATA SOURCE EXISTS
    # ========================================================

    # Alpaca is MarketPulse's primary market-data provider.
    #
    # update_or_create() keeps the configuration
    # self-healing:
    #
    # If Alpaca does not exist:
    #     Create it.
    #
    # If Alpaca already exists:
    #     Refresh its configuration.
    alpaca_source, created = (
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
    # 6.2 DISABLE LEGACY YAHOO FINANCE SOURCE
    # ========================================================

    # Yahoo Finance was the original historical-data provider.
    #
    # It is no longer exposed as the primary Data-tab source.
    #
    # We do not delete the database record because old
    # DataImport audit records may still reference it.
    #
    # Keeping historical audit relationships intact is better
    # than deleting the old provider.
    DataSource.objects.filter(
        name="Yahoo Finance"
    ).update(
        is_active=False
    )


    # ========================================================
    # 6.3 BUILD HISTORICAL DATA IMPORT FORM
    # ========================================================

    # GET:
    #     Displays the form.
    #
    # POST:
    #     Validates the historical-data request.
    form = DataImportForm(
        request.POST or None,
        initial={
            "source":
                alpaca_source.pk,
        },
    )


    # ========================================================
    # 6.4 RESTRICT DATA SOURCE TO ALPACA
    # ========================================================

    # If DataImportForm contains a "source" field, only expose
    # Alpaca in this Data-tab workflow.
    #
    # This prevents the user from accidentally selecting the
    # old Yahoo Finance source.
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
    # 6.5 HANDLE NEW HISTORICAL DATA IMPORT
    # ========================================================

    if (
        request.method == "POST"
        and form.is_valid()
    ):


        # ----------------------------------------------------
        # Create DataImport without saving immediately
        # ----------------------------------------------------

        import_job = (
            form.save(
                commit=False
            )
        )


        # ----------------------------------------------------
        # Associate import with logged-in user
        # ----------------------------------------------------

        import_job.user = (
            request.user
        )


        # ----------------------------------------------------
        # Enforce Alpaca as the provider
        # ----------------------------------------------------

        # MarketPulse now uses Alpaca as the primary provider
        # for the Data-tab workflow.
        import_job.source = (
            alpaca_source
        )


        # ----------------------------------------------------
        # Standardise ticker symbol
        # ----------------------------------------------------

        # Examples:
        #
        # aapl
        # Aapl
        #
        # become:
        #
        # AAPL
        import_job.symbol = (
            import_job.symbol
            .strip()
            .upper()
        )


        # ----------------------------------------------------
        # Save import audit/history record
        # ----------------------------------------------------

        import_job.save()


        # ====================================================
        # 6.6 RUN HISTORICAL DATA IMPORT
        # ====================================================

        if getattr(
            settings,
            "USE_CELERY",
            False,
        ):

            # ------------------------------------------------
            # CELERY / BACKGROUND MODE
            # ------------------------------------------------

            process_data_import.delay(
                import_job.pk
            )


            messages.info(
                request,
                (
                    f"{import_job.symbol} historical market "
                    f"data import from Alpaca has been submitted."
                ),
            )


        else:

            # ------------------------------------------------
            # LOCAL DEVELOPMENT / COLLEGE DEMO MODE
            # ------------------------------------------------

            # Run synchronously so imported observations
            # become immediately available after redirect.
            process_data_import(
                import_job.pk
            )


            # ------------------------------------------------
            # Reload because process_data_import modifies it
            # ------------------------------------------------

            import_job.refresh_from_db()


            # ------------------------------------------------
            # SUCCESSFUL IMPORT
            # ------------------------------------------------

            if (
                import_job.status
                == "completed"
            ):

                messages.success(
                    request,
                    (
                        f"{import_job.symbol} imported successfully "
                        f"from Alpaca. "
                        f"{import_job.records_imported} historical "
                        f"market observations were stored."
                    ),
                )


            # ------------------------------------------------
            # FAILED IMPORT
            # ------------------------------------------------

            else:

                messages.error(
                    request,
                    (
                        f"{import_job.symbol} Alpaca import failed. "
                        f"{import_job.error_message}"
                    ),
                )


        # ====================================================
        # 6.7 REDIRECT BACK TO DATA PAGE
        # ====================================================

        data_page_url = reverse(
            "data_management:import"
        )


        # Example:
        #
        # /data/import/?symbol=AAPL
        return redirect(
            f"{data_page_url}?symbol={import_job.symbol}"
        )


    # ========================================================
    # 7. DETERMINE WHICH SYMBOL SHOULD BE DISPLAYED
    # ========================================================

    # First preference:
    #
    # Symbol supplied in the URL.
    #
    # Example:
    #
    # /data/import/?symbol=AAPL
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
    # 8. IF NO SYMBOL IN URL, USE MOST RECENT IMPORT
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
    # 9. IF STILL EMPTY, USE LATEST MARKETDATA SYMBOL
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
    # 10. PREPARE EMPTY MARKET DATA VALUES
    # ========================================================

    # Empty QuerySet prevents unrelated symbols from being
    # shown when no dataset has been selected.
    market_data = (
        MarketData.objects.none()
    )


    # Total number of observations for selected symbol.
    total_records = 0


    # Oldest historical observation.
    earliest_record = None


    # Most recent historical observation.
    latest_record = None


    # ========================================================
    # 11. LOAD HISTORICAL OHLCV DATA
    # ========================================================

    if selected_symbol:


        # ----------------------------------------------------
        # Retrieve every stored observation for the asset
        # ----------------------------------------------------

        all_symbol_data = (
            MarketData.objects
            .filter(
                symbol=selected_symbol
            )
        )


        # ----------------------------------------------------
        # Count observations
        # ----------------------------------------------------

        total_records = (
            all_symbol_data
            .count()
        )


        # ----------------------------------------------------
        # Earliest observation
        # ----------------------------------------------------

        earliest_record = (
            all_symbol_data
            .order_by(
                "date"
            )
            .first()
        )


        # ----------------------------------------------------
        # Latest observation
        # ----------------------------------------------------

        latest_record = (
            all_symbol_data
            .order_by(
                "-date"
            )
            .first()
        )


        # ----------------------------------------------------
        # Historical table rows
        # ----------------------------------------------------

        # Only the latest 250 observations are sent to the
        # browser.
        #
        # Older observations remain permanently stored in
        # PostgreSQL and remain available to:
        #
        # - Backtesting
        # - Forecasting
        # - Machine learning
        # - Risk analysis
        # - Market Condition analysis
        # - Strategy Robustness
        # - Stress testing
        market_data = (
            all_symbol_data
            .order_by(
                "-date"
            )[:250]
        )


    # ========================================================
    # 12. FIND ALL AVAILABLE IMPORTED SYMBOLS
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
    # 13. RECENT DATA IMPORT HISTORY
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
    # 14. LOAD COMPLETE STRATEGY & MODEL LIBRARY
    # ========================================================

    # Example structure:
    #
    # [
    #     {
    #         "code": "stochastic",
    #         "label": "Stochastic Models",
    #         "items": [...]
    #     },
    #     {
    #         "code": "time_series",
    #         "label": "Time-Series Models",
    #         "items": [...]
    #     },
    # ]
    strategy_categories = (
        get_grouped_strategy_library()
    )


    # ========================================================
    # 15. READ SELECTED MODEL FROM URL
    # ========================================================

    # Example:
    #
    # /data/import/?symbol=AAPL&model=gbm
    selected_model_code = (
        request.GET
        .get(
            "model",
            "",
        )
        .strip()
    )


    selected_model = None


    # ========================================================
    # 16. LOAD SELECTED MODEL
    # ========================================================

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
    # 17. MODEL + DATASET COMPATIBILITY INFORMATION
    # ========================================================

    dataset_available = bool(
        selected_symbol
        and total_records > 0
    )


    model_selected = (
        selected_model
        is not None
    )


    # ========================================================
    # 18. DATA PROVIDER / PROVENANCE INFORMATION
    # ========================================================

    # These values are intentionally passed to the template
    # so the user can clearly see where the data originates.
    #
    # This is useful for:
    #
    # - Transparency
    # - Reproducibility
    # - Lecturer demonstration
    # - Debugging
    market_data_provider = (
        "Alpaca"
    )


    market_data_feed = getattr(
        settings,
        "ALPACA_DATA_FEED",
        "iex",
    )


    market_data_feed = (
        str(
            market_data_feed
        )
        .upper()
    )


    # ========================================================
    # 19. SEND DATA TO IMPORT.HTML
    # ========================================================

    context = {


        # ====================================================
        # IMPORT FORM
        # ====================================================

        "form":
            form,


        # ====================================================
        # DATA PROVIDER
        # ====================================================

        "market_data_provider":
            market_data_provider,

        "market_data_feed":
            market_data_feed,

        "alpaca_source":
            alpaca_source,


        # ====================================================
        # SELECTED MARKET DATASET
        # ====================================================

        "selected_symbol":
            selected_symbol,


        # ====================================================
        # HISTORICAL OHLCV ROWS
        # ====================================================

        "market_data":
            market_data,


        # ====================================================
        # DATASET SUMMARY
        # ====================================================

        "total_records":
            total_records,

        "earliest_record":
            earliest_record,

        "latest_record":
            latest_record,


        # ====================================================
        # AVAILABLE IMPORTED SYMBOLS
        # ====================================================

        "available_symbols":
            available_symbols,


        # ====================================================
        # RECENT IMPORTS
        # ====================================================

        "recent_imports":
            recent_imports,


        # ====================================================
        # STRATEGY / MODEL LIBRARY
        # ====================================================

        "strategy_categories":
            strategy_categories,


        # ====================================================
        # SELECTED MODEL
        # ====================================================

        "selected_model":
            selected_model,


        # ====================================================
        # MODEL SELECTION STATUS
        # ====================================================

        "model_selected":
            model_selected,


        # ====================================================
        # DATASET STATUS
        # ====================================================

        "dataset_available":
            dataset_available,
    }


    # ========================================================
    # 20. RENDER DATA PAGE
    # ========================================================

    return render(
        request,
        "data_management/import.html",
        context,
    )


# ============================================================
# 21. IMPORT HISTORY VIEW
# ============================================================

@login_required
def import_history(request):
    """
    ============================================================
    MARKET DATA IMPORT HISTORY
    ============================================================

    FRAMEWORK FLOW:

    DataImport
        ↓
    import_history()
        ↓
    templates/data_management/history.html


    Displays:

    - Symbol
    - Provider
    - Start date
    - End date
    - Status
    - Number of imported records
    - Import date/time
    - Failed-import information

    ============================================================
    """


    # ========================================================
    # 21.1 LOAD LOGGED-IN USER'S IMPORTS
    # ========================================================

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


    # ========================================================
    # 21.2 BUILD TEMPLATE CONTEXT
    # ========================================================

    context = {

        # Preferred variable.
        "imports":
            imports,


        # Compatibility with an older history.html version.
        "jobs":
            imports,
    }


    # ========================================================
    # 21.3 RENDER IMPORT HISTORY PAGE
    # ========================================================

    return render(
        request,
        "data_management/history.html",
        context,
    )


# ============================================================
# 22. MARKET CONDITION ANALYSIS
# ============================================================

@login_required
def market_condition(request):
    """
    ============================================================
    MARKETPULSE - MARKET CONDITION
    ============================================================

    USER QUESTION:

        "What type of market environment has this asset
        recently been experiencing?"


    TECHNICAL METHOD:

        Market Regime Analysis


    FRAMEWORK FLOW:

    Alpaca Historical Market Data
        ↓
    core.MarketData
        ↓
    identify_market_regime()
        ↓
    analysis_tools.analyzers
        ↓
    MarketRegime
        ↓
    data_management/market_condition.html


    IMPORTANT:

    The technical term "Market Regime Analysis" remains
    visible for academic clarity.

    However, the user-facing feature is called:

        Market Condition

    because that makes its purpose easier to understand.

    ============================================================
    """


    # ========================================================
    # 22.1 FIND SYMBOLS WITH HISTORICAL DATA
    # ========================================================

    symbols = list(
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
    # 22.2 DETERMINE SELECTED SYMBOL
    # ========================================================

    # Selection priority:
    #
    # 1. Submitted POST symbol
    # 2. Symbol passed in URL
    # 3. First available historical symbol
    selected_symbol = (
        request.POST.get(
            "symbol"
        )
        or request.GET.get(
            "symbol"
        )
        or (
            symbols[0]
            if symbols
            else ""
        )
    )


    selected_symbol = (
        selected_symbol
        .strip()
        .upper()
    )


    # ========================================================
    # 22.3 PREPARE SYMBOL SUMMARY
    # ========================================================

    observation_count = 0

    earliest_record = None

    latest_record = None


    if selected_symbol:

        selected_data = (
            MarketData.objects
            .filter(
                symbol=selected_symbol
            )
        )


        observation_count = (
            selected_data.count()
        )


        earliest_record = (
            selected_data
            .order_by(
                "date"
            )
            .first()
        )


        latest_record = (
            selected_data
            .order_by(
                "-date"
            )
            .first()
        )


    # ========================================================
    # 22.4 HANDLE ANALYSIS REQUEST
    # ========================================================

    if request.method == "POST":


        # ----------------------------------------------------
        # Validate asset selection
        # ----------------------------------------------------

        if not selected_symbol:

            messages.error(
                request,
                (
                    "Please select an asset before running "
                    "Market Condition analysis."
                ),
            )


        # ----------------------------------------------------
        # Require sufficient historical data
        # ----------------------------------------------------

        elif observation_count < 20:

            messages.error(
                request,
                (
                    f"{selected_symbol} currently has only "
                    f"{observation_count} historical observations. "
                    "More historical data is required before "
                    "MarketPulse can estimate the market condition."
                ),
            )


        else:

            # =================================================
            # RUN INTERNAL MARKET REGIME ENGINE
            # =================================================

            try:

                regime_result = (
                    identify_market_regime(
                        selected_symbol
                    )
                )


                # ---------------------------------------------
                # Analysis completed
                # ---------------------------------------------

                if regime_result:

                    messages.success(
                        request,
                        (
                            "Market Condition analysis completed "
                            f"for {selected_symbol}."
                        ),
                    )


                    results_url = reverse(
                        "data_management:market_condition_results"
                    )


                    return redirect(
                        f"{results_url}?symbol={selected_symbol}"
                    )


                # ---------------------------------------------
                # Analyzer returned no result
                # ---------------------------------------------

                messages.error(
                    request,
                    (
                        "MarketPulse could not determine a market "
                        "condition from the available historical data."
                    ),
                )


            except Exception as error:

                # ---------------------------------------------
                # Prevent analytical failure from crashing page
                # ---------------------------------------------

                messages.error(
                    request,
                    (
                        "Market Condition analysis could not be "
                        f"completed: {error}"
                    ),
                )


    # ========================================================
    # 22.5 LOAD MOST RECENT RESULT FOR SELECTED ASSET
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
    # 22.6 BUILD TEMPLATE CONTEXT
    # ========================================================

    context = {

        "symbols":
            symbols,

        "selected_symbol":
            selected_symbol,

        "observation_count":
            observation_count,

        "earliest_record":
            earliest_record,

        "latest_record":
            latest_record,


        # ====================================================
        # MARKET CONDITION RESULT
        # ====================================================

        "latest_regime":
            latest_regime,


        # ====================================================
        # DATA PROVENANCE
        # ====================================================

        "market_data_provider":
            "Alpaca",

        "market_data_feed":
            str(
                getattr(
                    settings,
                    "ALPACA_DATA_FEED",
                    "iex",
                )
            ).upper(),
    }


    # ========================================================
    # 22.7 RENDER MARKET CONDITION PAGE
    # ========================================================

    return render(
        request,
        "data_management/market_condition.html",
        context,
    )


# ============================================================
# 23. MARKET CONDITION RESULTS
# ============================================================

@login_required
def market_condition_results(request):
    """
    ============================================================
    MARKET CONDITION RESULTS
    ============================================================

    Displays recent Market Regime / Market Condition results.

    If the URL contains:

        ?symbol=AAPL

    MarketPulse filters the results to AAPL.

    Otherwise it displays the most recent results across all
    analysed symbols.

    The Market Condition result itself is calculated by
    MarketPulse from historical observations stored in
    core.MarketData.

    Once the historical importer is fully migrated, those
    observations originate from Alpaca.
    ============================================================
    """


    # ========================================================
    # 23.1 READ OPTIONAL SYMBOL FILTER
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
    # 23.2 START WITH ALL RESULTS
    # ========================================================

    regimes = (
        MarketRegime.objects
        .all()
    )


    # ========================================================
    # 23.3 FILTER BY SYMBOL WHEN REQUESTED
    # ========================================================

    if selected_symbol:

        regimes = (
            regimes
            .filter(
                symbol=selected_symbol
            )
        )


    # ========================================================
    # 23.4 ORDER MOST RECENT FIRST
    # ========================================================

    regimes = (
        regimes
        .order_by(
            "-date",
            "-created_at",
        )[:20]
    )


    # ========================================================
    # 23.5 AVAILABLE ANALYSED SYMBOLS
    # ========================================================

    analysed_symbols = (
        MarketRegime.objects
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
    # 23.6 TEMPLATE CONTEXT
    # ========================================================

    context = {

        "regimes":
            regimes,

        "selected_symbol":
            selected_symbol,

        "analysed_symbols":
            analysed_symbols,


        # ====================================================
        # DATA PROVENANCE
        # ====================================================

        "market_data_provider":
            "Alpaca",

        "market_data_feed":
            str(
                getattr(
                    settings,
                    "ALPACA_DATA_FEED",
                    "iex",
                )
            ).upper(),
    }


    # ========================================================
    # 23.7 RENDER RESULT PAGE
    # ========================================================

    return render(
        request,
        "data_management/market_condition_results.html",
        context,
    )