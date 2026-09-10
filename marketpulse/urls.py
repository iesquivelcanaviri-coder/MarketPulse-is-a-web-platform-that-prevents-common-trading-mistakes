"""
============================================================
MARKETPULSE - ROOT URL ROUTER
============================================================

Framework mapping:

Browser Request
        ↓
marketpulse/urls.py
        ↓
Individual Django Apps


VISIBLE APPLICATION AREAS:

Home
Dashboard
Accounts
Data
Strategies
Risk
API


DASHBOARD ALERT ARCHITECTURE:

There are now two related but different concepts:

1. AlertRule
       ↓
   A configurable condition created by the user.

   Example:

       SPY
       Price
       Greater Than
       800

2. Alert
       ↓
   A notification/event generated when attention is required.


Framework mapping:

Dashboard
    ↓
Alert Rule
    ↓
Market monitoring
    ↓
Condition triggered
    ↓
Alert
    ↓
User acknowledgement / resolution


The old public /analysis/ route has been removed.

The analysis_tools app remains installed internally because
its models and analytical functions are still used by:

Data
    → Market Condition / Regime Analysis

Strategies
    → Strategy Robustness / Overfitting Analysis

Risk
    → Stress Testing

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

from django.contrib import admin

from django.urls import (
    include,
    path,
)


# ============================================================
# 2. CORE VIEW IMPORT
# ============================================================

from core import views as core_views


# ============================================================
# 3. ROOT URL PATTERNS
# ============================================================

urlpatterns = [


    # ========================================================
    # 3.1 DJANGO ADMINISTRATION
    # ========================================================

    path(
        "admin/",
        admin.site.urls,
    ),


    # ========================================================
    # 3.2 PUBLIC HOME PAGE
    # ========================================================

    path(
        "",
        core_views.home,
        name="home",
    ),


    # ========================================================
    # 3.3 MAIN DASHBOARD
    # ========================================================

    path(
        "dashboard/",
        core_views.dashboard,
        name="dashboard",
    ),


    # ========================================================
    # 3.4 DASHBOARD - EDIT GENERATED ALERT
    # ========================================================

    # Browser action:
    #
    # /dashboard/alerts/5/edit/
    #
    # where:
    #
    # 5 = Alert database ID
    #
    #
    # Framework mapping:
    #
    # Dashboard
    #     ↓
    # Edit Alert button
    #     ↓
    # POST request
    #     ↓
    # core.views.edit_alert
    #     ↓
    # AlertEditForm
    #     ↓
    # core.models.Alert
    #     ↓
    # PostgreSQL
    #
    #
    # SECURITY:
    #
    # The corresponding view filters using:
    #
    #     user=request.user
    #
    # so a user cannot edit another user's Alert simply by
    # changing the numeric ID inside the URL.

    path(
        "dashboard/alerts/<int:alert_id>/edit/",
        core_views.edit_alert,
        name="alert_edit",
    ),


    # ========================================================
    # 3.5 DASHBOARD - MARK GENERATED ALERT AS READ
    # ========================================================

    # Browser action:
    #
    # /dashboard/alerts/5/read/
    #
    #
    # Purpose:
    #
    # Marks the Alert as acknowledged without resolving the
    # underlying condition.
    #
    #
    # Example:
    #
    # High volatility Alert
    #     ↓
    # User reads Alert
    #     ↓
    # is_read = True
    #
    # but:
    #
    # is_active may remain True.

    path(
        "dashboard/alerts/<int:alert_id>/read/",
        core_views.mark_alert_read,
        name="alert_mark_read",
    ),


    # ========================================================
    # 3.6 DASHBOARD - RESOLVE / REOPEN GENERATED ALERT
    # ========================================================

    # Browser action:
    #
    # /dashboard/alerts/5/resolution/
    #
    #
    # Framework mapping:
    #
    # Dashboard
    #     ↓
    # Resolve / Reopen
    #     ↓
    # core.views.toggle_alert_resolution
    #     ↓
    # core.models.Alert
    #
    #
    # Active Alert:
    #
    # is_active = True
    #     ↓
    # Resolve
    #     ↓
    # is_active = False
    # resolved_at = timestamp
    #
    #
    # Resolved Alert:
    #
    # is_active = False
    #     ↓
    # Reopen
    #     ↓
    # is_active = True
    # is_read = False
    # resolved_at = None

    path(
        "dashboard/alerts/<int:alert_id>/resolution/",
        core_views.toggle_alert_resolution,
        name="alert_toggle_resolution",
    ),


    # ========================================================
    # 3.7 DASHBOARD - CREATE ALERT RULE
    # ========================================================

    # Browser action:
    #
    # /dashboard/alert-rules/create/
    #
    #
    # Framework mapping:
    #
    # Dashboard
    #     ↓
    # Add Alert Rule
    #     ↓
    # POST
    #     ↓
    # core.views.create_alert_rule
    #     ↓
    # AlertRuleForm
    #     ↓
    # core.models.AlertRule
    #     ↓
    # PostgreSQL
    #
    #
    # Example rule:
    #
    # Symbol:
    #     SPY
    #
    # Metric:
    #     Price
    #
    # Operator:
    #     Greater Than
    #
    # Threshold:
    #     800

    path(
        "dashboard/alert-rules/create/",
        core_views.create_alert_rule,
        name="alert_rule_create",
    ),


    # ========================================================
    # 3.8 DASHBOARD - EDIT ALERT RULE
    # ========================================================

    # Browser action:
    #
    # /dashboard/alert-rules/4/edit/
    #
    # where:
    #
    # 4 = AlertRule database ID
    #
    #
    # Framework mapping:
    #
    # Dashboard Alert Rule table
    #     ↓
    # Edit
    #     ↓
    # POST
    #     ↓
    # core.views.edit_alert_rule
    #     ↓
    # AlertRuleForm
    #     ↓
    # AlertRule
    #     ↓
    # PostgreSQL
    #
    #
    # SECURITY:
    #
    # The view should retrieve the rule using:
    #
    #     user=request.user
    #
    # so users may modify only their own rule records.

    path(
        "dashboard/alert-rules/<int:rule_id>/edit/",
        core_views.edit_alert_rule,
        name="alert_rule_edit",
    ),


    # ========================================================
    # 3.9 DASHBOARD - ENABLE / DISABLE ALERT RULE
    # ========================================================

    # Browser action:
    #
    # /dashboard/alert-rules/4/toggle/
    #
    #
    # Purpose:
    #
    # Allows the user to temporarily stop monitoring a rule
    # without deleting its configuration.
    #
    #
    # Example:
    #
    # Enabled:
    #
    #     is_enabled = True
    #
    # Toggle:
    #
    #     ↓
    #
    # Disabled:
    #
    #     is_enabled = False
    #
    #
    # The rule remains stored in PostgreSQL.

    path(
        "dashboard/alert-rules/<int:rule_id>/toggle/",
        core_views.toggle_alert_rule,
        name="alert_rule_toggle",
    ),


    # ========================================================
    # 3.10 DASHBOARD - DELETE ALERT RULE
    # ========================================================

    # Browser action:
    #
    # /dashboard/alert-rules/4/delete/
    #
    #
    # Purpose:
    #
    # Permanently remove one configurable AlertRule.
    #
    #
    # IMPORTANT:
    #
    # Deleting an AlertRule should not automatically delete
    # historical Alert records that may already have been
    # generated from that rule.
    #
    # This preserves the historical record of previous
    # notifications.

    path(
        "dashboard/alert-rules/<int:rule_id>/delete/",
        core_views.delete_alert_rule,
        name="alert_rule_delete",
    ),


    # ========================================================
    # 3.11 ACCOUNTS
    # ========================================================

    # Includes:
    #
    # - Registration
    # - Login
    # - Logout
    # - Profile
    # - Password-related account workflows

    path(
        "accounts/",
        include(
            "accounts.urls"
        ),
    ),


    # ========================================================
    # 3.12 DATA MANAGEMENT
    # ========================================================

    # Includes:
    #
    # - Historical market data
    # - Alpaca imports
    # - Historical OHLCV storage
    # - Market Condition / regime analysis

    path(
        "data/",
        include(
            "data_management.urls"
        ),
    ),


    # ========================================================
    # 3.13 STRATEGY BUILDER
    # ========================================================

    # Includes:
    #
    # - Strategy and model library
    # - User-created strategies
    # - Strategy rules
    # - Backtesting
    # - Strategy comparison
    # - Robustness / overfitting analysis

    path(
        "strategy/",
        include(
            "strategy_builder.urls"
        ),
    ),


    # ========================================================
    # 3.14 RISK MANAGEMENT
    # ========================================================

    # Includes:
    #
    # - Trade Risk Planner
    # - Position sizing
    # - Stop-loss analysis
    # - Stress testing
    # - Portfolio risk analysis

    path(
        "risk/",
        include(
            "risk_management.urls"
        ),
    ),


    # ========================================================
    # 3.15 REST API
    # ========================================================

    # Includes:
    #
    # - Dashboard live market API
    # - Alpaca asset search
    # - Alpaca asset details
    # - Alpaca snapshots
    # - Alpaca historical chart data
    # - Strategy API
    # - Backtest API
    # - Risk APIs
    # - MATLAB bridge endpoints

    path(
        "api/",
        include(
            "api.urls"
        ),
    ),

]