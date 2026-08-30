"""============================================================ DATA MANAGEMENT URLS: root `/data/` → import/history views. ============================================================"""
from django.urls import path
from . import views
app_name='data_management'; urlpatterns=[path('import/',views.data_import,name='import'),path('history/',views.import_history,name='history')]
