"""============================================================
CORE ADMIN
Framework mapping: admin interface for shared market/strategy/backtest/alert records.
============================================================"""
from django.contrib import admin
from .models import Alert,Backtest,MarketData,Strategy
for m in [Alert,Backtest,MarketData,Strategy]: admin.site.register(m)
