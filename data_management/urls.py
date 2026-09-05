"""
============================================================
DATA MANAGEMENT - URL CONFIGURATION
============================================================

This file defines the user-facing routes for the
MarketPulse Data section.

Framework mapping:

marketpulse/urls.py
        ↓
data_management/urls.py
        ↓
data_management/views.py
        ↓
templates/data_management/


Main Data workflows:

/data/import/
    Historical market-data import and dataset workspace

/data/history/
    Previous historical-data imports

/data/market-condition/
    Market Condition analysis

/data/market-condition/results/
    Previous Market Condition / Market Regime results


ARCHITECTURE NOTE:

Market Regime Analysis previously appeared inside the
separate Analysis section.

It now belongs under Data because a market regime describes
the behaviour of the underlying market data rather than a
specific trading account or individual risk position.

The technical calculations can remain inside
analysis_tools.analyzers, while the user-facing workflow
belongs to data_management.
============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

from django.urls import path

from . import views


# ============================================================
# 2. APPLICATION NAMESPACE
# ============================================================

# The namespace allows templates and Python code to refer to
# these URLs safely using names such as:
#
# data_management:import
# data_management:history
# data_management:market_condition
# data_management:market_condition_results

app_name = "data_management"


# ============================================================
# 3. URL PATTERNS
# ============================================================

urlpatterns = [


    # ========================================================
    # 3.1 HISTORICAL MARKET DATA IMPORT
    # ========================================================

    # URL:
    #
    # /data/import/
    #
    # Purpose:
    #
    # Allows the user to import and review historical
    # market-data observations used throughout MarketPulse.
    #
    # These observations can later support:
    #
    # - historical OHLCV analysis
    # - strategy backtesting
    # - ATR calculations
    # - volatility calculations
    # - drawdown calculations
    # - market-condition analysis

    path(
        "import/",
        views.data_import,
        name="import",
    ),


    # ========================================================
    # 3.2 HISTORICAL IMPORT HISTORY
    # ========================================================

    # URL:
    #
    # /data/history/
    #
    # Purpose:
    #
    # Displays previous market-data import activity so the
    # user can see which datasets have already been added
    # to MarketPulse.

    path(
        "history/",
        views.import_history,
        name="history",
    ),


    # ========================================================
    # 3.3 MARKET CONDITION ANALYSIS
    # ========================================================

    # URL:
    #
    # /data/market-condition/
    #
    # User-facing purpose:
    #
    # Answers the question:
    #
    # "What type of market environment has this asset
    # recently experienced?"
    #
    # Possible classifications can include:
    #
    # - Uptrend
    # - Downtrend
    # - Sideways
    # - High volatility
    #
    # Technical method:
    #
    # Market Regime Analysis
    #
    # The analytical calculations can remain inside the
    # internal analysis_tools application, while this route
    # places the feature where the user naturally expects it:
    #
    # Data
    #   ↓
    # Market Condition

    path(
        "market-condition/",
        views.market_condition,
        name="market_condition",
    ),


    # ========================================================
    # 3.4 MARKET CONDITION RESULTS
    # ========================================================

    # URL:
    #
    # /data/market-condition/results/
    #
    # Purpose:
    #
    # Displays previously calculated MarketRegime results.
    #
    # The complete user-facing workflow becomes:
    #
    # Data
    #   ↓
    # Historical Market Data
    #   ↓
    # Market Condition
    #   ↓
    # Analysis Result

    path(
        "market-condition/results/",
        views.market_condition_results,
        name="market_condition_results",
    ),

]