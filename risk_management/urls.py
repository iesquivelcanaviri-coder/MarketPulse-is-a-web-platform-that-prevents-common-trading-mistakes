"""
============================================================
RISK MANAGEMENT - URL CONFIGURATION
============================================================

FRAMEWORK MAPPING:

MarketPulse
    ↓
/risk/
    ↓
risk_management/urls.py
    ↓
risk_management/views.py
    ↓
Risk templates


RISK WORKFLOW:

Risk
    ↓
Trade & Portfolio Risk Calculator
    ↓
Position sizing
    ↓
Stop-loss calculation
    ↓
Reward / Risk analysis
    ↓
Historical risk context
    ↓
Alpaca market information


STRESS TEST WORKFLOW:

Risk
    ↓
Stress Testing
    ↓
Select strategy
    ↓
Select asset
    ↓
Select severe market scenario
    ↓
analysis_tools/analyzers.py
    ↓
StressTest database result


IMPORTANT:

The old separate Analysis tab is no longer exposed
through the application's main navigation.

Stress Testing now belongs inside Risk because it answers:

"What could happen if market conditions become much worse?"

The old Risk Dashboard route has also been removed because
MarketPulse already has one main application Dashboard.

This keeps the Risk section focused on:

1. Trade risk planning
2. Position sizing
3. Stop-loss analysis
4. Reward-to-risk analysis
5. Stress testing

============================================================
"""


# ============================================================
# 1. DJANGO URL IMPORT
# ============================================================

# Django's path() function is used to connect a URL address
# to a specific view function inside the risk_management app.
from django.urls import path


# ============================================================
# 2. RISK MANAGEMENT VIEWS
# ============================================================

# This imports the views.py file from the current
# risk_management Django app.
#
# The dot means:
#
# "Import views from this same application folder."
from . import views


# ============================================================
# 3. APPLICATION NAMESPACE
# ============================================================

# Namespacing makes the Risk URLs easier to reference
# throughout MarketPulse without confusing them with URLs
# from other Django apps.
#
# Examples:
#
# risk_management:calculator
# risk_management:stress_test
# risk_management:stress_test_results
#
# The old:
#
# risk_management:dashboard
#
# has deliberately been removed because there is no longer
# a separate Risk Dashboard.
app_name = "risk_management"


# ============================================================
# 4. RISK MANAGEMENT URL PATTERNS
# ============================================================

urlpatterns = [


    # ========================================================
    # 4.1 TRADE & PORTFOLIO RISK CALCULATOR
    # ========================================================

    # Browser URL:
    #
    # /risk/calculator/
    #
    # Purpose:
    #
    # This is the main Risk workspace in MarketPulse.
    #
    # The page allows the user to:
    #
    # - Search or select an asset
    # - Read Alpaca market information
    # - Review historical MarketPulse risk information
    # - Enter simulated trading capital
    # - Define the maximum risk allowed for one trade
    # - Choose a long or short position
    # - Define or retrieve an entry price
    # - Select a stop-loss method
    # - Add an optional profit target
    # - Calculate risk-constrained position size
    # - Calculate planned maximum loss
    # - Calculate capital allocation
    # - Calculate reward-to-risk
    #
    # URL name:
    #
    # risk_management:calculator
    path(
        "calculator/",
        views.calculator,
        name="calculator",
    ),


    # ========================================================
    # 4.2 STRESS TEST
    # ========================================================

    # Browser URL:
    #
    # /risk/stress-test/
    #
    # Stress Testing previously belonged to the separate
    # Analysis area of MarketPulse.
    #
    # It has now been moved into Risk because its purpose is
    # directly related to understanding potential losses under
    # severe or unusual market conditions.
    #
    # The user should be able to select:
    #
    # - A strategy
    # - An asset
    # - A predefined severe market scenario
    #
    # Example scenarios can include:
    #
    # - Severe market decline
    # - Volatility spike
    # - Liquidity shock
    # - Market condition / regime change
    #
    # The calculations themselves can still use:
    #
    # analysis_tools/analyzers.py
    #
    # behind the scenes.
    #
    # This means analysis_tools becomes an internal analytics
    # engine rather than a separate visible navigation tab.
    #
    # URL name:
    #
    # risk_management:stress_test
    path(
        "stress-test/",
        views.stress_test,
        name="stress_test",
    ),


    # ========================================================
    # 4.3 STRESS TEST RESULTS
    # ========================================================

    # Browser URL:
    #
    # /risk/stress-test/results/
    #
    # Purpose:
    #
    # Displays previously generated stress-test results so the
    # user can review how a selected strategy behaved under
    # severe simulated market conditions.
    #
    # Results may include information such as:
    #
    # - Stress scenario used
    # - Original strategy performance
    # - Stressed performance
    # - Maximum drawdown
    # - Risk classification
    # - Whether the strategy passed or failed the stress test
    #
    # URL name:
    #
    # risk_management:stress_test_results
    path(
        "stress-test/results/",
        views.stress_test_results,
        name="stress_test_results",
    ),


]