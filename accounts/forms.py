"""
============================================================
MARKETPULSE - ACCOUNTS FORMS
============================================================

FRAMEWORK MAPPING:

Registration Page
    ↓
UserRegistrationForm
    ↓
Validate username
    ↓
Validate email address
    ↓
Validate passwords
    ↓
accounts.User
    ↓
PostgreSQL


Profile Page
    ↓
UserProfileForm
    ↓
accounts.UserProfile
    ↓
PostgreSQL


PURPOSE:

This file validates account information before Django
attempts to save the information into the database.

This is particularly important for fields that must remain
unique, such as:

- Username
- Email address


EXAMPLE:

User enters:

    username = user2

        ↓

UserRegistrationForm.clean_username()

        ↓

Does user2 already exist?

        ↓

YES
    → Display a validation message
    → Do NOT attempt another database insert

NO
    → Continue registration


This prevents PostgreSQL errors such as:

    duplicate key value violates unique constraint
    "accounts_user_username_key"

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

# Django forms provides the standard form and ModelForm
# functionality used throughout the accounts application.
from django import forms


# get_user_model() returns the custom user model configured in:
#
# marketpulse/settings.py
#
# AUTH_USER_MODEL = "accounts.User"
#
# Using this function is safer than importing Django's
# default User model directly because MarketPulse uses its
# own custom user model.
from django.contrib.auth import get_user_model


# UserCreationForm provides Django's built-in registration
# functionality, including:
#
# - password1
# - password2
# - password matching
# - password validation
# - secure password hashing
from django.contrib.auth.forms import UserCreationForm


# ============================================================
# 2. MARKETPULSE ACCOUNT MODELS
# ============================================================

# UserProfile stores additional MarketPulse information
# associated with the authenticated user.
from .models import UserProfile


# ============================================================
# 3. CUSTOM USER MODEL
# ============================================================

# This retrieves:
#
# accounts.User
#
# because MarketPulse defines:
#
# AUTH_USER_MODEL = "accounts.User"
#
# in settings.py.
User = get_user_model()


# ============================================================
# 4. USER REGISTRATION FORM
# ============================================================

class UserRegistrationForm(UserCreationForm):
    """
    ============================================================
    MARKETPULSE USER REGISTRATION
    ============================================================

    This form validates information submitted through the
    MarketPulse registration page.

    Registration workflow:

    User
        ↓
    register.html
        ↓
    UserRegistrationForm
        ↓
    Username validation
        ↓
    Email validation
        ↓
    Password validation
        ↓
    accounts.User
        ↓
    PostgreSQL


    IMPORTANT:

    Username and email validation takes place BEFORE
    form.save() attempts to create the database record.

    This means the user receives a normal validation message
    rather than a database IntegrityError.
    ============================================================
    """


    # ========================================================
    # 4.1 EMAIL FIELD
    # ========================================================

    # Email is required when creating a MarketPulse account.
    #
    # forms.EmailField also performs basic email-format
    # validation.
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class":
                    "form-control",

                "placeholder":
                    "Enter your email address",
            }
        ),
    )


    # ========================================================
    # 4.2 FIRST NAME
    # ========================================================

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class":
                    "form-control",

                "placeholder":
                    "Enter your first name",
            }
        ),
    )


    # ========================================================
    # 4.3 LAST NAME
    # ========================================================

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class":
                    "form-control",

                "placeholder":
                    "Enter your last name",
            }
        ),
    )


    # ========================================================
    # 4.4 FORM MODEL CONFIGURATION
    # ========================================================

    class Meta:

        # IMPORTANT:
        #
        # This points to MarketPulse's custom accounts.User
        # model instead of Django's default User model.
        model = User


        # Fields displayed and processed during registration.
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


        # Bootstrap styling for the username field.
        widgets = {

            "username":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",

                        "placeholder":
                            "Choose a username",

                        "autocomplete":
                            "username",
                    }
                ),
        }


    # ========================================================
    # 4.5 FORM INITIALISATION
    # ========================================================

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """
        Apply consistent Bootstrap styling to Django's
        password fields.

        password1 and password2 are inherited from
        UserCreationForm, so their widgets are configured
        here rather than inside Meta.widgets.
        """

        super().__init__(
            *args,
            **kwargs,
        )


        # ----------------------------------------------------
        # Password 1 styling
        # ----------------------------------------------------

        self.fields[
            "password1"
        ].widget.attrs.update(
            {
                "class":
                    "form-control",

                "placeholder":
                    "Create a password",

                "autocomplete":
                    "new-password",
            }
        )


        # ----------------------------------------------------
        # Password 2 styling
        # ----------------------------------------------------

        self.fields[
            "password2"
        ].widget.attrs.update(
            {
                "class":
                    "form-control",

                "placeholder":
                    "Confirm your password",

                "autocomplete":
                    "new-password",
            }
        )


    # ========================================================
    # 4.6 VALIDATE USERNAME
    # ========================================================

    def clean_username(self):
        """
        Prevent duplicate usernames before Django attempts
        to insert a new User into PostgreSQL.

        Example:

        Existing database username:
            user2

        New registration:
            user2

        Result:
            ValidationError

        rather than:
            PostgreSQL IntegrityError
        """


        # Retrieve the value already processed by Django.
        username = (
            self.cleaned_data
            .get(
                "username",
                "",
            )
            .strip()
        )


        # ----------------------------------------------------
        # Require a value
        # ----------------------------------------------------

        if not username:

            raise forms.ValidationError(
                "Please enter a username."
            )


        # ----------------------------------------------------
        # Check existing usernames
        # ----------------------------------------------------

        # __iexact performs a case-insensitive comparison.
        #
        # For example:
        #
        # user2
        # User2
        # USER2
        #
        # are treated as the same registration identity.
        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise forms.ValidationError(
                (
                    "This username is already in use. "
                    "Please choose another username."
                )
            )


        # Return the cleaned value when validation succeeds.
        return username


    # ========================================================
    # 4.7 VALIDATE EMAIL
    # ========================================================

    def clean_email(self):
        """
        Prevent multiple MarketPulse accounts from being
        registered using the same email address.
        """


        # Retrieve the email safely.
        email = (
            self.cleaned_data
            .get(
                "email",
                "",
            )
            .strip()
            .lower()
        )


        # ----------------------------------------------------
        # Require an email value
        # ----------------------------------------------------

        if not email:

            raise forms.ValidationError(
                "Please enter an email address."
            )


        # ----------------------------------------------------
        # Check for duplicate email
        # ----------------------------------------------------

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                (
                    "An account with this email address "
                    "already exists."
                )
            )


        return email


# ============================================================
# 5. USER PROFILE FORM
# ============================================================

class UserProfileForm(forms.ModelForm):
    """
    ============================================================
    MARKETPULSE USER PROFILE
    ============================================================

    Allows an authenticated MarketPulse user to update
    additional profile information.

    Framework flow:

    Profile Page
        ↓
    UserProfileForm
        ↓
    UserProfile
        ↓
    PostgreSQL
    ============================================================
    """


    class Meta:

        model = UserProfile


        fields = (
            "bio",
            "location",
            "trading_experience",
            "risk_tolerance",
            "max_daily_loss",
            "preferred_markets",
        )


        widgets = {

            # ------------------------------------------------
            # Biography
            # ------------------------------------------------

            "bio":
                forms.Textarea(
                    attrs={
                        "rows":
                            4,

                        "class":
                            "form-control",

                        "placeholder":
                            "Tell us a little about yourself",
                    }
                ),
        }


    # ========================================================
    # 5.1 PROFILE FORM INITIALISATION
    # ========================================================

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """
        Add consistent Bootstrap styling to profile fields
        without changing the underlying UserProfile model.
        """


        super().__init__(
            *args,
            **kwargs,
        )


        # ----------------------------------------------------
        # Apply Bootstrap classes
        # ----------------------------------------------------

        for field_name, field in self.fields.items():

            # The bio field already has its CSS class set
            # above, but updating it here is harmless.
            current_class = (
                field.widget.attrs.get(
                    "class",
                    "",
                )
            )


            # Checkbox widgets should use Bootstrap's
            # form-check-input class rather than form-control.
            if isinstance(
                field.widget,
                forms.CheckboxInput,
            ):

                field.widget.attrs[
                    "class"
                ] = "form-check-input"


            # Multiple checkbox fields may use a
            # CheckboxSelectMultiple widget.
            elif isinstance(
                field.widget,
                forms.CheckboxSelectMultiple,
            ):

                field.widget.attrs[
                    "class"
                ] = "form-check-input"


            else:

                field.widget.attrs[
                    "class"
                ] = (
                    current_class
                    +
                    " form-control"
                ).strip()