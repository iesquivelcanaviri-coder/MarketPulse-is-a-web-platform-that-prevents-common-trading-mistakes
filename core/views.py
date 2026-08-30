"""============================================================
CORE - HOME/DASHBOARD VIEWS
Framework mapping: root URLs call these views; dashboard queries live PostgreSQL data.
============================================================"""
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import render
from .models import Alert,Backtest,MarketData,Strategy
def home(request): return render(request,'home.html')
@login_required
def dashboard(request):
    strategies=Strategy.objects.filter(user=request.user); backtests=Backtest.objects.filter(strategy__user=request.user).select_related('strategy').order_by('-created_at')
    avg=backtests.aggregate(v=Avg('win_rate'))['v'] or 0
    return render(request,'dashboard.html',{'active_strategy_count':strategies.filter(is_active=True).count(),'backtest_count':backtests.count(),'avg_win_rate':float(avg)*100,'market_data_count':MarketData.objects.count(),'latest_backtest':backtests.first(),'alerts':Alert.objects.filter(user=request.user,is_active=True)[:5]})
