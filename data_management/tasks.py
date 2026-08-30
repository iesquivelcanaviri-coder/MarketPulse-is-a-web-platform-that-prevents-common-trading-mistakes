"""
============================================================
DATA MANAGEMENT - CELERY TASKS
============================================================

FRAMEWORK MAPPING:

data_management/views.py
    -> calls process_data_import()

process_data_import()
    -> reads the DataImport database record

data_management/utils.py
    -> import_yahoo_finance_data() retrieves Yahoo Finance data

core/models.py
    -> MarketData stores the historical OHLCV records

The task can run:
- synchronously during local development
- asynchronously through Celery/Redis in production
============================================================
"""

# ============================================================
# 1. IMPORTS
# ============================================================

from celery import shared_task

from .models import DataImport
from .utils import import_yahoo_finance_data


# ============================================================
# 2. HISTORICAL MARKET DATA IMPORT TASK
# ============================================================

@shared_task
def process_data_import(import_id):

    """
    Import Yahoo Finance historical market data for one
    DataImport database record.

    The function:

    1. Finds the DataImport record.
    2. Marks it as processing.
    3. Calls the Yahoo Finance import service.
    4. Saves the number of imported records.
    5. Marks the import completed or failed.
    """

    # --------------------------------------------------------
    # Retrieve the import request
    # --------------------------------------------------------

    import_job = DataImport.objects.get(
        pk=import_id
    )


    # --------------------------------------------------------
    # Mark import as processing
    # --------------------------------------------------------

    import_job.status = "processing"

    import_job.error_message = ""

    import_job.save(
        update_fields=[
            "status",
            "error_message",
        ]
    )


    # ========================================================
    # 3. DOWNLOAD AND STORE YAHOO FINANCE DATA
    # ========================================================

    try:

        records_imported = import_yahoo_finance_data(
            symbol=import_job.symbol,
            start_date=import_job.start_date,
            end_date=import_job.end_date,
        )


        # ----------------------------------------------------
        # Successful import
        # ----------------------------------------------------

        import_job.status = "completed"

        import_job.records_imported = records_imported

        import_job.error_message = ""

        import_job.save(
            update_fields=[
                "status",
                "records_imported",
                "error_message",
            ]
        )


        return {
            "status": "completed",
            "symbol": import_job.symbol,
            "records_imported": records_imported,
        }


    # ========================================================
    # 4. IMPORT ERROR HANDLING
    # ========================================================

    except Exception as error:

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


        return {
            "status": "failed",
            "symbol": import_job.symbol,
            "error": str(error),
        }