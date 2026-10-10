"""
============================================================
MARKETPULSE - ROOT URL ROUTER
============================================================
PURPOSE:
Connect requested URL paths to Django views and app routers.
FRAMEWORK:
Browser request → Root URL router → View or app URL router.
APPLICATION AREAS:
Home, Dashboard, Accounts, Data, Strategies, Risk, Community,
Inbox and API.
COMMUNITY:
community.urls supplies community and private-messaging routes.
Its app_name="community" supports names such as community:feed,
community:inbox, community:compose_message and
community:message_detail.
PASSWORD RECOVERY:
Request reset → Email-request confirmation → UID/token link
→ Set new password → Reset-complete page.
DASHBOARD ALERTS:
AlertRule describes a monitoring condition.
Alert represents a generated notification or event.
Views handle editing, acknowledgement, resolution and rules.
INTERNAL ANALYTICS:
This root router does not register an analysis/ prefix.
App routers determine their own remaining public routes.
LECTURE:
Imports, aliases, variables, lists, strings, function calls,
keyword arguments, attribute access and modular design.
============================================================
"""
# ============================================================
# 1. DJANGO IMPORTS
# ============================================================
from django.contrib import admin  # I import Django's administration site.
from django.contrib.auth import views as auth_views  # I import authentication views with an alias to distinguish them from project views.
from django.urls import (  # I begin a grouped import of URL-routing tools.
    include,  # I import the function that delegates routing to another URL configuration.
    path,  # I import the function that defines a URL pattern.
)  # I finish the grouped import.
# ============================================================
# 2. CORE VIEW IMPORT
# ============================================================
from core import views as core_views  # I import core views using an alias that identifies their application.
# ============================================================
# 3. ROOT URL PATTERNS
# ============================================================
urlpatterns = [  # I create the ordered list Django uses to resolve requests.
    # ========================================================
    # 3.1 DJANGO ADMINISTRATION
    # ========================================================
    path(  # I register a URL pattern.
        "admin/",  # I match URLs beginning with the admin prefix.
        admin.site.urls,  # I connect this prefix to Django's admin URL configuration.
    ),  # I finish the admin route.
    # ========================================================
    # 3.2 PUBLIC HOME PAGE
    # ========================================================
    path(  # I register the home-page route.
        "",  # I match the site's root path.
        core_views.home,  # I pass the home view reference; Django calls it when a request matches.
        name="home",  # I give this route a name for URL reversing.
    ),  # I finish the home route.
    # ========================================================
    # 3.3 MAIN DASHBOARD
    # ========================================================
    path(  # I register the dashboard route.
        "dashboard/",  # I match the dashboard path.
        core_views.dashboard,  # I select the dashboard view.
        name="dashboard",  # I give the route its reusable name.
    ),  # I finish the dashboard route.
    # ========================================================
    # 3.4 DASHBOARD - EDIT GENERATED ALERT
    # ========================================================
    # Example: /dashboard/alerts/5/edit/
    # The view handles forms, ownership checks and database edits.
    path(  # I register an alert-edit route.
        "dashboard/alerts/<int:alert_id>/edit/",  # I capture the alert ID and convert it to an integer.
        core_views.edit_alert,  # I send the request and alert_id to the editing view.
        name="alert_edit",  # I name the route for links and redirects.
    ),  # I finish the alert-edit route.
    # ========================================================
    # 3.5 DASHBOARD - MARK GENERATED ALERT AS READ
    # ========================================================
    # Acknowledging an alert is separate from resolving it.
    path(  # I register the acknowledgement route.
        "dashboard/alerts/<int:alert_id>/read/",  # I capture the ID of the alert being acknowledged.
        core_views.mark_alert_read,  # I delegate the read-status update to this view.
        name="alert_mark_read",  # I give the route its reusable name.
    ),  # I finish the acknowledgement route.
    # ========================================================
    # 3.6 DASHBOARD - RESOLVE / REOPEN GENERATED ALERT
    # ========================================================
    # The view controls active status and resolution timestamps.
    path(  # I register the resolution-toggle route.
        "dashboard/alerts/<int:alert_id>/resolution/",  # I capture the target alert's integer ID.
        core_views.toggle_alert_resolution,  # I delegate resolution or reopening to this view.
        name="alert_toggle_resolution",  # I name the route.
    ),  # I finish the resolution route.
    # ========================================================
    # 3.7 DASHBOARD - CREATE ALERT RULE
    # ========================================================
    # Example rule: SPY price greater than 800.
    path(  # I register the rule-creation route.
        "dashboard/alert-rules/create/",  # I match the create-rule path.
        core_views.create_alert_rule,  # I select the view responsible for creating a rule.
        name="alert_rule_create",  # I name the creation route.
    ),  # I finish the rule-creation route.
    # ========================================================
    # 3.8 DASHBOARD - EDIT ALERT RULE
    # ========================================================
    # The view is responsible for restricting edits to the owner.
    path(  # I register the rule-editing route.
        "dashboard/alert-rules/<int:rule_id>/edit/",  # I capture the rule ID as an integer.
        core_views.edit_alert_rule,  # I pass the request and rule_id to the editing view.
        name="alert_rule_edit",  # I name the editing route.
    ),  # I finish the rule-editing route.
    # ========================================================
    # 3.9 DASHBOARD - ENABLE / DISABLE ALERT RULE
    # ========================================================
    # Toggling monitoring does not itself mean deleting the rule.
    path(  # I register the enable-or-disable route.
        "dashboard/alert-rules/<int:rule_id>/toggle/",  # I capture the rule whose status should change.
        core_views.toggle_alert_rule,  # I delegate the status change to the view.
        name="alert_rule_toggle",  # I name the toggle route.
    ),  # I finish the rule-toggle route.
    # ========================================================
    # 3.10 DASHBOARD - DELETE ALERT RULE
    # ========================================================
    # Record deletion and historical-alert retention belong to
    # the view and model relationships, not this URL declaration.
    path(  # I register the rule-deletion route.
        "dashboard/alert-rules/<int:rule_id>/delete/",  # I capture the target rule's ID.
        core_views.delete_alert_rule,  # I select the view responsible for deletion.
        name="alert_rule_delete",  # I name the deletion route.
    ),  # I finish the rule-deletion route.
    # ========================================================
    # 3.11 PASSWORD RECOVERY - REQUEST RESET
    # ========================================================
    # Django handles the reset workflow; settings configure email.
    path(  # I register the password-reset request route.
        "accounts/password-reset/",  # I match the password-reset form path.
        auth_views.PasswordResetView.as_view(  # I convert Django's class-based view into a callable with these settings.
            template_name=(  # I configure the reset-request page template.
                "accounts/password_reset.html"  # I specify the HTML template path.
            ),  # I finish the template-name argument.
            email_template_name=(  # I configure the reset-email body template.
                "accounts/password_reset_email.html"  # I specify the email body template path.
            ),  # I finish the email-template argument.
            subject_template_name=(  # I configure the reset-email subject template.
                "accounts/password_reset_subject.txt"  # I specify the subject template path.
            ),  # I finish the subject-template argument.
        ),  # I finish configuring the password-reset view.
        name="password_reset",  # I give the route Django's standard reset-request name.
    ),  # I finish the reset-request route.
    # ========================================================
    # 3.12 PASSWORD RECOVERY - EMAIL REQUEST COMPLETE
    # ========================================================
    # The confirmation page should avoid revealing account existence.
    path(  # I register the reset-request confirmation route.
        "accounts/password-reset/done/",  # I match the confirmation-page path.
        auth_views.PasswordResetDoneView.as_view(  # I configure Django's request-complete view.
            template_name=(  # I supply its page template.
                "accounts/password_reset_done.html"  # I specify the confirmation template path.
            ),  # I finish the template argument.
        ),  # I finish configuring the view.
        name="password_reset_done",  # I give the route its standard password-reset name.
    ),  # I finish the confirmation route.
    # ========================================================
    # 3.13 PASSWORD RECOVERY - SECURE RESET LINK
    # ========================================================
    path(  # I register the route used by the reset link.
        (  # I group adjacent strings that Python joins into one route string.
            "accounts/password-reset-confirm/"  # I define the fixed route prefix.
            "<uidb64>/<token>/"  # I capture the encoded user identifier and token as strings.
        ),  # I finish the combined route string.
        auth_views.PasswordResetConfirmView.as_view(  # I configure Django's token-validation and password-setting view.
            template_name=(  # I supply the password-setting page template.
                "accounts/password_reset_confirm.html"  # I specify the confirmation-form template path.
            ),  # I finish the template argument.
        ),  # I finish configuring the reset-confirm view.
        name="password_reset_confirm",  # I give the route its standard reset-link name.
    ),  # I finish the reset-confirm route.
    # ========================================================
    # 3.14 PASSWORD RECOVERY - RESET COMPLETE
    # ========================================================
    path(  # I register the password-reset completion route.
        "accounts/password-reset-complete/",  # I match the completion-page path.
        auth_views.PasswordResetCompleteView.as_view(  # I configure Django's reset-complete view.
            template_name=(  # I supply its completion-page template.
                "accounts/password_reset_complete.html"  # I specify the template path.
            ),  # I finish the template argument.
        ),  # I finish configuring the completion view.
        name="password_reset_complete",  # I give the route its standard completion name.
    ),  # I finish the completion route.
    # ========================================================
    # 3.15 ACCOUNTS
    # ========================================================
    # Explicit password-reset routes remain above this app include.
    path(  # I register the accounts application's route prefix.
        "accounts/",  # I match the accounts prefix.
        include(  # I delegate the remaining path to another URL configuration.
            "accounts.urls"  # I identify the accounts URL module.
        ),  # I finish the include call.
    ),  # I finish the accounts registration.
    # ========================================================
    # 3.16 DATA MANAGEMENT
    # ========================================================
    path(  # I register the data application's route prefix.
        "data/",  # I match the data prefix.
        include(  # I delegate the remaining path.
            "data_management.urls"  # I identify the data-management URL module.
        ),  # I finish the include call.
    ),  # I finish the data registration.
    # ========================================================
    # 3.17 STRATEGY BUILDER
    # ========================================================
    path(  # I register the strategy application's route prefix.
        "strategy/",  # I match the strategy prefix.
        include(  # I delegate the remaining path.
            "strategy_builder.urls"  # I identify the strategy-builder URL module.
        ),  # I finish the include call.
    ),  # I finish the strategy registration.
    # ========================================================
    # 3.18 RISK MANAGEMENT
    # ========================================================
    # The included file determines which risk routes are exposed.
    path(  # I register the risk application's route prefix.
        "risk/",  # I match the risk prefix.
        include(  # I delegate the remaining path.
            "risk_management.urls"  # I identify the risk-management URL module.
        ),  # I finish the include call.
    ),  # I finish the risk registration.
    # ========================================================
    # 3.19 COMMUNITY & PRIVATE MESSAGING
    # ========================================================
    # community.urls supplies its routes and community namespace.
    # Templates can use {% url 'community:feed' %} when configured.
    path(  # I register the community application's route prefix.
        "community/",  # I match the community prefix.
        include(  # I delegate the remaining path.
            "community.urls"  # I identify the community and messaging URL module.
        ),  # I finish the include call.
    ),  # I finish the community registration.
    # ========================================================
    # 3.20 REST API
    # ========================================================
    path(  # I register the API route prefix.
        "api/",  # I match the API prefix.
        include(  # I delegate the remaining path.
            "api.urls"  # I identify the API URL module.
        ),  # I finish the include call.
    ),  # I finish the API registration.
]  # I finish the ordered root URL list.