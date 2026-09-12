"""
============================================================
MARKETPULSE - ACCOUNTS VIEWS
============================================================

FRAMEWORK MAPPING:

Browser
    ↓
accounts/urls.py
    ↓
accounts/views.py
    ↓
accounts/forms.py
    ↓
accounts/models.py
    ↓
PostgreSQL
    ↓
accounts templates


REGISTRATION FLOW:

Registration Page
    ↓
UserRegistrationForm
    ↓
Validate Submitted Data
    ↓
Check Username Availability
    ↓
Username Available?
    ├── No
    │     ↓
    │   Display Form Error
    │
    └── Yes
          ↓
        Create User
          ↓
        Create UserProfile
          ↓
        PostgreSQL
          ↓
        Redirect to Login


PROFILE FLOW:

Authenticated User
    ↓
Profile Page
    ↓
UserProfileForm
    ↓
Update UserProfile
    ↓
PostgreSQL
    ↓
Return to Profile


PURPOSE:

This file handles the user-facing account workflows:

1. User registration
2. Duplicate-username protection
3. Automatic profile creation
4. User profile editing
5. Success/error messages

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

# messages allows MarketPulse to display feedback such as:
#
# - Account created successfully
# - Profile updated successfully
from django.contrib import messages


# get_user_model() returns the user model configured in:
#
# marketpulse/settings.py
#
# AUTH_USER_MODEL = "accounts.User"
#
# This is safer than importing Django's default User model.
from django.contrib.auth import get_user_model


# login_required prevents unauthenticated visitors
# from opening the profile page.
from django.contrib.auth.decorators import login_required


# IntegrityError is used as a final database-level safeguard.
#
# For example:
#
# if two registration requests attempted to create the same
# username at almost exactly the same time, PostgreSQL would
# still protect the unique username constraint.
from django.db import IntegrityError, transaction


# render:
# Combines a Django template with context.
#
# redirect:
# Sends the browser to another named route.
from django.shortcuts import (
    redirect,
    render,
)


# ============================================================
# 2. MARKETPULSE ACCOUNT FORMS
# ============================================================

from .forms import (
    UserProfileForm,
    UserRegistrationForm,
)


# ============================================================
# 3. MARKETPULSE ACCOUNT MODELS
# ============================================================

from .models import UserProfile


# ============================================================
# 4. CUSTOM USER MODEL
# ============================================================

# MarketPulse uses:
#
# accounts.User
#
# rather than Django's default auth.User model.
User = get_user_model()


# ============================================================
# 5. USER REGISTRATION
# ============================================================

def register(request):
    """
    ============================================================
    MARKETPULSE USER REGISTRATION
    ============================================================

    USER FLOW:

    User opens:
        /accounts/register/

            ↓

    User enters:
        - Username
        - First name
        - Last name
        - Email
        - Password

            ↓

    UserRegistrationForm validates the submitted information

            ↓

    MarketPulse checks whether the username already exists

            ↓

    If duplicate:
        Show a normal validation message

    If available:
        Create accounts.User
            ↓
        Create UserProfile
            ↓
        Redirect to login


    IMPORTANT:

    The database username field is unique.

    Therefore MarketPulse must prevent a duplicate username
    before attempting to create another User record.

    ============================================================
    """


    # ========================================================
    # 5.1 BUILD REGISTRATION FORM
    # ========================================================

    # GET request:
    #
    # request.POST is empty, so Django creates a blank form.
    #
    # POST request:
    #
    # request.POST contains the user's submitted registration
    # information.
    form = UserRegistrationForm(
        request.POST or None
    )


    # ========================================================
    # 5.2 PROCESS SUBMITTED REGISTRATION
    # ========================================================

    if (
        request.method == "POST"
        and form.is_valid()
    ):


        # ----------------------------------------------------
        # Read validated username
        # ----------------------------------------------------

        username = (
            form.cleaned_data
            .get(
                "username",
                "",
            )
            .strip()
        )


        # ====================================================
        # 5.3 CHECK WHETHER USERNAME ALREADY EXISTS
        # ====================================================

        # __iexact performs a case-insensitive comparison.
        #
        # Therefore:
        #
        # user2
        # User2
        # USER2
        #
        # are treated as the same username for registration
        # purposes.
        username_exists = (
            User.objects
            .filter(
                username__iexact=username
            )
            .exists()
        )


        if username_exists:


            # ------------------------------------------------
            # Attach the error directly to the username field.
            # ------------------------------------------------

            form.add_error(
                "username",
                (
                    "This username is already in use. "
                    "Please choose another username."
                ),
            )


        else:


            # =================================================
            # 5.4 CREATE USER SAFELY
            # =================================================

            try:


                # transaction.atomic() means the related
                # database operations are treated as one unit.
                #
                # If creation fails, Django rolls the operation
                # back instead of leaving a partial registration.
                with transaction.atomic():


                    # -----------------------------------------
                    # Create accounts.User
                    # -----------------------------------------

                    user = form.save()


                    # -----------------------------------------
                    # Create associated UserProfile
                    # -----------------------------------------

                    # get_or_create() prevents duplicate
                    # UserProfile records if one already exists.
                    UserProfile.objects.get_or_create(
                        user=user
                    )


                # =================================================
                # 5.5 SUCCESS MESSAGE
                # =================================================

                messages.success(
                    request,
                    (
                        "Account created successfully. "
                        "You can now log in."
                    ),
                )


                # =================================================
                # 5.6 REDIRECT TO LOGIN
                # =================================================

                return redirect(
                    "accounts:login"
                )


            # =====================================================
            # 5.7 DATABASE DUPLICATE SAFEGUARD
            # =====================================================

            except IntegrityError:


                # PostgreSQL is the final layer protecting
                # unique database constraints.
                #
                # Instead of allowing an HTTP 500 page,
                # MarketPulse converts the database error into
                # a user-friendly registration error.
                form.add_error(
                    "username",
                    (
                        "This username is already in use. "
                        "Please choose another username."
                    ),
                )


    # ========================================================
    # 5.8 RENDER REGISTRATION PAGE
    # ========================================================

    return render(
        request,
        "accounts/register.html",
        {
            "form":
                form,
        },
    )


# ============================================================
# 6. USER PROFILE
# ============================================================

@login_required
def profile(request):
    """
    ============================================================
    MARKETPULSE USER PROFILE
    ============================================================

    USER FLOW:

    Logged-in User
        ↓
    /accounts/profile/
        ↓
    Retrieve UserProfile
        ↓
    UserProfileForm
        ↓
    User updates profile
        ↓
    Save changes
        ↓
    PostgreSQL
        ↓
    Return to profile page


    SECURITY:

    @login_required ensures that only an authenticated
    MarketPulse user can access this view.

    The UserProfile record is obtained using request.user,
    so each user works with their own profile.

    ============================================================
    """


    # ========================================================
    # 6.1 LOAD OR CREATE USER PROFILE
    # ========================================================

    profile_object, created = (
        UserProfile.objects
        .get_or_create(
            user=request.user
        )
    )


    # ========================================================
    # 6.2 BUILD PROFILE FORM
    # ========================================================

    # instance=profile_object tells Django that this form
    # should update the existing UserProfile instead of
    # creating another one.
    form = UserProfileForm(
        request.POST or None,
        instance=profile_object,
    )


    # ========================================================
    # 6.3 PROCESS PROFILE UPDATE
    # ========================================================

    if (
        request.method == "POST"
        and form.is_valid()
    ):


        # ----------------------------------------------------
        # Save profile changes
        # ----------------------------------------------------

        form.save()


        # ----------------------------------------------------
        # User feedback
        # ----------------------------------------------------

        messages.success(
            request,
            "Profile updated successfully.",
        )


        # ----------------------------------------------------
        # Redirect prevents duplicate POST submission if the
        # browser is refreshed.
        # ----------------------------------------------------

        return redirect(
            "accounts:profile"
        )


    # ========================================================
    # 6.4 RENDER PROFILE PAGE
    # ========================================================

    return render(
        request,
        "accounts/profile.html",
        {
            "form":
                form,
        },
    )