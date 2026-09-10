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
Historical Open, High, Low, Close and Volume table


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
    ↓
User selects stored asset
    ↓
Run Market Condition analysis
    ↓
MarketRegime result saved
    ↓
Redirect back to Market Condition workspace
    ↓
Latest classification displayed on same page


PURPOSE OF THE DATA TAB:

The Data tab is responsible for:

1. Importing historical market data from Alpaca.
2. Saving imported observations into core.MarketData.
3. Displaying historical Open, High, Low, Close and Volume data.
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

The old separate Analysis navigation tab is no longer exposed
through the user interface.

analysis_tools remains an INTERNAL analytics engine.

The user-facing location for Market Regime Analysis is:

Data
    ↓
Market Condition


MARKET CONDITION UX:

The Data page acts as the entry point.

The dedicated Market Condition workspace is responsible for:

- Choosing an imported asset.
- Running Market Regime Analysis.
- Displaying the current historical classification.
- Displaying confidence and volatility.
- Explaining the result in user-friendly language.

The user stays on the Market Condition page after analysis.


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

from django.conf import settings

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.shortcuts import redirect, render

from django.urls import reverse


# ============================================================
# 2. CORE MARKET DATA IMPORT
# ============================================================

from core.models import MarketData


# ============================================================
# 3. DATA MANAGEMENT IMPORTS
# ============================================================

from .forms import DataImportForm

from .models import (
    DataImport,
    DataSource,
)

from .tasks import process_data_import


# ============================================================
# 4. STRATEGY & MODEL LIBRARY IMPORTS
# ============================================================

from strategy_builder.library import (
    get_grouped_strategy_library,
)

from strategy_builder.models import (
    StrategyLibraryItem,
)


# ============================================================
# 5. INTERNAL ANALYTICS ENGINE IMPORTS
# ============================================================

from analysis_tools.analyzers import (
    identify_market_regime,
)

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
    Historical market-data table


    MARKET CONDITION SUMMARY FLOW:

    MarketRegime
        ↓
    data_import()
        ↓
    latest_regime
        ↓
    import.html
        ↓
    Latest Market Condition can be summarised
    inside the main Data workspace


    DEDICATED ANALYSIS FLOW:

    Data workspace
        ↓
    Open Market Condition Analysis
        ↓
    market_condition()
        ↓
    market_condition.html


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

    ============================================================
    """


    # ========================================================
    # 6.1 ENSURE ALPACA DATA SOURCE EXISTS
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
    # 6.2 DISABLE LEGACY YAHOO FINANCE SOURCE
    # ========================================================

    DataSource.objects.filter(
        name="Yahoo Finance"
    ).update(
        is_active=False
    )


    # ========================================================
    # 6.3 BUILD HISTORICAL DATA IMPORT FORM
    # ========================================================

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
        # Enforce Alpaca as provider
        # ----------------------------------------------------

        import_job.source = (
            alpaca_source
        )


        # ----------------------------------------------------
        # Standardise ticker symbol
        # ----------------------------------------------------

        import_job.symbol = (
            import_job.symbol
            .strip()
            .upper()
        )


        # ----------------------------------------------------
        # Save import audit record
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

            process_data_import(
                import_job.pk
            )


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


        return redirect(
            f"{data_page_url}?symbol={import_job.symbol}"
        )


    # ========================================================
    # 7. DETERMINE WHICH SYMBOL SHOULD BE DISPLAYED
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

    market_data = (
        MarketData.objects.none()
    )


    total_records = 0

    earliest_record = None

    latest_record = None


    # ========================================================
    # 11. LOAD HISTORICAL MARKET DATA
    # ========================================================

    if selected_symbol:


        all_symbol_data = (
            MarketData.objects
            .filter(
                symbol=selected_symbol
            )
        )


        total_records = (
            all_symbol_data
            .count()
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

    strategy_categories = (
        get_grouped_strategy_library()
    )


    # ========================================================
    # 15. READ SELECTED MODEL FROM URL
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
    # 18. LOAD LATEST MARKET CONDITION SUMMARY
    # ========================================================

    # The main Data page may still show the most recently
    # calculated Market Condition as a summary.
    #
    # The actual analysis is performed in the dedicated
    # Market Condition workspace.

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
    # 19. DATA PROVIDER / PROVENANCE INFORMATION
    # ========================================================

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
    # 20. SEND DATA TO IMPORT.HTML
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
        # HISTORICAL MARKET DATA
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


        # ====================================================
        # MARKET CONDITION SUMMARY
        # ====================================================

        "latest_regime":
            latest_regime,
    }


    # ========================================================
    # 21. RENDER DATA PAGE
    # ========================================================

    return render(
        request,
        "data_management/import.html",
        context,
    )


# ============================================================
# 22. IMPORT HISTORY VIEW
# ============================================================

@login_required
def import_history(request):
    """
    ============================================================
    MARKET DATA IMPORT HISTORY
    ============================================================

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

        "jobs":
            imports,
    }


    return render(
        request,
        "data_management/history.html",
        context,
    )


