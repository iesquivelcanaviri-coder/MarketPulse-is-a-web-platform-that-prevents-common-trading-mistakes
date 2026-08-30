"""
============================================================
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

PURPOSE:

The Data tab is responsible for:

1. Importing historical market data.
2. Saving the imported data into MarketData.
3. Showing the imported OHLCV data.
4. Remembering the most recently imported symbol.
5. Providing data to strategies, backtesting,
   risk management and analysis tools.

============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from core.models import MarketData

from .forms import DataImportForm
from .models import DataImport, DataSource
from .tasks import process_data_import


# ============================================================
# 2. HISTORICAL MARKET DATA IMPORT VIEW
# ============================================================

@login_required
def data_import(request):

    # ========================================================
    # 2.1 MAKE SURE YAHOO FINANCE EXISTS
    # ========================================================

    yahoo_source, _ = DataSource.objects.update_or_create(

        name="Yahoo Finance",

        defaults={
            "url": "https://finance.yahoo.com/",
            "is_active": True,
        },

    )


    # ========================================================
    # 2.2 BUILD IMPORT FORM
    # ========================================================

    form = DataImportForm(
        request.POST or None
    )


    # ========================================================
    # 2.3 HANDLE NEW IMPORT
    # ========================================================

    if request.method == "POST" and form.is_valid():

        import_job = form.save(
            commit=False
        )


        # ----------------------------------------------------
        # Connect import to logged-in user
        # ----------------------------------------------------

        import_job.user = request.user


        # ----------------------------------------------------
        # Standardise ticker symbol
        # ----------------------------------------------------

        import_job.symbol = (
            import_job.symbol
            .strip()
            .upper()
        )


        # ----------------------------------------------------
        # Save import request
        # ----------------------------------------------------

        import_job.save()


        # ====================================================
        # 2.4 RUN YAHOO FINANCE IMPORT
        # ====================================================

        if getattr(
            settings,
            "USE_CELERY",
            False,
        ):

            # ------------------------------------------------
            # Background mode
            # ------------------------------------------------

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
            # Local development / lecturer demonstration
            # ------------------------------------------------

            # Run immediately so imported values can appear
            # in the table after the redirect.
            process_data_import(
                import_job.pk
            )


            # Reload updated DataImport status.
            import_job.refresh_from_db()


            # ------------------------------------------------
            # Successful import
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
            # Failed import
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
        # 2.5 REDIRECT BACK TO DATA PAGE
        # ====================================================

        # Example:
        #
        # /data/import/?symbol=AAPL

        url = reverse(
            "data_management:import"
        )

        return redirect(
            f"{url}?symbol={import_job.symbol}"
        )


    # ========================================================
    # 3. FIND WHICH SYMBOL SHOULD BE DISPLAYED
    # ========================================================

    # First preference:
    #
    # URL:
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
    # 4. IF NO SYMBOL IS IN URL, USE MOST RECENT IMPORT
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
    # 5. IF STILL EMPTY, USE MOST RECENT MARKETDATA SYMBOL
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
    # 6. PREPARE MARKET DATA VALUES
    # ========================================================

    market_data = MarketData.objects.none()

    total_records = 0

    earliest_record = None

    latest_record = None


    # ========================================================
    # 7. LOAD HISTORICAL OHLCV DATA
    # ========================================================

    if selected_symbol:

        all_symbol_data = (
            MarketData.objects
            .filter(
                symbol=selected_symbol
            )
        )


        # ----------------------------------------------------
        # Total number of stored observations
        # ----------------------------------------------------

        total_records = (
            all_symbol_data
            .count()
        )


        # ----------------------------------------------------
        # Oldest historical row
        # ----------------------------------------------------

        earliest_record = (
            all_symbol_data
            .order_by(
                "date"
            )
            .first()
        )


        # ----------------------------------------------------
        # Most recent historical row
        # ----------------------------------------------------

        latest_record = (
            all_symbol_data
            .order_by(
                "-date"
            )
            .first()
        )


        # ----------------------------------------------------
        # Table data
        # ----------------------------------------------------

        # Show the newest 250 rows on the Data page.
        #
        # All imported records remain stored in the database
        # even though only 250 are displayed at once.

        market_data = (
            all_symbol_data
            .order_by(
                "-date"
            )[:250]
        )


    # ========================================================
    # 8. GET ALL AVAILABLE SYMBOLS
    # ========================================================

    available_symbols = (
        MarketData.objects
        .order_by("symbol")
        .values_list(
            "symbol",
            flat=True,
        )
        .distinct()
    )


    # ========================================================
    # 9. IMPORT HISTORY
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
    # 10. SEND EVERYTHING TO IMPORT.HTML
    # ========================================================

    context = {

        "form":
            form,

        "selected_symbol":
            selected_symbol,

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

        "recent_imports":
            recent_imports,
    }


    return render(
        request,
        "data_management/import.html",
        context,
    )


# ============================================================
# 11. IMPORT HISTORY VIEW
# ============================================================

@login_required
def import_history(request):

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

        # Compatibility with an older history template.
        "jobs":
            imports,
    }


    return render(
        request,
        "data_management/history.html",
        context,
    )