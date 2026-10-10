"""============================================================
ANALYSIS RESULT MODELS
Framework mapping: analyzers.py writes these records; views/templates display them.
============================================================"""

# ============================================================
# 1. IMPORTS
# ============================================================
# PROGRAMMING CONCEPT: Modules and imports
# Imports let this file reuse code that exists somewhere else.

from django.conf import settings  # Imports Django project settings so the model can use the configured user model.
from django.db import models  # Imports Django's model tools used to define database fields and relationships.
from core.models import Strategy,TimeStampedModel  # Imports the shared Strategy model and timestamp parent model from the core app.

# ============================================================
# 2. FRAMEWORK / DATA FLOW
# ============================================================
# DJANGO FRAMEWORK FLOW:
#
# analysis_tools/analyzers.py
#     ↓
# Performs quantitative analysis
#     ↓
# analysis_tools/models.py
#     ↓
# Defines how analysis results are stored
#     ↓
# Django ORM
#     ↓
# PostgreSQL / configured database
#     ↓
# analysis_tools/views.py
#     ↓
# Django templates
#     ↓
# User interface
#
# PROGRAMMING LANGUAGE CONCEPTS USED IN THIS FILE:
#
# Import              → reuse code from Django and core
# Class               → blueprint for an analysis-result object
# Inheritance         → models inherit from TimeStampedModel
# Class attributes    → Django fields such as symbol and confidence
# Data types          → CharField, DecimalField, BooleanField, etc.
# Lists               → REGIMES and TYPES collections
# Tuples              → each choice contains stored/display values
# Function calls      → models.CharField(...), models.ForeignKey(...)
# Arguments           → max_length=20, default=False, etc.
# Relationships       → ForeignKey connects database models
# Constants           → REGIMES and TYPES define fixed allowed choices
# Nested class        → Meta configures the MarketRegime model
# Constraints         → UniqueConstraint protects database consistency

# ============================================================
# 3. OVERFITTING TEST MODEL
# ============================================================
# PURPOSE:
# Stores the result of checking whether a strategy performs well
# on training data but poorly on unseen data.
#
# FRAMEWORK FLOW:
#
# Strategy + Market Data
#     ↓
# analysis_tools/analyzers.py
#     ↓
# Overfitting calculation
#     ↓
# OverfittingTest
#     ↓
# Database
#     ↓
# View / Template
#
# LECTURE CONCEPT:
# This class demonstrates Object-Oriented Programming.
# The class is a blueprint and each database row becomes an object.

class OverfittingTest(TimeStampedModel):  # Defines the OverfittingTest class and inherits shared timestamp behaviour from TimeStampedModel.
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='overfitting_tests')  # ForeignKey creates a many-to-one relationship between overfitting tests and a user.
    strategy=models.ForeignKey(Strategy,on_delete=models.CASCADE,related_name='overfitting_tests')  # Connects each overfitting test to the Strategy that was analysed.
    symbol=models.CharField(max_length=20)  # CharField stores the market symbol such as SPY as text with a maximum of 20 characters.
    test_period=models.CharField(max_length=60)  # Stores a text description of the period used for the overfitting test.
    in_sample_return=models.DecimalField(max_digits=10,decimal_places=6)  # Stores the strategy return calculated from the in-sample or training data.
    out_sample_return=models.DecimalField(max_digits=10,decimal_places=6)  # Stores the strategy return calculated from unseen out-of-sample data.
    overfitting_score=models.DecimalField(max_digits=10,decimal_places=6)  # Stores the numerical score used to measure possible overfitting.
    is_overfitted=models.BooleanField(default=False)  # BooleanField stores True or False and begins as False by default.
    recommendations=models.TextField(blank=True)  # TextField stores optional recommendations and blank=True allows the value to be left empty.

# ============================================================
# 4. MARKET REGIME MODEL
# ============================================================
# PURPOSE:
# Stores the detected market condition for a symbol on a date.
#
# Examples:
# bull
# bear
# sideways
# volatile
#
# FRAMEWORK FLOW:
#
# core.MarketData
#     ↓
# analysis_tools/analyzers.py
#     ↓
# Market-condition calculation
#     ↓
# MarketRegime
#     ↓
# Database
#     ↓
# Market Condition workspace / dashboard
#
# LECTURE CONCEPT:
# This class uses a collection of tuples as choices.
# It also uses a nested Meta class to configure database behaviour.

