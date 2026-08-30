"""
============================================================
STRATEGY BUILDER - MODELS
============================================================
Framework mapping: core.Strategy owns StrategyRule children through `strategy.rules`;
core.Backtest owns BacktestTrade execution records.
"""
from django.db import models
from core.models import Backtest,Strategy,TimeStampedModel
class StrategyRule(TimeStampedModel):
    CONDITIONS=[('ma_cross_up','Fast MA crosses above Slow MA'),('ma_cross_down','Fast MA crosses below Slow MA')]
    ACTIONS=[('buy','Buy'),('sell','Sell')]
    strategy=models.ForeignKey(Strategy,on_delete=models.CASCADE,related_name='rules'); name=models.CharField(max_length=160); symbol=models.CharField(max_length=20); condition_type=models.CharField(max_length=30,choices=CONDITIONS); action=models.CharField(max_length=10,choices=ACTIONS); parameters=models.JSONField(default=dict); is_active=models.BooleanField(default=True)
    def __str__(self): return self.name
class BacktestTrade(TimeStampedModel):
    backtest=models.ForeignKey(Backtest,on_delete=models.CASCADE,related_name='trades'); symbol=models.CharField(max_length=20); entry_date=models.DateField(); exit_date=models.DateField(null=True,blank=True); entry_price=models.DecimalField(max_digits=14,decimal_places=4); exit_price=models.DecimalField(max_digits=14,decimal_places=4,null=True,blank=True); requested_quantity=models.PositiveIntegerField(default=0); quantity=models.PositiveIntegerField(); partial_fill=models.BooleanField(default=False); transaction_cost=models.DecimalField(max_digits=14,decimal_places=2,default=0); profit_loss=models.DecimalField(max_digits=14,decimal_places=2,null=True,blank=True); status=models.CharField(max_length=20,choices=[('open','Open'),('closed','Closed')],default='open')
