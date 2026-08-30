"""============================================================
CELERY IMPORT TASK
Framework mapping: optional Redis worker → yfinance service → DataImport status + MarketData.
============================================================"""
from celery import shared_task
from .models import DataImport
from .utils import import_yahoo_finance_data
@shared_task
def import_market_data_task(pk):
    j=DataImport.objects.get(pk=pk); j.status='processing'; j.save()
    try:j.records_imported=import_yahoo_finance_data(j.symbol,j.start_date,j.end_date); j.status='completed'; j.error_message=''
    except Exception as e:j.status='failed'; j.error_message=str(e)
    j.save(); return j.status
