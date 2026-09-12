"""============================================================
ACCOUNTS - URLS
============================================================

Framework mapping:

marketpulse/urls.py
        ↓
accounts/urls.py
        ↓
accounts/views.py
        ↓
accounts/templates/accounts/

This file controls the URL routes for:

- User registration
- User login
- User logout
- User profile viewing
- User profile editing
- User password changing
- Password-change confirmation

Django's built-in authentication views are used for:

- Login
- Logout
- Password changing
- Password-change confirmation

MarketPulse uses custom views for:

- Registration
- Profile management

============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

# Django provides ready-made authentication views for common
# account actions such as login, logout and password changes.
from django.contrib.auth import views as auth_views

# path() connects a URL to a Django view.
#
# reverse_lazy() allows Django to resolve a named URL only when
# it is actually needed. This is useful inside URL configuration
# because the complete URL structure may still be loading.
from django.urls import path, reverse_lazy

# Import MarketPulse's custom account views from accounts/views.py.
from . import views


# ============================================================
# 2. APPLICATION NAMESPACE
# ============================================================

# This namespace keeps all account URLs organised under
# "accounts".
#
# This means templates should use URL names such as:
#
# {% url 'accounts:register' %}
# {% url 'accounts:login' %}
# {% url 'accounts:logout' %}
# {% url 'accounts:profile' %}
# {% url 'accounts:password_change' %}
# {% url 'accounts:password_change_done' %}
#
# Using a namespace is useful because larger Django projects
# can contain several apps with similar URL names.

app_name = "accounts"


# ============================================================
# 3. ACCOUNT URL PATTERNS
# ============================================================

urlpatterns = [


    # ========================================================
    # USER REGISTRATION
    # ========================================================

    # --------------------------------------------------------
    # Register a new MarketPulse user
    # --------------------------------------------------------

    # URL:
    # /accounts/register/
    #
    # This route calls the custom register() function from
    # accounts/views.py.
    #
    # The registration view is responsible for creating the
    # user's account and the associated UserProfile information.

    path(
        "register/",
        views.register,
        name="register",
    ),


    # ========================================================
    # USER LOGIN
    # ========================================================

    # --------------------------------------------------------
    # Log into MarketPulse
    # --------------------------------------------------------

    # URL:
    # /accounts/login/
    #
    # LoginView is supplied by Django's authentication system.
    #
    # Instead of using Django's default:
    #
    # registration/login.html
    #
    # MarketPulse uses:
    #
    # accounts/templates/accounts/login.html

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html"
        ),
        name="login",
    ),


    # ========================================================
    # USER LOGOUT
    # ========================================================

    # --------------------------------------------------------
    # Log out of MarketPulse
    # --------------------------------------------------------

    # URL:
    # /accounts/logout/
    #
    # LogoutView securely removes the authenticated user's
    # session.
    #
    # The destination after logout is controlled by:
    #
    # LOGOUT_REDIRECT_URL
    #
    # inside marketpulse/settings.py.

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),


    # ========================================================
    # USER PROFILE
    # ========================================================

    # --------------------------------------------------------
    # View and update the logged-in user's profile
    # --------------------------------------------------------

    # URL:
    # /accounts/profile/
    #
    # This route calls the custom profile() function from
    # accounts/views.py.
    #
    # The profile page can:
    #
    # - Display username
    # - Display first name
    # - Display last name
    # - Display email address
    # - Display account creation date
    # - Display last login
    # - Display UserProfile information
    # - Display trading preferences
    # - Display risk preferences
    # - Allow personal information to be edited
    # - Allow profile information to be edited
    # - Save updated information to the database
    #
    # The profile() view should use @login_required so another
    # visitor cannot access a user's private profile.

    path(
        "profile/",
        views.profile,
        name="profile",
    ),


    # ========================================================
    # CHANGE PASSWORD
    # ========================================================

    # --------------------------------------------------------
    # Change the password while logged in
    # --------------------------------------------------------

    # URL:
    # /accounts/password-change/
    #
    # PasswordChangeView is Django's built-in secure password
    # change workflow.
    #
    # It requires the authenticated user to enter:
    #
    # - Their current password
    # - Their new password
    # - Their new password again
    #
    # Django then:
    #
    # 1. Checks the current password.
    # 2. Validates the new password.
    # 3. Hashes the new password securely.
    # 4. Updates the user account.
    # 5. Redirects to password_change_done.
    #
    # IMPORTANT:
    #
    # Because this file uses:
    #
    # app_name = "accounts"
    #
    # the template URL must be:
    #
    # {% url 'accounts:password_change' %}
    #
    # NOT:
    #
    # {% url 'password_change' %}

    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(

            # MarketPulse's custom Bootstrap password-change page.
            template_name="accounts/password_change.html",

            # After the password has been successfully changed,
            # redirect to the password-change success page.
            success_url=reverse_lazy(
                "accounts:password_change_done"
            ),
        ),
        name="password_change",
    ),


    # ========================================================
    # PASSWORD CHANGE SUCCESS
    # ========================================================

    # --------------------------------------------------------
    # Confirmation after password change
    # --------------------------------------------------------

    # URL:
    # /accounts/password-change/done/
    #
    # This page is displayed only after PasswordChangeView
    # successfully updates the password.
    #
    # It gives the user clear confirmation that their password
    # was changed successfully.

    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(

            # Custom MarketPulse success template.
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),

]