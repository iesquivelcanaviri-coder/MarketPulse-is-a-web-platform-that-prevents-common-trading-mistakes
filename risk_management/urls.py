"""============================================================ RISK URLS: `/risk/` → calculator/dashboard. ============================================================"""
from django.urls import path
from . import views
app_name='risk_management'; urlpatterns=[path('calculator/',views.calculator,name='calculator'),path('dashboard/',views.dashboard,name='dashboard')]
