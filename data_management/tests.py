"""============================================================ DATA FORM TEST: invalid date ranges are rejected without network calls. ============================================================"""
from django.test import TestCase
from .models import DataSource
from .forms import DataImportForm
class DataTests(TestCase):
    def test_dates(self):
        s=DataSource.objects.create(name='Yahoo Finance',url='https://finance.yahoo.com/'); f=DataImportForm(data={'source':s.pk,'symbol':'AAPL','start_date':'2026-02-02','end_date':'2026-01-01'}); self.assertFalse(f.is_valid())
