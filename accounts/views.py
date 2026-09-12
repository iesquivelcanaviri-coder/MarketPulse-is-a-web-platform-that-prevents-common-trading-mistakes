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
Load accounts.User
    ↓
Load UserProfile
    ↓
UserAccountUpdateForm
    +
UserProfileForm
    ↓
Validate Both Forms
    ↓
Update User Account Information
    +
Update UserProfile Information
    ↓
PostgreSQL
    ↓
Return to Profile


PURPOSE:

This file handles the user-facing account workflows:

1. User registration
2. Duplicate-username protection
3. Automatic profile creation
4. User account information editing
5. User profile information editing
6. Profile information display
7. Success/error messages
8. Safe database transactions

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
# transaction allows related database updates to be treated
# as one operation.
#
# For example:
#
# if the User update succeeded but the UserProfile update
# failed, transaction.atomic() can roll back the complete
# operation instead of leaving inconsistent information.
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
    UserAccountUpdateForm,
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
    Retrieve accounts.User
        ↓
    Retrieve UserProfile
        ↓
    Display Current Account Information
        ↓
    User Clicks Edit Profile
        ↓
    UserAccountUpdateForm
        +
    UserProfileForm
        ↓
    Validate Both Forms
        ↓
    Update User Account
        +
    Update UserProfile
        ↓
    PostgreSQL
        ↓
    Redirect to Profile Page
        ↓
    Display Updated Information


    SECURITY:

    @login_required ensures that only an authenticated
    MarketPulse user can access this view.

    The UserProfile record is obtained using request.user,
    which means each authenticated user can only work with
    their own linked profile through this view.

    Password information is deliberately not handled here.

    Password changing and forgotten-password recovery should
    use Django's dedicated authentication/password workflow.

    ============================================================
    """


    # ========================================================
    # 6.1 LOAD OR CREATE USER PROFILE
    # ========================================================

    # request.user represents the currently authenticated
    # MarketPulse user.
    #
    # get_or_create() makes the profile page more robust because
    # if an older user account somehow does not yet have a
    # UserProfile record, MarketPulse creates one automatically.
    profile_object, created = (
        UserProfile.objects
        .get_or_create(
            user=request.user
        )
    )


    # ========================================================
    # 6.2 PROCESS PROFILE UPDATE
    # ========================================================

    if request.method == "POST":


        # ----------------------------------------------------
        # Build main user-account form
        # ----------------------------------------------------

        # instance=request.user is extremely important.
        #
        # It tells Django:
        #
        # "Update this existing logged-in user."
        #
        # Without instance=request.user, a ModelForm could try
        # to create a completely new database record instead.
        user_form = UserAccountUpdateForm(
            request.POST,
            instance=request.user,
        )


        # ----------------------------------------------------
        # Build additional profile-information form
        # ----------------------------------------------------

        # request.FILES is included so this view also works if
        # UserProfile contains a future upload field such as:
        #
        # profile_picture
        #
        # If there are currently no file fields, including
        # request.FILES does not cause a problem.
        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile_object,
        )


        # ====================================================
        # 6.3 VALIDATE BOTH FORMS
        # ====================================================

        # MarketPulse only updates the database when BOTH forms
        # are valid.
        #
        # This prevents a situation such as:
        #
        # User form valid
        # Profile form invalid
        #
        # but only half of the submitted changes being saved.
        if (
            user_form.is_valid()
            and profile_form.is_valid()
        ):


            # =================================================
            # 6.4 SAVE BOTH RECORDS SAFELY
            # =================================================

            try:


                # transaction.atomic() groups the two database
                # updates together.
                #
                # Therefore:
                #
                # accounts.User update
                #       +
                # UserProfile update
                #
                # are treated as one database operation.
                with transaction.atomic():


                    # -----------------------------------------
                    # Save main account information
                    # -----------------------------------------

                    user_form.save()


                    # -----------------------------------------
                    # Save additional profile information
                    # -----------------------------------------

                    profile_form.save()


                # =================================================
                # 6.5 SUCCESS MESSAGE
                # =================================================

                messages.success(
                    request,
                    (
                        "Your profile has been updated "
                        "successfully."
                    ),
                )


                # =================================================
                # 6.6 REDIRECT AFTER SUCCESSFUL POST
                # =================================================

                # Redirecting after a successful POST follows
                # the Post/Redirect/Get pattern.
                #
                # This prevents the browser from submitting the
                # same form again when the page is refreshed.
                return redirect(
                    "accounts:profile"
                )


            # =====================================================
            # 6.7 DATABASE ERROR SAFEGUARD
            # =====================================================

            except IntegrityError:


                # This protects the page from unexpected database
                # uniqueness conflicts or integrity problems.
                #
                # The user receives a normal error message rather
                # than an HTTP 500 page.
                messages.error(
                    request,
                    (
                        "Your profile could not be updated "
                        "because some information conflicts "
                        "with an existing account."
                    ),
                )


    # ========================================================
    # 6.8 DISPLAY EXISTING PROFILE
    # ========================================================

    else:


        # ----------------------------------------------------
        # Load current main account information
        # ----------------------------------------------------

        # Because instance=request.user is supplied, Django
        # automatically fills the form with the user's existing
        # information from PostgreSQL.
        user_form = UserAccountUpdateForm(
            instance=request.user
        )


        # ----------------------------------------------------
        # Load current additional profile information
        # ----------------------------------------------------

        profile_form = UserProfileForm(
            instance=profile_object
        )


    # ========================================================
    # 6.9 BUILD ACCOUNT INFORMATION FOR DISPLAY
    # ========================================================

    # These values come directly from accounts.User.
    #
    # They are displayed separately from UserProfile because
    # Django stores authentication/account information on the
    # User model.
    account_details = [
        (
            "Username",
            request.user.get_username(),
        ),
        (
            "First name",
            request.user.first_name,
        ),
        (
            "Last name",
            request.user.last_name,
        ),
        (
            "Email",
            request.user.email,
        ),
        (
            "Account created",
            request.user.date_joined,
        ),
        (
            "Last login",
            request.user.last_login,
        ),
    ]


    # ========================================================
    # 6.10 BUILD ADDITIONAL PROFILE INFORMATION
    # ========================================================

    # Instead of manually listing every UserProfile field,
    # Django's model metadata is used to read the fields.
    #
    # This means that if another normal UserProfile field is
    # added later, it can automatically appear in the profile
    # information section without rewriting this view.
    profile_details = []


    # --------------------------------------------------------
    # Loop through UserProfile database fields
    # --------------------------------------------------------

    for field in profile_object._meta.fields:


        # ----------------------------------------------------
        # Skip internal fields
        # ----------------------------------------------------

        # id:
        # Internal database primary key.
        #
        # user:
        # Internal relationship between UserProfile and User.
        #
        # Neither needs to be presented as normal profile
        # information to the user.
        if field.name in {
            "id",
            "user",
        }:

            continue


        # ----------------------------------------------------
        # Read current field value
        # ----------------------------------------------------

        value = getattr(
            profile_object,
            field.name,
            None,
        )


        # ----------------------------------------------------
        # Handle fields with display choices
        # ----------------------------------------------------

        # Django models can contain fields such as:
        #
        # ROLE_CHOICES = [
        #     ("beginner", "Beginner"),
        #     ("advanced", "Advanced"),
        # ]
        #
        # For these fields Django automatically creates a method
        # such as:
        #
        # get_role_display()
        #
        # Using that method gives the user the readable label
        # instead of the database code.
        display_method_name = (
            f"get_{field.name}_display"
        )


        if hasattr(
            profile_object,
            display_method_name,
        ):

            display_method = getattr(
                profile_object,
                display_method_name,
            )

            value = display_method()


        # ----------------------------------------------------
        # Add field to profile information
        # ----------------------------------------------------

        profile_details.append(
            (
                field.verbose_name.title(),
                value,
            )
        )


    # ========================================================
    # 6.11 BUILD TEMPLATE CONTEXT
    # ========================================================

    # Context contains everything profile.html needs:
    #
    # profile
    #     Complete UserProfile object
    #
    # account_details
    #     Information stored on accounts.User
    #
    # profile_details
    #     Additional information stored on UserProfile
    #
    # user_form
    #     Form for first name, last name and email
    #
    # profile_form
    #     Form for the additional UserProfile fields
    context = {

        "profile":
            profile_object,

        "account_details":
            account_details,

        "profile_details":
            profile_details,

        "user_form":
            user_form,

        "profile_form":
            profile_form,
    }


    # ========================================================
    # 6.12 RENDER PROFILE PAGE
    # ========================================================

    return render(
        request,
        "accounts/profile.html",
        context,
    )