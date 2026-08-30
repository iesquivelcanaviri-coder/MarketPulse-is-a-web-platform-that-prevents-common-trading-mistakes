""" ============================================================
DATA MANAGEMENT - VIEWS
============================================================
FRAMEWORK MAPPING:
Yahoo Finance
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
    +
Strategy & Model selector

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

PURPOSE OF THE DATA TAB:
The Data tab is responsible for:
1. Importing historical market data.
2. Saving imported data into core.MarketData.
3. Displaying historical OHLCV data:
   - Date
   - Open
   - High
   - Low
   - Close
   - Volume

4. Remembering the most recently imported symbol.
5. Allowing the user to switch between imported symbols.
6. Displaying recent import history.
7. Loading the MarketPulse Strategy & Model Library.
8. Allowing the user to select a quantitative model
   against the currently selected dataset.
9. Providing historical data to:
   - Strategy Builder
   - Backtesting
   - Risk Management
   - Overfitting Detection
   - Market Regime Detection
   - Stress Testing
   - Model Runner
============================================================"""
# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

# Django settings are used to determine whether Celery
# should run imports asynchronously.
from django.conf import settings


# Django messages allow success, information and error
# messages to appear in the shared base.html template.
from django.contrib import messages


# Only authenticated users should be able to import,
# inspect and test market data.
from django.contrib.auth.decorators import login_required


# redirect:
# Sends the browser to another URL.
#
# render:
# Combines a Django template with context data.
from django.shortcuts import redirect, render


# reverse converts a named Django URL into its actual path.
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

# MarketData stores the historical OHLCV observations
# downloaded from Yahoo Finance.
from core.models import MarketData


# ============================================================
# 3. DATA MANAGEMENT IMPORTS
# ============================================================

# DataImportForm validates:
#
# - Source
# - Symbol
# - Start date
# - End date
from .forms import DataImportForm


# DataSource:
# Stores external market-data providers.
#
# DataImport:
# Stores an audit/history record for every import request.
from .models import DataImport, DataSource


# process_data_import connects the import request to:
#
# Yahoo Finance
#     ↓
# data_management/utils.py
#     ↓
# core.MarketData
from .tasks import process_data_import


# ============================================================
# 4. STRATEGY & MODEL LIBRARY IMPORTS
# ============================================================

# This service groups all library entries by their
# academic/model category.
#
# Examples:
#
# Stochastic Models
# Time-Series Models
# Machine Learning Models
# Factor Models
# Portfolio Optimisation
# Derivatives Pricing
# Simulation & Monte Carlo
from strategy_builder.library import (
    get_grouped_strategy_library,
)


# StrategyLibraryItem stores the metadata for each
# quantitative model available in MarketPulse.
from strategy_builder.models import (
    StrategyLibraryItem,
)


# ============================================================
# 5. HISTORICAL MARKET DATA IMPORT VIEW
# ============================================================

