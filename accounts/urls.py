# accounts/urls.py

# Import Django's path function for creating URL patterns
from django.urls import path
# Import Django's built-in authentication views (login, logout, etc.)
from django.contrib.auth import views as auth_views
# Import this app's custom views (register, profile, etc.)
from . import views

# Define the namespace for this app's URLs
# This allows us to reference these URLs with 'accounts:register' instead of just 'register'
app_name = 'accounts'

# Define the URL patterns for this app
# Each path() call creates a URL route that maps to a view
urlpatterns = [
    # Registration page URL
    # When someone visits /register/, Django calls the register view from our views.py
    # The 'name' parameter creates a named URL we can reference in templates and other code
    path('register/', views.register, name='register'),
    # Login page URL
    # Uses Django's built-in LoginView class-based view
    # template_name tells Django which HTML file to use for the login form
    # This saves us from writing a custom login view
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    # Logout URL
    # Uses Django's built-in LogoutView
    # No template needed since logout just redirects to the next page
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # User profile page URL
    # When someone visits /profile/, Django calls our custom profile view
    # This would show/edit the user's trading preferences and settings
    path('profile/', views.profile, name='profile'),
]