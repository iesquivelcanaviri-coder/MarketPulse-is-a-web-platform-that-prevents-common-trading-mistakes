"""============================================================ API URLS: `/api/` routes used by React and third-party clients. ============================================================"""
from django.urls import include,path
from rest_framework.routers import DefaultRouter
from . import views
router=DefaultRouter(); router.register('strategies',views.StrategyViewSet,basename='strategy-api'); router.register('backtests',views.BacktestViewSet,basename='backtest-api')
urlpatterns=[path('health/',views.health),path('market/latest/',views.market_latest),path('risk/position-size/',views.risk_position_size),path('matlab/risk/',views.matlab_risk),path('',include(router.urls))]
