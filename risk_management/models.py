"""============================================================
RISK SNAPSHOT MODEL
Framework mapping: calculator results are persisted for audit/history.
============================================================"""
from django.conf import settings
from django.db import models
from core.models import TimeStampedModel
class RiskSnapshot(TimeStampedModel):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='risk_snapshots'); symbol=models.CharField(max_length=20,blank=True); account_balance=models.DecimalField(max_digits=14,decimal_places=2); risk_percentage=models.DecimalField(max_digits=8,decimal_places=6); volatility=models.DecimalField(max_digits=10,decimal_places=6,default=0); recommended_position_size=models.DecimalField(max_digits=14,decimal_places=4); stop_loss_price=models.DecimalField(max_digits=14,decimal_places=4)