class MarketRegime(TimeStampedModel):  # Defines the MarketRegime model and inherits timestamp behaviour from TimeStampedModel.
    REGIMES=[('bull','Bull Market'),('bear','Bear Market'),('sideways','Sideways'),('volatile','High Volatility')]  # A list of tuples defines the allowed market-regime values and their user-friendly labels.
    symbol=models.CharField(max_length=20)  # Stores the ticker symbol being analysed as text.
    date=models.DateField()  # DateField stores the date to which this market-regime result belongs.
    regime=models.CharField(max_length=20,choices=REGIMES)  # Stores the regime and restricts its value to one of the choices defined in REGIMES.
    confidence=models.DecimalField(max_digits=8,decimal_places=6)  # Stores the numerical confidence level of the detected market regime.
    volatility=models.DecimalField(max_digits=10,decimal_places=6)  # Stores the calculated volatility value for the market.
    trend_strength=models.DecimalField(max_digits=10,decimal_places=6)  # Stores the calculated strength of the detected market trend.

    # ========================================================
    # 4.1 MARKET REGIME DATABASE RULES
    # ========================================================
    # PROGRAMMING CONCEPT: Nested class
    # Meta is a class inside MarketRegime.
    #
    # DJANGO CONCEPT:
    # Meta changes how Django manages this model without becoming
    # a normal database field itself.

    class Meta:  # Defines Django metadata and database rules for the MarketRegime model.
        constraints=[models.UniqueConstraint(fields=['symbol','date'],name='unique_regime_date')]  # Prevents the same symbol and date combination from being stored more than once.
        ordering=['-date']  # Tells Django to return MarketRegime records with the newest date first by default.

# ============================================================
# 5. STRESS TEST MODEL
# ============================================================
# PURPOSE:
# Stores the results of testing a strategy under difficult
# simulated market conditions.
#
# Supported scenarios:
# - Market Crash
# - Volatility Spike
# - Liquidity Crisis
# - Regime Change
#
# FRAMEWORK FLOW:
#
# Strategy
#     +
# Historical Market Data
#     ↓
# analysis_tools/analyzers.py
#     ↓
# Stress scenario
#     ↓
# StressTest
#     ↓
# Database
#     ↓
# View / Template
#     ↓
# User reviews strategy robustness
#
# LECTURE CONCEPT:
# This demonstrates classes, inheritance, collections, data types,
# object relationships, default values and structured JSON data.

class StressTest(TimeStampedModel):  # Defines the StressTest model and inherits timestamp behaviour from TimeStampedModel.
    TYPES=[('crash','Market Crash'),('volatility_spike','Volatility Spike'),('liquidity_crisis','Liquidity Crisis'),('regime_change','Regime Change')]  # A list of tuples defines the allowed stress-test scenario values and labels.
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='stress_tests')  # Connects each stress-test result to the user who owns it.
    strategy=models.ForeignKey(Strategy,on_delete=models.CASCADE,related_name='stress_tests')  # Connects the stress-test result to the Strategy that was tested.
    symbol=models.CharField(max_length=20)  # Stores the ticker symbol used during the stress test.
    test_type=models.CharField(max_length=40,choices=TYPES)  # Stores the selected stress-test type and restricts it to one of the TYPES choices.
    test_parameters=models.JSONField(default=dict)  # JSONField stores structured stress-test parameters and uses an empty dictionary as the default.
    max_drawdown=models.DecimalField(max_digits=10,decimal_places=6)  # Stores the largest calculated loss from a peak to a trough during the stress scenario.
    recovery_time=models.PositiveIntegerField(default=0)  # Stores a non-negative integer representing the calculated recovery time and starts at zero.
    robustness_score=models.DecimalField(max_digits=10,decimal_places=6)  # Stores the numerical result representing how robust the strategy was during the stress test.
    passed_test=models.BooleanField(default=False)  # Stores True when the strategy passes the stress test and False otherwise.
    notes=models.TextField(blank=True)  # Stores optional explanatory notes and allows the field to be left blank.