"""
============================================================
CORE - SHARED MODELS
============================================================
Framework mapping:
- data_management writes MarketData.
- strategy_builder owns child StrategyRule/BacktestTrade rows.
- risk_management and analysis_tools read MarketData.
- dashboard reads Strategy, Backtest and Alert.
"""
from django.conf import settings
from django.db import models
class TimeStampedModel(models.Model):
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: abstract=True
class MarketData(TimeStampedModel):
    symbol=models.CharField(max_length=20,db_index=True); date=models.DateField(db_index=True)
    open_price=models.DecimalField(max_digits=14,decimal_places=4); high_price=models.DecimalField(max_digits=14,decimal_places=4); low_price=models.DecimalField(max_digits=14,decimal_places=4); close_price=models.DecimalField(max_digits=14,decimal_places=4); volume=models.BigIntegerField(default=0)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['symbol','date'],name='unique_symbol_date')]; ordering=['-date']
    def __str__(self): return f'{self.symbol} {self.date}'
class Strategy(TimeStampedModel):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='strategies'); name=models.CharField(max_length=120); description=models.TextField(blank=True); is_active=models.BooleanField(default=True)
    rule_config=models.JSONField(default=dict)  # Deliberately not named `rules`; StrategyRule uses that reverse accessor.
    def __str__(self): return self.name
class Backtest(TimeStampedModel):
    strategy=models.ForeignKey(Strategy,on_delete=models.CASCADE,related_name='backtests'); symbol=models.CharField(max_length=20); start_date=models.DateField(); end_date=models.DateField()
    initial_capital=models.DecimalField(max_digits=14,decimal_places=2,default=10000); final_capital=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    total_return=models.DecimalField(max_digits=10,decimal_places=6,default=0); max_drawdown=models.DecimalField(max_digits=10,decimal_places=6,default=0); sharpe_ratio=models.DecimalField(max_digits=10,decimal_places=6,default=0); win_rate=models.DecimalField(max_digits=10,decimal_places=6,default=0)
    total_trades=models.PositiveIntegerField(default=0); transaction_costs=models.DecimalField(max_digits=14,decimal_places=2,default=0); results=models.JSONField(default=dict)
    def __str__(self): return f'{self.strategy.name}: {self.start_date} to {self.end_date}'
class Alert(TimeStampedModel):
    TYPES=[('price','Price'),('strategy','Strategy'),('risk','Risk'),('regime','Market Regime')]
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='alerts'); alert_type=models.CharField(max_length=20,choices=TYPES); title=models.CharField(max_length=200); message=models.TextField(); is_read=models.BooleanField(default=False); is_active=models.BooleanField(default=True)
    def __str__(self): return self.title
