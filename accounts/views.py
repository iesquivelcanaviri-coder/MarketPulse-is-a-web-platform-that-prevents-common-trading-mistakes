from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm
from .models import UserProfile


def register(request):
    """ Handles user registration for new accounts.
    This view processes both GET and POST requests:
    - GET: Displays the registration form
    - POST: Processes form submission, creates user, and creates associated profile
    Connected to URL pattern: 'accounts/register/'
    Uses template: 'accounts/register.html'
    """
    # Check if the form was submitted (POST request)
    if request.method == 'POST':
        # Create a form instance with POST data
        form = UserRegistrationForm(request.POST)
        # Validate the form data
        if form.is_valid():
            # Save the user to the database
            user = form.save()
            # Create a UserProfile instance linked to the new user
            # This is important because our custom User model extends Django's default
            # and we need to store additional trading-specific information
            UserProfile.objects.create(user=user)
            # Get the username from cleaned form data for the success message
            username = form.cleaned_data.get('username')
            # Add a success message to be displayed on the next page
            messages.success(request, f'Account created for {username}! You can now log in.')
            # Redirect to the login page after successful registration
            return redirect('accounts:login')
    else:
        # If it's a GET request, create an empty form
        form = UserRegistrationForm()
    # Render the registration template with the form context
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    """   Displays and updates the user's profile information.
    The @login_required decorator ensures only authenticated users can access this view.
    If an unauthenticated user tries to access, they'll be redirected to the login page.
    This view handles both displaying and updating profile information.
    Connected to URL pattern: 'accounts/profile/'
    Uses template: 'accounts/profile.html'
    """
    # Try to get the user's profile, handling the case where it might not exist yet
    try:
        # Get the UserProfile related to the current logged-in user
        # request.user is automatically available in all views and represents
        # the currently authenticated user
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # If the profile doesn't exist (which could happen if we created users
        # before implementing the UserProfile model), create one now
        profile = UserProfile.objects.create(user=request.user)
    
    # Check if the form was submitted (POST request)
    if request.method == 'POST':
        # Create a form instance with POST data and the existing profile instance
        # The instance parameter tells the form to update this specific profile
        # rather than creating a new one
        form = UserProfileForm(request.POST, instance=profile)
        # Validate the form data
        if form.is_valid():
            # Save the updated profile information to the database
            form.save()
            # Add a success message to be displayed on the page
            messages.success(request, 'Your profile has been updated!')
            # Redirect back to the profile page to show the updated information
            return redirect('accounts:profile')
    else:
        # If it's a GET request, create a form with the existing profile data
        # The instance parameter pre-fills the form with current profile values
        form = UserProfileForm(instance=profile)
    
    # Render the profile template with the form context
    # The form will either be empty (for GET) or contain validation errors (for invalid POST)
    return render(request, 'accounts/profile.html', {'form': form})