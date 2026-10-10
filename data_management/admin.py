"""============================================================ DATA MANAGEMENT ADMIN ============================================================"""
# ============================================================
# 1. IMPORTS
# ============================================================
from django.contrib import admin  # I import Django's administration tools.
from .models import DataImport, DataSource  # I import both model classes from this application's models.py.
# ============================================================
# 2. REGISTER THE DATA PROVIDER MODEL
# ============================================================
admin.site.register(DataSource)  # I register providers with the default admin site and its standard model interface.
# ============================================================
# 3. REGISTER THE IMPORT JOB MODEL
# ============================================================
admin.site.register(DataImport)  # I register import jobs so authorized staff can manage their database records.