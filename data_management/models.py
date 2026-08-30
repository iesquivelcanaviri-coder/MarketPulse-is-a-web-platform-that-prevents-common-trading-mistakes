"""
============================================================
DATA MANAGEMENT - MODELS
============================================================
Framework mapping: form/view/task track imports here; OHLCV observations are stored in core.MarketData.
"""
from django.conf import settings
from django.db import models
from core.models import TimeStampedModel
class DataSource(TimeStampedModel):
    name=models.CharField(max_length=100,unique=True); url=models.URLField(); api_key_required=models.BooleanField(default=False); is_active=models.BooleanField(default=True)
    def __str__(self):return self.name
class DataImport(TimeStampedModel):
    STATUS=[('pending','Pending'),('processing','Processing'),('completed','Completed'),('failed','Failed')]
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='data_imports'); source=models.ForeignKey(DataSource,on_delete=models.PROTECT); symbol=models.CharField(max_length=20); start_date=models.DateField(); end_date=models.DateField(); status=models.CharField(max_length=20,choices=STATUS,default='pending'); records_imported=models.PositiveIntegerField(default=0); error_message=models.TextField(blank=True)
