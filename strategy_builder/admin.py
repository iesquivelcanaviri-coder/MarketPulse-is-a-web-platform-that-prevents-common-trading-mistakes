"""============================================================ STRATEGY ADMIN ============================================================"""
from django.contrib import admin
from .models import StrategyRule,BacktestTrade
admin.site.register(StrategyRule); admin.site.register(BacktestTrade)
