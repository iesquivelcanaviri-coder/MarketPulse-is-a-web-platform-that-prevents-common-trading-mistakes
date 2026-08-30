"""============================================================ STRATEGY URLS: `/strategy/` → list/create/backtest/results. ============================================================"""
from django.urls import path
from . import views
app_name='strategy_builder'; urlpatterns=[path('',views.strategy_list,name='list'),path('create/',views.strategy_create,name='create'),path('<int:strategy_id>/backtest/',views.backtest_strategy,name='backtest'),path('results/<int:backtest_id>/',views.backtest_results,name='results')]
