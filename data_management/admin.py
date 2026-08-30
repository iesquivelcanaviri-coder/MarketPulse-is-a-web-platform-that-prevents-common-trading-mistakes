"""============================================================ DATA MANAGEMENT ADMIN ============================================================"""
from django.contrib import admin
from .models import DataImport,DataSource
admin.site.register(DataSource); admin.site.register(DataImport)
