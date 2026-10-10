"""============================================================
ANALYSIS TOOLS - DJANGO APP CONFIGURATION
============================================================

FILE PURPOSE:

This file tells Django how to register and configure
the analysis_tools application.

It does NOT perform the actual market analysis.

The actual analysis logic can live in files such as:
analysis_tools/analyzers.py

DJANGO FRAMEWORK FLOW:

marketpulse/settings.py
        ↓
INSTALLED_APPS
        ↓
analysis_tools/apps.py
        ↓
AnalysisToolsConfig
        ↓
Django Application Registry
        ↓
analysis_tools application becomes available to Django

MARKETPULSE FLOW:

MarketPulse
        ↓
analysis_tools application
        ↓
AnalysisToolsConfig
        ↓
Django recognises the application
        ↓
Models / Views / Analysis Logic can be used

LECTURE - PROGRAMMING LANGUAGE CONCEPTS:

Import
    ↓
Class
    ↓
Inheritance
    ↓
Class Attributes
    ↓
Assignment
    ↓
String Literals
    ↓
Object-Oriented Programming

============================================================"""

# ============================================================
# 1. DJANGO IMPORT
# ============================================================

from django.apps import AppConfig  # IMPORT: brings Django's AppConfig class into this Python file so we can use it.

# ============================================================
# 2. ANALYSIS TOOLS APPLICATION CONFIGURATION
# ============================================================

class AnalysisToolsConfig(AppConfig):  # CLASS + INHERITANCE: creates our configuration class and inherits Django behaviour from AppConfig.
    default_auto_field = 'django.db.models.BigAutoField'  # CLASS ATTRIBUTE + ASSIGNMENT + STRING: tells Django to use BigAutoField for automatic model primary keys.
    name = 'analysis_tools'  # CLASS ATTRIBUTE + ASSIGNMENT + STRING: tells Django that this configuration belongs to the analysis_tools application.