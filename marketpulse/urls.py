"""
============================================================
MARKETPULSE - RISK MANAGEMENT URLS
============================================================

PURPOSE:

This file contains the URL routes for the MarketPulse
Risk application.

The Risk workspace now focuses on one clear workflow:

Risk
    ↓
Trade & Portfolio Risk Planner
    ↓
Search Market
    ↓
Review Current Market Information
    ↓
Review Historical Risk Context
    ↓
Set Risk Budget
    ↓
Define Trade
    ↓
Calculate Position Size
    ↓
Review Risk Plan


IMPORTANT PROJECT UPDATE:

The Stress Test feature has been removed from the
MarketPulse project.

This means the Risk application no longer contains:

- Stress Test page
- Stress Test results page
- Stress Test URL routes

The purpose of this change is to keep the project
smaller, clearer and more reliable for the final
demonstration.


CURRENT RISK RESPONSIBILITIES:

The Risk tab is responsible for:

1. Searching for a market asset.
2. Loading current Alpaca market information.
3. Loading stored historical risk information.
4. Defining available trading capital.
5. Setting a maximum risk percentage.
6. Defining a hypothetical entry price.
7. Calculating a stop-loss.
8. Calculating risk per share or unit.
9. Calculating a risk-constrained position size.
10. Calculating potential reward-to-risk information.


FRAMEWORK MAPPING:

Browser
    ↓
/risk/calculator/
    ↓
risk_management.urls
    ↓
risk_management.views.calculator
    ↓
RiskPlannerForm
    ↓
risk_management/calculators.py
    ↓
Alpaca Market Data
        +
core.MarketData
    ↓
Risk calculation
    ↓
risk_management/calculator.html
    ↓
User


SECURITY:

Risk pages require authentication through the
@login_required decorator inside the corresponding
view.

Alpaca credentials remain on the Django backend and
must never be exposed through this URL configuration,
templates or browser JavaScript.

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

from django.urls import path


# ============================================================
# 2. RISK VIEW IMPORT
# ============================================================

from . import views


# ============================================================
# 3. APPLICATION NAMESPACE
# ============================================================

# The namespace allows MarketPulse to reference Risk URLs
# using names such as:
#
# risk_management:calculator
#
# instead of relying on hard-coded URL strings.
app_name = "risk_management"


# ============================================================
# 4. RISK URL PATTERNS
# ============================================================

urlpatterns = [


    # ========================================================
    # 4.1 TRADE & PORTFOLIO RISK PLANNER
    # ========================================================

    # Browser URL:
    #
    # /risk/calculator/
    #
    #
    # Framework mapping:
    #
    # User
    #     ↓
    # Risk navigation tab
    #     ↓
    # /risk/calculator/
    #     ↓
    # risk_management.views.calculator
    #     ↓
    # RiskPlannerForm
    #     ↓
    # Alpaca current market information
    #         +
    # MarketPulse historical MarketData
    #         +
    # risk_management/calculators.py
    #     ↓
    # Position sizing / stop-loss / risk calculations
    #     ↓
    # calculator.html
    #     ↓
    # Risk Plan displayed to user

    path(
        "calculator/",
        views.calculator,
        name="calculator",
    ),

]