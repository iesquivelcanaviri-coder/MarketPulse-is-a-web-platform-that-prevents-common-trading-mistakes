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
UserAccountUpdateForm
    ↓
accounts.User
    ↓
PostgreSQL

        +

UserProfileForm
    ↓
accounts.UserProfile
    ↓
PostgreSQL


PURPOSE:

This file validates account information before Django
attempts to save the information into the database.

The forms in this file are responsible for:

- Registering new MarketPulse users
- Preventing duplicate usernames
- Preventing duplicate email addresses
- Allowing logged-in users to update account information
- Allowing logged-in users to update profile information
- Applying Bootstrap styling to form controls


This is particularly important for fields that must remain
unique, such as:

- Username
- Email address


REGISTRATION EXAMPLE:

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


PROFILE UPDATE EXAMPLE:

Logged-in user changes:

    first_name = Irene
    last_name = Esquivel
    email = newemail@example.com

        ↓

UserAccountUpdateForm

        ↓

Validate username and email

        ↓

Update existing accounts.User record

        ↓

PostgreSQL


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

                "autocomplete":
                    "email",
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

                "autocomplete":
                    "given-name",
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

                "autocomplete":
                    "family-name",
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
# 5. USER ACCOUNT UPDATE FORM
# ============================================================

class UserAccountUpdateForm(forms.ModelForm):
    """
    ============================================================
    MARKETPULSE USER ACCOUNT UPDATE
    ============================================================

    Allows an authenticated user to update information stored
    directly inside the accounts.User model.

    This is different from UserProfileForm.

    UserAccountUpdateForm updates:

    - Username
    - First name
    - Last name
    - Email address


    UserProfileForm updates:

    - Biography
    - Location
    - Trading experience
    - Risk tolerance
    - Maximum daily loss
    - Preferred markets


    Framework flow:

    Logged-in User
        ↓
    profile.html
        ↓
    UserAccountUpdateForm
        ↓
    Validate username
        ↓
    Validate email
        ↓
    Update existing accounts.User
        ↓
    PostgreSQL


    IMPORTANT:

    This form does NOT manage passwords.

    Password changes and forgotten-password recovery should
    use Django's dedicated password-management functionality.
    ============================================================
    """


    # ========================================================
    # 5.1 EMAIL FIELD
    # ========================================================

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class":
                    "form-control",

                "placeholder":
                    "Enter your email address",

                "autocomplete":
                    "email",
            }
        ),
    )


    # ========================================================
    # 5.2 FIRST NAME
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

                "autocomplete":
                    "given-name",
            }
        ),
    )


    # ========================================================
    # 5.3 LAST NAME
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

                "autocomplete":
                    "family-name",
            }
        ),
    )


    # ========================================================
    # 5.4 FORM MODEL CONFIGURATION
    # ========================================================

    class Meta:

        # Use the same custom MarketPulse user model.
        model = User


        # These fields can be edited from the profile page.
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
        )


        widgets = {

            "username":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",

                        "placeholder":
                            "Enter your username",

                        "autocomplete":
                            "username",
                    }
                ),
        }


    # ========================================================
    # 5.5 VALIDATE UPDATED USERNAME
    # ========================================================

    def clean_username(self):
        """
        Check that the new username is not already being used
        by another MarketPulse account.

        The currently logged-in user's own database record is
        excluded from the duplicate check.

        Example:

        Current user:
            username = irene

        User saves profile without changing username:
            irene

        This remains valid because the current user's record
        is excluded.

        However, if another account already uses:
            trader1

        and the current user attempts to change to:
            trader1

        the form displays a validation error.
        """


        username = (
            self.cleaned_data
            .get(
                "username",
                "",
            )
            .strip()
        )


        # ----------------------------------------------------
        # Require username
        # ----------------------------------------------------

        if not username:

            raise forms.ValidationError(
                "Please enter a username."
            )


        # ----------------------------------------------------
        # Search for another user with this username
        # ----------------------------------------------------

        duplicate_username = User.objects.filter(
            username__iexact=username
        )


        # ----------------------------------------------------
        # Exclude the user currently being edited
        # ----------------------------------------------------

        if self.instance and self.instance.pk:

            duplicate_username = (
                duplicate_username.exclude(
                    pk=self.instance.pk
                )
            )


        # ----------------------------------------------------
        # Reject username when another account owns it
        # ----------------------------------------------------

        if duplicate_username.exists():

            raise forms.ValidationError(
                (
                    "This username is already in use. "
                    "Please choose another username."
                )
            )


        return username


    # ========================================================
    # 5.6 VALIDATE UPDATED EMAIL
    # ========================================================

    def clean_email(self):
        """
        Check that another MarketPulse account is not already
        using the requested email address.

        The currently logged-in user's own account is excluded
        from the duplicate check.
        """


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
        # Require email
        # ----------------------------------------------------

        if not email:

            raise forms.ValidationError(
                "Please enter an email address."
            )


        # ----------------------------------------------------
        # Search for another account using the email
        # ----------------------------------------------------

        duplicate_email = User.objects.filter(
            email__iexact=email
        )


        # ----------------------------------------------------
        # Exclude the currently logged-in user
        # ----------------------------------------------------

        if self.instance and self.instance.pk:

            duplicate_email = (
                duplicate_email.exclude(
                    pk=self.instance.pk
                )
            )


        # ----------------------------------------------------
        # Reject duplicate email
        # ----------------------------------------------------

        if duplicate_email.exists():

            raise forms.ValidationError(
                (
                    "Another MarketPulse account is already "
                    "using this email address."
                )
            )


        return email


