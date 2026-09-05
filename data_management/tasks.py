"""
============================================================
DATA MANAGEMENT - CELERY TASKS
============================================================

FRAMEWORK MAPPING:

data_management/views.py
    ↓
process_data_import()

process_data_import()
    ↓
Reads the DataImport database record
    ↓
data_management/utils.py
    ↓
import_market_data()
    ↓
data_management/services/alpaca.py
    ↓
Alpaca Historical Market Data API
    ↓
core/models.py
    ↓
MarketData stores the historical OHLCV records


PRIMARY MARKET DATA PROVIDER:

Alpaca


PURPOSE:

This module coordinates historical market-data imports.

The task does not communicate with Alpaca directly.

Instead:

1. The view creates a DataImport database record.
2. This task manages the import-job lifecycle.
3. utils.py performs the MarketPulse import workflow.
4. services/alpaca.py communicates with Alpaca.
5. Normalised OHLCV observations are stored in MarketData.


EXECUTION MODES:

The task can run:

- synchronously during local development when USE_CELERY=False
- asynchronously through Celery/Redis when USE_CELERY=True


WHY THIS DESIGN IS USED:

Keeping the task separate from the external API service makes
the application easier to maintain and test.

The task is responsible for:

- job status
- error handling
- imported-record counts

The Alpaca service is responsible for:

- authentication
- HTTP requests
- market-data retrieval
- API response normalisation

============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

# Celery's shared_task decorator allows this function to run
# asynchronously when Celery is enabled in MarketPulse.
from celery import shared_task


# Import the DataImport model used to keep track of each
# historical-data import request.
from .models import DataImport


# Import the provider-neutral historical-data importer.
#
# IMPORTANT:
#
# import_market_data() will be implemented in utils.py and
# will use Alpaca as MarketPulse's primary historical-data
# provider.
#
# This replaces the old:
#
# import_yahoo_finance_data()
from .utils import import_market_data


# ============================================================
# 2. HISTORICAL MARKET DATA IMPORT TASK
# ============================================================

@shared_task
def process_data_import(import_id):

    """
    ========================================================
    PROCESS ONE HISTORICAL MARKET DATA IMPORT
    ========================================================

    Process one DataImport database record.

    The current primary market-data provider is Alpaca.

    Workflow:

    1. Retrieve the DataImport record.
    2. Mark the job as processing.
    3. Pass the requested symbol and date range to
       import_market_data().
    4. import_market_data() obtains historical OHLCV data
       through the Alpaca service.
    5. MarketData records are created or updated.
    6. Save the number of imported observations.
    7. Mark the job as completed.

    If an error occurs:

    1. Mark the import as failed.
    2. Store a readable error message.
    3. Return structured information about the failure.

    Keeping this task provider-neutral means the rest of
    MarketPulse does not need to know the details of the
    external market-data API.
    """


    # ========================================================
    # 2.1 RETRIEVE THE IMPORT JOB
    # ========================================================

    # Locate the DataImport database record created by the
    # Data tab when the user requested a historical import.
    try:

        import_job = DataImport.objects.get(
            pk=import_id
        )


    # --------------------------------------------------------
    # Import record does not exist
    # --------------------------------------------------------

    except DataImport.DoesNotExist:

        return {
            "status": "failed",
            "import_id": import_id,
            "provider": "Alpaca",
            "error": (
                "The requested DataImport record "
                "does not exist."
            ),
        }


    # ========================================================
    # 2.2 MARK THE IMPORT AS PROCESSING
    # ========================================================

    # Change the job status before starting the external
    # market-data request.
    #
    # records_imported is reset to zero so that an old value
    # cannot remain if the same job record is processed again.
    import_job.status = "processing"

    import_job.records_imported = 0

    import_job.error_message = ""


    import_job.save(
        update_fields=[
            "status",
            "records_imported",
            "error_message",
        ]
    )


    # ========================================================
    # 3. IMPORT ALPACA HISTORICAL MARKET DATA
    # ========================================================

    try:

        # ----------------------------------------------------
        # Provider-neutral import function
        # ----------------------------------------------------
        #
        # import_market_data() belongs in:
        #
        # data_management/utils.py
        #
        # That function will use:
        #
        # data_management/services/alpaca.py
        #
        # to retrieve historical OHLCV observations from
        # Alpaca and persist them in core.MarketData.
        records_imported = import_market_data(
            symbol=import_job.symbol,
            start_date=import_job.start_date,
            end_date=import_job.end_date,
        )


        # ====================================================
        # 3.1 SUCCESSFUL IMPORT
        # ====================================================

        import_job.status = "completed"

        import_job.records_imported = (
            records_imported
        )

        import_job.error_message = ""


        import_job.save(
            update_fields=[
                "status",
                "records_imported",
                "error_message",
            ]
        )


        # Return structured information that can also be
        # useful when this function is run through Celery.
        return {
            "status": "completed",
            "import_id": import_job.pk,
            "symbol": import_job.symbol,
            "provider": "Alpaca",
            "records_imported": records_imported,
        }


    # ========================================================
    # 4. IMPORT ERROR HANDLING
    # ========================================================

    except Exception as error:

        # ----------------------------------------------------
        # Mark the DataImport record as failed
        # ----------------------------------------------------

        import_job.status = "failed"

        import_job.records_imported = 0

        import_job.error_message = str(error)


        import_job.save(
            update_fields=[
                "status",
                "records_imported",
                "error_message",
            ]
        )


        # ----------------------------------------------------
        # Return structured error information
        # ----------------------------------------------------

        return {
            "status": "failed",
            "import_id": import_job.pk,
            "symbol": import_job.symbol,
            "provider": "Alpaca",
            "records_imported": 0,
            "error": str(error),
        }