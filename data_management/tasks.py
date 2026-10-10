"""
DATA MANAGEMENT - CELERY TASKS
Coordinate historical import jobs using Django models and Celery.
Flow: views.py → this task → utils.import_market_data() → Alpaca service → MarketData.
This task manages job status, processed-record counts and error messages.
The caller chooses direct execution or background execution through .delay().
"""
# ============================================================
# 1. IMPORTS
# ============================================================
from celery import shared_task  # I import the decorator that makes this function a reusable Celery task.
from .models import DataImport  # I import the model that tracks historical import jobs.
from .utils import import_market_data  # I import the provider-neutral historical-data importer.
# ============================================================
# 2. HISTORICAL DATA IMPORT TASK
# ============================================================
@shared_task  # I register this function as a task usable with the configured Celery application.
def process_data_import(import_id):  # I receive the database ID of the import job to process.
    """Process one import job and return structured success or failure information."""
    # --------------------------------------------------------
    # 2.1 RETRIEVE THE IMPORT JOB
    # --------------------------------------------------------
    try:  # I attempt to retrieve the requested database record.
        import_job = DataImport.objects.get(  # I ask Django's ORM for one matching import job.
            pk=import_id  # I match its primary key against the supplied ID.
        )  # I finish retrieving the job.
    except DataImport.DoesNotExist:  # I handle a missing import record.
        return {  # I exit early with a failure dictionary.
            "status": "failed",  # I report that processing could not proceed.
            "import_id": import_id,  # I include the requested ID.
            "provider": "Alpaca",  # I identify the current provider.
            "error": (  # I begin the error message.
                "The requested DataImport record "  # I identify the missing record.
                "does not exist."  # I finish the explanation.
            ),  # I finish the combined string.
        }  # I finish the returned dictionary.
    # --------------------------------------------------------
    # 2.2 MARK THE JOB AS PROCESSING
    # --------------------------------------------------------
    import_job.status = "processing"  # I set the job's application status before importing.
    import_job.records_imported = 0  # I clear any previous processed-record count.
    import_job.error_message = ""  # I clear any previous error message.
    import_job.save(  # I persist these changes to the database.
        update_fields=[  # I restrict the save to the listed model fields.
            "status",  # I save the processing status.
            "records_imported",  # I save the reset count.
            "error_message",  # I save the cleared error message.
        ]  # I finish the field list.
    )  # I finish saving the processing state.
    # --------------------------------------------------------
    # 2.3 IMPORT HISTORICAL DATA
    # --------------------------------------------------------
    try:  # I handle errors raised during importing or the success updates.
        records_imported = import_market_data(  # I call the importer and retain its processed-record count.
            symbol=import_job.symbol,  # I supply the job's market symbol.
            start_date=import_job.start_date,  # I supply the requested start date.
            end_date=import_job.end_date,  # I supply the requested end date.
        )  # I finish the import call; its default timeframe remains unchanged.
        # ----------------------------------------------------
        # 2.4 SAVE SUCCESS
        # ----------------------------------------------------
        import_job.status = "completed"  # I mark the import job as completed.
        import_job.records_imported = records_imported  # I store the count returned by the importer.
        import_job.error_message = ""  # I ensure the completed job has no stored error message.
        import_job.save(  # I persist the successful outcome.
            update_fields=[  # I specify which fields to update.
                "status",  # I save the completed status.
                "records_imported",  # I save the processed-record count.
                "error_message",  # I save the empty error message.
            ]  # I finish the field list.
        )  # I finish saving the outcome.
        return {  # I return structured success information.
            "status": "completed",  # I report successful job completion.
            "import_id": import_job.pk,  # I include the saved job's primary key.
            "symbol": import_job.symbol,  # I include the imported symbol.
            "provider": "Alpaca",  # I identify the provider.
            "records_imported": records_imported,  # I include the number of processed bars.
        }  # I finish the success dictionary.
    # --------------------------------------------------------
    # 2.5 SAVE AND RETURN FAILURE
    # --------------------------------------------------------
    except Exception as error:  # I catch an exception raised inside the preceding try block.
        import_job.status = "failed"  # I mark the import job as failed.
        import_job.records_imported = 0  # I reset the job's recorded count to zero.
        import_job.error_message = str(error)  # I convert the exception into readable text.
        import_job.save(  # I persist the failure information.
            update_fields=[  # I specify which fields to update.
                "status",  # I save the failed status.
                "records_imported",  # I save the zero count.
                "error_message",  # I save the exception message.
            ]  # I finish the field list.
        )  # I finish saving the failure.
        return {  # I return structured failure information.
            "status": "failed",  # I report the application-level failure.
            "import_id": import_job.pk,  # I include the affected job's ID.
            "symbol": import_job.symbol,  # I include its market symbol.
            "provider": "Alpaca",  # I identify the provider.
            "records_imported": 0,  # I report the reset job count.
            "error": str(error),  # I include the readable exception message.
        }  # I finish the failure dictionary.