# ============================================================
# 6. USER PROFILE FORM
# ============================================================

class UserProfileForm(forms.ModelForm):
    """
    ============================================================
    MARKETPULSE USER PROFILE
    ============================================================

    Allows an authenticated MarketPulse user to update
    additional information stored inside UserProfile.

    This information is separate from the main accounts.User
    model.

    Profile information includes:

    - Biography
    - Location
    - Trading experience
    - Risk tolerance
    - Maximum daily loss
    - Preferred markets


    Framework flow:

    Logged-in User
        ↓
    profile.html
        ↓
    UserProfileForm
        ↓
    accounts.UserProfile
        ↓
    PostgreSQL
    ============================================================
    """


    # ========================================================
    # 6.1 FORM MODEL CONFIGURATION
    # ========================================================

    class Meta:

        model = UserProfile


        # These are the additional profile fields currently
        # available in the MarketPulse UserProfile model.
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

            # ------------------------------------------------
            # Location
            # ------------------------------------------------

            "location":
                forms.TextInput(
                    attrs={
                        "class":
                            "form-control",

                        "placeholder":
                            "Enter your location",
                    }
                ),

            # ------------------------------------------------
            # Maximum daily loss
            # ------------------------------------------------

            "max_daily_loss":
                forms.NumberInput(
                    attrs={
                        "class":
                            "form-control",

                        "placeholder":
                            "Enter your maximum daily loss",

                        "step":
                            "0.01",
                    }
                ),
        }


    # ========================================================
    # 6.2 PROFILE FORM INITIALISATION
    # ========================================================

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """
        Add consistent Bootstrap styling to profile fields
        without changing the underlying UserProfile model.

        Different widget types use different Bootstrap CSS
        classes.

        Examples:

        Text field
            → form-control

        Dropdown
            → form-select

        Checkbox
            → form-check-input
        """


        super().__init__(
            *args,
            **kwargs,
        )


        # ----------------------------------------------------
        # Apply Bootstrap classes
        # ----------------------------------------------------

        for field_name, field in self.fields.items():

            current_class = (
                field.widget.attrs.get(
                    "class",
                    "",
                )
            )


            # ------------------------------------------------
            # Individual checkbox
            # ------------------------------------------------

            if isinstance(
                field.widget,
                forms.CheckboxInput,
            ):

                field.widget.attrs[
                    "class"
                ] = "form-check-input"


            # ------------------------------------------------
            # Multiple checkbox options
            # ------------------------------------------------

            elif isinstance(
                field.widget,
                forms.CheckboxSelectMultiple,
            ):

                field.widget.attrs[
                    "class"
                ] = "form-check-input"


            # ------------------------------------------------
            # Dropdown / select menu
            # ------------------------------------------------

            elif isinstance(
                field.widget,
                forms.Select,
            ):

                field.widget.attrs[
                    "class"
                ] = (
                    current_class
                    +
                    " form-select"
                ).strip()


            # ------------------------------------------------
            # Normal text, number and textarea controls
            # ------------------------------------------------

            else:

                field.widget.attrs[
                    "class"
                ] = (
                    current_class
                    +
                    " form-control"
                ).strip()