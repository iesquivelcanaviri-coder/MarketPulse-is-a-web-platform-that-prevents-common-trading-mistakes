"""============================================================
ANALYSIS RESULT MODELS
Framework mapping: analyzers.py writes these records; views/templates display them.
============================================================"""
from django.conf import settings
from django.db import models
from core.models import Strategy,TimeStampedModel
class OverfittingTest(TimeStampedModel):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='overfitting_tests'); strategy=models.ForeignKey(Strategy,on_delete=models.CASCADE,related_name='overfitting_tests'); symbol=models.CharField(max_length=20); test_period=models.CharField(max_length=60); in_sample_return=models.DecimalField(max_digits=10,decimal_places=6); out_sample_return=models.DecimalField(max_digits=10,decimal_places=6); overfitting_score=models.DecimalField(max_digits=10,decimal_places=6); is_overfitted=models.BooleanField(default=False); recommendations=models.TextField(blank=True)
class MarketRegime(TimeStampedModel):
    REGIMES=[('bull','Bull Market'),('bear','Bear Market'),('sideways','Sideways'),('volatile','High Volatility')]
    symbol=models.CharField(max_length=20); date=models.DateField(); regime=models.CharField(max_length=20,choices=REGIMES); confidence=models.DecimalField(max_digits=8,decimal_places=6); volatility=models.DecimalField(max_digits=10,decimal_places=6); trend_strength=models.DecimalField(max_digits=10,decimal_places=6)
    class Meta: constraints=[models.UniqueConstraint(fields=['symbol','date'],name='unique_regime_date')]; ordering=['-date']
class StressTest(TimeStampedModel):
    TYPES=[('crash','Market Crash'),('volatility_spike','Volatility Spike'),('liquidity_crisis','Liquidity Crisis'),('regime_change','Regime Change')]
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='stress_tests'); strategy=models.ForeignKey(Strategy,on_delete=models.CASCADE,related_name='stress_tests'); symbol=models.CharField(max_length=20); test_type=models.CharField(max_length=40,choices=TYPES); test_parameters=models.JSONField(default=dict); max_drawdown=models.DecimalField(max_digits=10,decimal_places=6); recovery_time=models.PositiveIntegerField(default=0); robustness_score=models.DecimalField(max_digits=10,decimal_places=6); passed_test=models.BooleanField(default=False); notes=models.TextField(blank=True)
