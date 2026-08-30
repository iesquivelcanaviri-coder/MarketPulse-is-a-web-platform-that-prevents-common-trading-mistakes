"""============================================================ ANALYSIS ADMIN ============================================================"""
from django.contrib import admin
from .models import OverfittingTest,MarketRegime,StressTest
for m in [OverfittingTest,MarketRegime,StressTest]:admin.site.register(m)
