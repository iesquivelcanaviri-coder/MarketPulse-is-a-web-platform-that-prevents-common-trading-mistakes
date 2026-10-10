"""============================================================
ANALYSIS TOOLS - DJANGO ADMIN
============================================================

FILE PURPOSE:

This file connects the analysis_tools database models
to Django's built-in administration website.

It allows an administrator to manage:

- OverfittingTest records
- MarketRegime records
- StressTest records

FRAMEWORK:

Django
    ↓
analysis_tools application
    ↓
analysis_tools/models.py
    ↓
analysis_tools/admin.py
    ↓
Django Admin
    ↓
Database records

MARKETPULSE FLOW:

Analysis calculations
    ↓
OverfittingTest / MarketRegime / StressTest
    ↓
PostgreSQL / Neon database
    ↓
analysis_tools/admin.py
    ↓
Django Admin interface
    ↓
Administrator can view and manage records

LECTURE CONNECTION:

Programming Language Features / Concepts used here:

1. Modules
2. Imports
3. Classes
4. Lists
5. Variables
6. For loops / iteration
7. Attribute access
8. Function / method calls

============================================================"""


# ============================================================
# 1. DJANGO ADMIN IMPORT
# ============================================================

from django.contrib import admin  # IMPORT: brings Django's built-in admin module into this Python file.


# ============================================================
# 2. ANALYSIS MODEL IMPORTS
# ============================================================

from .models import OverfittingTest,MarketRegime,StressTest  # RELATIVE IMPORT: imports three model classes from analysis_tools/models.py.


# ============================================================
# 3. REGISTER ANALYSIS MODELS WITH DJANGO ADMIN
# ============================================================

for m in [OverfittingTest,MarketRegime,StressTest]:admin.site.register(m)  # FOR LOOP: repeats the registration once for every model in this list.
# m is a VARIABLE that temporarily refers to the current model while the loop runs.
# [OverfittingTest,MarketRegime,StressTest] is a LIST containing three Python model classes.
# OverfittingTest is a CLASS representing stored overfitting-analysis results.
# MarketRegime is a CLASS representing stored market-condition or market-regime results.
# StressTest is a CLASS representing stored stress-testing results.
# "for" is a Python CONTROL-FLOW statement used to iterate through an iterable such as a list.
# "in" tells Python to take each item from the list one at a time.
# admin.site uses ATTRIBUTE ACCESS: "site" is accessed from Django's imported admin module.
# admin.site.register accesses Django Admin's register METHOD.
# register(m) is a METHOD CALL that sends the current model class to Django Admin.
# Django therefore performs the equivalent registration for all three analysis models.