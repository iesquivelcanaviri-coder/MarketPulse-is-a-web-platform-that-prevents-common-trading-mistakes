""" 
accounts/models.py
This file defines the user-related models for the MarketPulse application.
It contains two main models:
1. User - A custom user model that extends Django's built-in AbstractUser
2. UserProfile - Additional user information specific to trading preferences
The User model replaces Django's default user model to add trading-specific fields,
while the UserProfile model stores additional preferences and settings that
don't need to be part of the core authentication system.
"""
# Import necessary Django components
from django.contrib.auth.models import AbstractUser  # Django's base user model
from django.db import models  # Django's database modeling tools

class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.  
    We extend AbstractUser instead of creating a completely new user model because
    AbstractUser already contains the core authentication fields like username,
    email, password, etc. This way we get all the built-in Django authentication
    functionality while adding our own trading-specific fields.
    """
    
    # Define user role choices as a tuple of tuples
    # This creates a dropdown in the admin interface and validates input
    USER_ROLES = (
        ('guest', 'Guest'),        # Limited access, can view public content only
        ('trader', 'Trader'),      # Standard user with trading capabilities
        ('admin', 'Admin'),        # Full administrative access
    )
    # Add a role field to the user model
    # CharField stores text data, max_length=20 limits it to 20 characters
    # choices=USER_ROLES restricts values to the predefined options
    # default='trader' sets the default role for new users
    role = models.CharField(max_length=20, choices=USER_ROLES, default='trader')
        # Email verification status - important for account security
    # BooleanField stores True/False values, default=False means unverified by default
    email_verified = models.BooleanField(default=False)
        # Timestamps for when the user was created and last updated
    # auto_now_add=True sets the field to the current timestamp when the object is first created
    created_at = models.DateTimeField(auto_now_add=True)
        # auto_now=True updates the field to the current timestamp every time the object is saved
    updated_at = models.DateTimeField(auto_now=True)


class UserProfile(models.Model):
    """
    Extended profile information for users.
    
    This model stores additional information about users that isn't part of the core
    authentication system. We use a OneToOneField to link each profile to exactly one
    user. This separation keeps the User model focused on authentication while
    allowing us to store trading-specific preferences here.
    """
    # Create a one-to-one relationship with the User model
    # on_delete=models.CASCADE means if the user is deleted, this profile is also deleted
    # related_name='profile' allows us to access the profile from a user object with user.profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Basic profile information
    # TextField is used for longer text content, max_length=500 limits the length
    # blank=True allows this field to be empty in forms
    bio = models.TextField(max_length=500, blank=True) 
    # CharField for shorter text like location, max_length=30 is sufficient
    location = models.CharField(max_length=30, blank=True)
    # DateField for storing dates (no time)
    # null=True, blank=True allows this field to be empty in the database and in forms
    birth_date = models.DateField(null=True, blank=True)
    # Trading-specific fields
    # IntegerField for whole numbers, default=0 means new users start with 0 experience
    trading_experience = models.IntegerField(default=0, help_text="Years of trading experience")    
    # Risk tolerance with predefined choices
    # This helps us tailor the user experience based on their comfort with risk
    risk_tolerance = models.CharField(
        max_length=20,
        choices=[
            ('conservative', 'Conservative'),  # Prefers low-risk investments
            ('moderate', 'Moderate'),          # Balanced approach to risk
            ('aggressive', 'Aggressive'),      # Comfortable with high-risk investments
        ],
        default='moderate'  # Most users start with moderate risk tolerance
    )
    # Maximum daily loss the user is willing to accept
    # DecimalField is used for money values to avoid floating point rounding errors
    # max_digits=10 allows for numbers up to 99,999,999.99
    # decimal_places=2 stores two decimal places for cents
    max_daily_loss = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    # Preferred trading markets
    # This helps us customize the data and tools shown to the user
    preferred_markets = models.CharField(
        max_length=100,
        choices=[
            ('stocks', 'Stocks'),           # Traditional stock market
            ('etfs', 'ETFs'),               # Exchange-traded funds
            ('crypto', 'Cryptocurrency'),    # Digital assets like Bitcoin
            ('forex', 'Forex'),             # Foreign exchange market
        ],
        default='stocks'  # Most users start with stock trading
    )
    # Timestamps for tracking when the profile was created and last updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """    String representation of the UserProfile model.
        This method defines how the object should be displayed when printed
        or shown in the Django admin interface. It's a good practice to make
        this human-readable and informative.
        Returns:
            str: A formatted string showing the username and indicating it's a profile """
        return f"{self.user.username}'s Profile"