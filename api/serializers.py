"""
============================================================
API SERIALIZERS
============================================================
Framework mapping: Django models → JSON structures returned to React.
"""

# ============================================================
# 1. DJANGO REST FRAMEWORK IMPORT
# ============================================================

from rest_framework import serializers  # IMPORT / MODULE: Imports Django REST Framework's serializer tools so this file can convert Django model objects into API-friendly data.

# ============================================================
# 2. MARKETPULSE MODEL IMPORTS
# ============================================================

from core.models import MarketData,Strategy,Backtest  # IMPORT: Imports the three Django model classes whose database data will be represented through the API.

# ============================================================
# 3. MARKET DATA SERIALIZER
# ============================================================
# FRAMEWORK FLOW:
#
# PostgreSQL
#     ↓
# core.models.MarketData
#     ↓
# MarketDataSerializer
#     ↓
# Django REST Framework
#     ↓
# JSON / API response
#     ↓
# React frontend
#
# PROGRAMMING CONCEPTS:
# - Class
# - Inheritance
# - Nested class
# - Assignment
# - Tuple
# - Abstraction
# - Object-to-data mapping

class MarketDataSerializer(serializers.ModelSerializer):  # CLASS + INHERITANCE: Creates MarketDataSerializer and inherits ModelSerializer behaviour from Django REST Framework.
    class Meta: model=MarketData; fields=('symbol','date','open_price','high_price','low_price','close_price','volume')  # NESTED CLASS + ASSIGNMENT + TUPLE: Connects this serializer to MarketData and selects the model fields that the API is allowed to expose.

# ============================================================
# 4. STRATEGY SERIALIZER
# ============================================================
# FRAMEWORK FLOW:
#
# PostgreSQL
#     ↓
# core.models.Strategy
#     ↓
# StrategySerializer
#     ↓
# Django REST Framework
#     ↓
# Strategy API data
#     ↓
# React frontend
#
# PROGRAMMING CONCEPTS:
# - Class
# - Inheritance
# - Configuration
# - Tuples
# - Read-only data
# - Encapsulation
# - Abstraction

class StrategySerializer(serializers.ModelSerializer):  # CLASS + INHERITANCE: Creates a serializer specifically for Strategy objects using behaviour inherited from ModelSerializer.
    class Meta: model=Strategy; fields=('id','name','description','is_active','rule_config','created_at'); read_only_fields=('id','created_at')  # CONFIGURATION + TUPLES: Selects which Strategy fields appear in the API and prevents API users from directly changing id and created_at.

# ============================================================
# 5. BACKTEST SERIALIZER
# ============================================================
# FRAMEWORK FLOW:
#
# PostgreSQL
#     ↓
# core.models.Backtest
#     ↓
# BacktestSerializer
#     ↓
# strategy relationship
#     ↓
# strategy.name
#     ↓
# strategy_name
#     ↓
# Django REST Framework
#     ↓
# Backtest API data
#     ↓
# React frontend
#
# PROGRAMMING CONCEPTS:
# - Class
# - Inheritance
# - Object relationships
# - Attribute access
# - Method/function call
# - Keyword arguments
# - Assignment
# - Nested class
# - Tuples
# - Abstraction

class BacktestSerializer(serializers.ModelSerializer):  # CLASS + INHERITANCE: Creates the serializer responsible for converting Backtest model objects into API data.
    strategy_name=serializers.CharField(source='strategy.name',read_only=True)  # ASSIGNMENT + METHOD CALL + KEYWORD ARGUMENTS: Creates an extra text field called strategy_name by reading the related Strategy object's name; read_only means API input cannot change it directly.
    class Meta: model=Backtest; fields=('id','strategy','strategy_name','symbol','start_date','end_date','initial_capital','final_capital','total_return','max_drawdown','sharpe_ratio','win_rate','total_trades','transaction_costs','results')  # NESTED CLASS + CONFIGURATION + TUPLE: Connects the serializer to Backtest and explicitly defines every Backtest value that can appear in the API representation.