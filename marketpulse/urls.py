"""============================================================
ROOT URL ROUTER
Framework mapping: sends requests to each feature app and `/api/` to DRF.
============================================================"""
from django.contrib import admin
from django.urls import include,path
from core import views as core_views
urlpatterns=[path('admin/',admin.site.urls),path('',core_views.home,name='home'),path('dashboard/',core_views.dashboard,name='dashboard'),path('accounts/',include('accounts.urls')),path('data/',include('data_management.urls')),path('strategy/',include('strategy_builder.urls')),path('risk/',include('risk_management.urls')),path('analysis/',include('analysis_tools.urls')),path('api/',include('api.urls'))]
