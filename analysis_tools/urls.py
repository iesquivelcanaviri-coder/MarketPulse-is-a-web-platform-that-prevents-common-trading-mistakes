"""============================================================ ANALYSIS URLS: `/analysis/` → overfitting/regime/stress. ============================================================"""
from django.urls import path
from . import views
app_name='analysis_tools'; urlpatterns=[path('overfitting/',views.overfitting,name='overfitting'),path('overfitting/results/',views.overfitting_results,name='overfitting_results'),path('regime/',views.regime,name='regime'),path('stress/',views.stress,name='stress'),path('stress/results/',views.stress_results,name='stress_results')]