# ============================================================
# 23. MARKET CONDITION ANALYSIS
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


    USER-FACING WORKFLOW:

    Data Workspace
        ↓
    Open Market Condition Analysis
        ↓
    Market Condition workspace
        ↓
    Choose stored dataset
        ↓
    Click Analyse Market Condition
        ↓
    identify_market_regime()
        ↓
    MarketRegime saved
        ↓
    Redirect back to SAME Market Condition workspace
        ↓
    New result displayed


    IMPORTANT:

    The Market Condition page is a dedicated sub-workspace
    belonging to the Data section.

    After analysis the user stays on this page.

    They return to the main Data page only by intentionally
    selecting:

        Back to Data

    ============================================================
    """


    # ========================================================
    # 23.1 FIND SYMBOLS WITH HISTORICAL DATA
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
    # 23.2 DETERMINE SELECTED SYMBOL
    # ========================================================

    # Selection priority:
    #
    # 1. Submitted POST symbol
    # 2. Symbol supplied in URL
    # 3. First stored historical symbol

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
    # 23.3 PREPARE SYMBOL SUMMARY
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
            selected_data
            .count()
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
    # 23.4 HANDLE ANALYSIS REQUEST
    # ========================================================

    if request.method == "POST":


        # ----------------------------------------------------
        # NO SYMBOL SELECTED
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
        # NOT ENOUGH HISTORICAL DATA
        # ----------------------------------------------------

        elif observation_count < 20:

            messages.error(
                request,
                (
                    f"{selected_symbol} currently has only "
                    f"{observation_count} historical observations. "
                    "At least 20 observations are required before "
                    "MarketPulse can estimate the Market Condition."
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
                # ANALYSIS COMPLETED SUCCESSFULLY
                # ---------------------------------------------

                if regime_result:

                    messages.success(
                        request,
                        (
                            "Market Condition analysis completed "
                            f"for {selected_symbol}."
                        ),
                    )


                    # =========================================
                    # IMPORTANT UX CHANGE
                    # =========================================
                    #
                    # Keep the user inside the dedicated
                    # Market Condition workspace.
                    #
                    # Example:
                    #
                    # /data/market-condition/?symbol=MSFT

                    market_condition_url = reverse(
                        "data_management:market_condition"
                    )


                    return redirect(
                        f"{market_condition_url}"
                        f"?symbol={selected_symbol}"
                    )


                # ---------------------------------------------
                # ANALYZER RETURNED NO RESULT
                # ---------------------------------------------

                messages.error(
                    request,
                    (
                        "MarketPulse could not determine a "
                        "Market Condition from the available "
                        "historical data."
                    ),
                )


            except Exception as error:

                # ---------------------------------------------
                # ANALYTICAL ERROR
                # ---------------------------------------------

                messages.error(
                    request,
                    (
                        "Market Condition analysis could not be "
                        f"completed: {error}"
                    ),
                )


    # ========================================================
    # 23.5 LOAD MOST RECENT RESULT FOR SELECTED ASSET
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
    # 23.6 BUILD TEMPLATE CONTEXT
    # ========================================================

    context = {

        # ====================================================
        # AVAILABLE DATASETS
        # ====================================================

        "symbols":
            symbols,


        # ====================================================
        # SELECTED DATASET
        # ====================================================

        "selected_symbol":
            selected_symbol,


        # ====================================================
        # DATASET SUMMARY
        # ====================================================

        "observation_count":
            observation_count,

        "earliest_record":
            earliest_record,

        "latest_record":
            latest_record,


        # ====================================================
        # LATEST MARKET CONDITION
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
    # 23.7 RENDER MARKET CONDITION WORKSPACE
    # ========================================================

    return render(
        request,
        "data_management/market_condition.html",
        context,
    )


# ============================================================
# 24. LEGACY MARKET CONDITION RESULTS ROUTE
# ============================================================

@login_required
def market_condition_results(request):
    """
    ============================================================
    LEGACY MARKET CONDITION RESULTS ROUTE
    ============================================================

    Older MarketPulse code used:

        /data/market-condition/results/

    and attempted to render:

        data_management/market_condition_results.html


    The current architecture no longer requires a separate
    results template.

    Market Condition analysis and its result are now displayed
    together inside:

        data_management/market_condition.html


    WHY KEEP THIS VIEW?

    Older links, bookmarks or URL patterns might still point to:

        /data/market-condition/results/?symbol=AAPL


    Instead of producing:

        TemplateDoesNotExist

    this compatibility view redirects the user into the current
    Market Condition workspace.

    ============================================================
    """


    # ========================================================
    # 24.1 READ OPTIONAL SYMBOL
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
    # 24.2 IF NO SYMBOL, USE MOST RECENT ANALYSED SYMBOL
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
    # 24.3 REDIRECT TO CURRENT MARKET CONDITION WORKSPACE
    # ========================================================

    market_condition_url = reverse(
        "data_management:market_condition"
    )


    if selected_symbol:

        return redirect(
            f"{market_condition_url}"
            f"?symbol={selected_symbol}"
        )


    return redirect(
        market_condition_url
    )