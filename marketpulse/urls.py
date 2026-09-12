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


AUTHENTICATION / PASSWORD RECOVERY:

User
    ↓
Login
    ↓
Forgot Password
    ↓
Django PasswordResetView
    ↓
Password Reset Email
    ↓
Secure UID + Token Link
    ↓
PasswordResetConfirmView
    ↓
New Password
    ↓
PasswordResetCompleteView
    ↓
Return to Login


DASHBOARD ALERT ARCHITECTURE:

There are two related but different concepts:

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
Market Monitoring
    ↓
Condition Triggered
    ↓
Alert
    ↓
User Acknowledgement / Resolution


INTERNAL ANALYTICS:

The old public /analysis/ route has been removed.

The analysis_tools app can remain installed internally
because analytical functionality may still be used by:

Data
    → Market Condition / Regime Analysis

Strategies
    → Strategy Robustness / Overfitting Analysis


Risk now focuses on:

Risk
    → Trade Risk Planning
    → Position Sizing
    → Stop-Loss Analysis
    → Reward / Risk


Stress Testing has been removed from the current
user-facing MarketPulse project.

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

from django.contrib import admin

# Django's built-in authentication views provide the complete
# password-reset workflow without MarketPulse having to create
# its own reset-token security system.
from django.contrib.auth import views as auth_views

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
    # The view retrieves the rule using:
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
    # 3.11 PASSWORD RECOVERY - REQUEST RESET
    # ========================================================

    # Browser URL:
    #
    # /accounts/password-reset/
    #
    #
    # User workflow:
    #
    # Login
    #     ↓
    # Forgot Password?
    #     ↓
    # Enter registered email
    #     ↓
    # PasswordResetView
    #
    #
    # Django handles:
    #
    # - Looking for an account with the submitted email
    # - Creating the secure reset token
    # - Creating the encoded user identifier
    # - Building the reset email
    # - Sending the email using EMAIL_BACKEND
    #
    #
    # MarketPulse customises:
    #
    # - Page template
    # - Email message template
    # - Email subject template
    #
    #
    # The actual email provider is configured separately in:
    #
    # marketpulse/settings.py

    path(
        "accounts/password-reset/",

        auth_views.PasswordResetView.as_view(

            template_name=(
                "accounts/password_reset.html"
            ),

            email_template_name=(
                "accounts/password_reset_email.html"
            ),

            subject_template_name=(
                "accounts/password_reset_subject.txt"
            ),

        ),

        name="password_reset",
    ),


    # ========================================================
    # 3.12 PASSWORD RECOVERY - EMAIL REQUEST COMPLETE
    # ========================================================

    # Browser URL:
    #
    # /accounts/password-reset/done/
    #
    #
    # Framework mapping:
    #
    # Password Reset Form
    #     ↓
    # Successful submission
    #     ↓
    # PasswordResetDoneView
    #     ↓
    # "Check your email" page
    #
    #
    # SECURITY:
    #
    # The page should use neutral wording such as:
    #
    # "If an account exists for this email..."
    #
    # This avoids revealing whether a particular email
    # address is registered with MarketPulse.

    path(
        "accounts/password-reset/done/",

        auth_views.PasswordResetDoneView.as_view(

            template_name=(
                "accounts/password_reset_done.html"
            ),

        ),

        name="password_reset_done",
    ),


    # ========================================================
    # 3.13 PASSWORD RECOVERY - SECURE RESET LINK
    # ========================================================

    # Example email URL:
    #
    # /accounts/password-reset-confirm/
    # <uidb64>/<token>/
    #
    #
    # uidb64:
    #
    #     Encoded identifier for the account.
    #
    #
    # token:
    #
    #     Secure Django-generated password-reset token.
    #
    #
    # Framework mapping:
    #
    # User opens email
    #     ↓
    # Clicks secure reset URL
    #     ↓
    # Django validates UID + token
    #     ↓
    # PasswordResetConfirmView
    #     ↓
    # User enters new password twice
    #     ↓
    # Django validates password
    #     ↓
    # Password changed
    #
    #
    # MarketPulse does NOT need to create or store its own
    # password-reset tokens.

    path(
        (
            "accounts/password-reset-confirm/"
            "<uidb64>/<token>/"
        ),

        auth_views.PasswordResetConfirmView.as_view(

            template_name=(
                "accounts/password_reset_confirm.html"
            ),

        ),

        name="password_reset_confirm",
    ),


    # ========================================================
    # 3.14 PASSWORD RECOVERY - RESET COMPLETE
    # ========================================================

    # Browser URL:
    #
    # /accounts/password-reset-complete/
    #
    #
    # Framework mapping:
    #
    # New password accepted
    #     ↓
    # PasswordResetCompleteView
    #     ↓
    # Password Updated page
    #     ↓
    # User returns to Login
    #
    #
    # No password or token is exposed by this page.

    path(
        "accounts/password-reset-complete/",

        auth_views.PasswordResetCompleteView.as_view(

            template_name=(
                "accounts/password_reset_complete.html"
            ),

        ),

        name="password_reset_complete",
    ),


    # ========================================================
    # 3.15 ACCOUNTS
    # ========================================================

    # Includes the existing MarketPulse account system:
    #
    # - Registration
    # - Login
    # - Logout
    # - Profile
    #
    #
    # Password recovery is intentionally defined above rather
    # than replacing the existing accounts application.
    #
    # This means MarketPulse keeps its existing custom User
    # model and registration/login workflow.

    path(
        "accounts/",
        include(
            "accounts.urls"
        ),
    ),


    # ========================================================
    # 3.16 DATA MANAGEMENT
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
    # 3.17 STRATEGY BUILDER
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
    # 3.18 RISK MANAGEMENT
    # ========================================================

    # Includes:
    #
    # - Trade Risk Planner
    # - Position sizing
    # - Stop-loss analysis
    # - Reward-to-risk calculations
    # - Historical risk context
    #
    #
    # Stress testing has been removed from the current
    # MarketPulse user-facing Risk workflow.

    path(
        "risk/",
        include(
            "risk_management.urls"
        ),
    ),


    # ========================================================
    # 3.19 REST API
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
    # - Optional MATLAB bridge endpoints

    path(
        "api/",
        include(
            "api.urls"
        ),
    ),

]