@login_required
def data_import(request):
    """
    ============================================================
    HISTORICAL MARKET DATA + MODEL SELECTION
    ============================================================

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
    Yahoo Finance
        ↓
    core.MarketData
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


    OHLCV means:

    O = Open
    H = High
    L = Low
    C = Close
    V = Volume

    ============================================================
    """


    # ========================================================
    # 5.1 MAKE SURE YAHOO FINANCE EXISTS
    # ========================================================

    # update_or_create() makes this self-healing.
    #
    # If Yahoo Finance does not exist:
    #     it is created.
    #
    # If it already exists:
    #     its URL and active status are refreshed.
    DataSource.objects.update_or_create(

        name="Yahoo Finance",

        defaults={
            "url": "https://finance.yahoo.com/",
            "is_active": True,
        },

    )


    # ========================================================
    # 5.2 BUILD HISTORICAL DATA IMPORT FORM
    # ========================================================

    # GET request:
    #     Shows an empty form.
    #
    # POST request:
    #     request.POST contains the user's submitted values.
    form = DataImportForm(
        request.POST or None
    )


    # ========================================================
    # 5.3 HANDLE NEW HISTORICAL DATA IMPORT
    # ========================================================

    if request.method == "POST" and form.is_valid():


        # ----------------------------------------------------
        # Create DataImport without saving immediately
        # ----------------------------------------------------

        import_job = form.save(
            commit=False
        )


        # ----------------------------------------------------
        # Associate import with logged-in user
        # ----------------------------------------------------

        import_job.user = request.user


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
        # Save DataImport audit/history record
        # ----------------------------------------------------

        import_job.save()


        # ====================================================
        # 5.4 RUN THE HISTORICAL DATA IMPORT
        # ====================================================

        if getattr(
            settings,
            "USE_CELERY",
            False,
        ):

            # ------------------------------------------------
            # CELERY / BACKGROUND MODE
            # ------------------------------------------------

            # Production can run this in the background.
            process_data_import.delay(
                import_job.pk
            )


            messages.info(
                request,
                (
                    f"{import_job.symbol} historical market "
                    f"data import has been submitted."
                ),
            )


        else:

            # ------------------------------------------------
            # LOCAL DEVELOPMENT / COLLEGE DEMO MODE
            # ------------------------------------------------

            # Run synchronously so the imported values are
            # immediately available when the page reloads.
            process_data_import(
                import_job.pk
            )


            # ------------------------------------------------
            # Reload job because task changed its fields
            # ------------------------------------------------

            import_job.refresh_from_db()


            # ------------------------------------------------
            # SUCCESSFUL IMPORT
            # ------------------------------------------------

            if import_job.status == "completed":

                messages.success(
                    request,
                    (
                        f"{import_job.symbol} imported successfully. "
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
                        f"{import_job.symbol} import failed. "
                        f"{import_job.error_message}"
                    ),
                )


        # ====================================================
        # 5.5 REDIRECT BACK TO DATA PAGE
        # ====================================================

        # Named URL:
        #
        # data_management:import
        #
        # becomes:
        #
        # /data/import/
        data_page_url = reverse(
            "data_management:import"
        )


        # Redirect example:
        #
        # /data/import/?symbol=AAPL
        #
        # This tells the Data page which dataset should be
        # displayed immediately after importing.
        return redirect(
            f"{data_page_url}?symbol={import_job.symbol}"
        )


    # ========================================================
    # 6. DETERMINE WHICH SYMBOL SHOULD BE DISPLAYED
    # ========================================================

    # First preference:
    #
    # Read ticker from URL.
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
    # 7. IF NO SYMBOL IN URL, USE MOST RECENT IMPORT
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
    # 8. IF STILL EMPTY, USE LATEST MARKETDATA SYMBOL
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
    # 9. PREPARE EMPTY MARKET DATA VALUES
    # ========================================================

    # Empty QuerySet avoids returning unrelated market data
    # when no symbol has been selected.
    market_data = MarketData.objects.none()


    # Total number of stored rows for selected asset.
    total_records = 0


    # Oldest stored historical record.
    earliest_record = None


    # Latest stored historical record.
    latest_record = None


    # ========================================================
    # 10. LOAD HISTORICAL OHLCV DATA
    # ========================================================

    if selected_symbol:


        # ----------------------------------------------------
        # Retrieve every stored observation for selected asset
        # ----------------------------------------------------

        all_symbol_data = (
            MarketData.objects
            .filter(
                symbol=selected_symbol
            )
        )


        # ----------------------------------------------------
        # Count total observations
        # ----------------------------------------------------

        total_records = (
            all_symbol_data
            .count()
        )


        # ----------------------------------------------------
        # Earliest stored observation
        # ----------------------------------------------------

        earliest_record = (
            all_symbol_data
            .order_by(
                "date"
            )
            .first()
        )


        # ----------------------------------------------------
        # Latest stored observation
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

        # Display newest 250 rows.
        #
        # IMPORTANT:
        # This does NOT delete or limit the underlying database.
        #
        # Every imported observation remains available for:
        #
        # - Backtesting
        # - Forecasting
        # - Machine learning
        # - Risk analysis
        # - Stress testing
        market_data = (
            all_symbol_data
            .order_by(
                "-date"
            )[:250]
        )


    # ========================================================
    # 11. FIND ALL AVAILABLE IMPORTED SYMBOLS
    # ========================================================

    # Used to create symbol-selection buttons on the Data page.
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
    # 12. RECENT DATA IMPORT HISTORY
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
    # 13. LOAD COMPLETE STRATEGY & MODEL LIBRARY
    # ========================================================

    # Returns data structured approximately as:
    #
    # [
    #     {
    #         "code": "stochastic",
    #         "label": "1. Stochastic Models",
    #         "items": [...]
    #     },
    #     {
    #         "code": "time_series",
    #         "label": "2. Time-Series Models",
    #         "items": [...]
    #     },
    # ]
    #
    # This lets the template display HTML <optgroup>
    # sections grouped by category.
    strategy_categories = (
        get_grouped_strategy_library()
    )


    # ========================================================
    # 14. READ SELECTED MODEL FROM URL
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


    # Default:
    #
    # No model selected.
    selected_model = None


    # ========================================================
    # 15. LOAD SELECTED MODEL
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
    # 16. MODEL + DATASET COMPATIBILITY INFORMATION
    # ========================================================

    # This does not execute the model yet.
    #
    # It gives the template useful information about whether
    # a dataset is currently available.
    dataset_available = (
        selected_symbol
        and total_records > 0
    )


    # Minimum general flag for the next phase.
    #
    # Some advanced models will later require:
    #
    # - multiple assets
    # - factor data
    # - option inputs
    # - interest-rate data
    # - fundamental data
    #
    # Therefore selecting a model does not automatically mean
    # it is executable against single-asset Yahoo OHLCV data.
    model_selected = (
        selected_model is not None
    )


    # ========================================================
    # 17. SEND EVERYTHING TO IMPORT.HTML
    # ========================================================

    context = {
        # ====================================================
        # IMPORT FORM
        # ====================================================
        "form":
            form,
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
        # ===================================================
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
    # 18. RENDER DATA PAGE
    # ========================================================

    return render(
        request,
        "data_management/import.html",
        context,
    )


# ============================================================
# 19. IMPORT HISTORY VIEW
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

    The page displays:

    - Symbol
    - Source
    - Start date
    - End date
    - Status
    - Number of imported records
    - Import date/time
    - Failed import information

    ============================================================
    """


    # ========================================================
    # 19.1 LOAD LOGGED-IN USER'S IMPORTS
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
    # 19.2 BUILD TEMPLATE CONTEXT
    # ========================================================

    context = {


        # Preferred variable for current history.html.
        "imports":
            imports,


        # Compatibility with an older version of history.html
        # that may still contain:
        #
        # {% for job in jobs %}
        "jobs":
            imports,
    }


    # ========================================================
    # 19.3 RENDER IMPORT HISTORY PAGE
    # ========================================================

    return render(
        request,
        "data_management/history.html",
        context,
    )