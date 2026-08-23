# Import necessary Django components
from django.contrib.auth.forms import UserCreationForm  # Django's built-in form for user registration
from django.contrib.auth.models import User               # Django's built-in User model
from django import forms                                   # Django's forms module for creating custom forms
from .models import UserProfile                            # Import our custom UserProfile model from the same app

""" This file defines forms for user registration and profile management.
Forms in Django handle user input, validation, and data conversion.
They provide a secure way to process user data and interact with models. """

class UserRegistrationForm(UserCreationForm):
    """ Custom user registration form that extends Django's built-in UserCreationForm.
    We're adding additional fields beyond the default username and password fields.
    In Django, forms automatically handle validation, error messages, and HTML rendering.
    This makes it easier to create secure, consistent user interfaces.  """
    # Additional fields beyond what UserCreationForm provides by default
    email = forms.EmailField(required=True)  # Email field with email validation
    first_name = forms.CharField(max_length=30, required=True)  # User's first name
    last_name = forms.CharField(max_length=30, required=True)   # User's last name
    class Meta:
        """ The Meta class is a Django convention for providing configuration options.
        Here we're specifying which model this form is associated with and which fields to include."""
        model = User  # This form will create/update User model instances
        # Fields to include in the form, in this order:
        # 'username' and 'password1', 'password2' come from UserCreationForm
        # 'first_name', 'last_name', 'email' are our custom additions
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        """Custom save method that processes the form data before saving to the database.
        This method is called when the form is valid and we want to save the data.
        Args:
            commit (bool): If True, saves the user to the database immediately.
                           If False, creates the user object but doesn't save it yet.
                           This allows for additional processing before saving.
        Returns: User: The created User instance """
        # Call the parent class's save method with commit=False
        # This creates the user object but doesn't save it to the database yet
        user = super().save(commit=False)
        # Set the additional fields from the cleaned form data
        # cleaned_data is a dictionary containing validated form values
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # If commit is True, save the user to the database
        if commit:
            user.save()
        # Return the user object (whether saved or not)
        return user

class UserProfileForm(forms.ModelForm):
    """ Form for editing the user's profile information.
    This form works with our custom UserProfile model, which extends the base User model.
    ModelForm is a Django feature that automatically generates a form from a model.
    It handles field types, validation, and saving to the database. """
    class Meta:
        """ Configure the form by specifying the model and fields to include. """
        model = UserProfile  # This form works with our UserProfile model
        # Fields from the UserProfile model to include in the form:
        # 'bio' - User's biography/description
        # 'location' - User's location
        # 'birth_date' - User's date of birth
        # 'trading_experience' - Years of trading experience
        # 'risk_tolerance' - User's risk tolerance level
        # 'max_daily_loss' - Maximum daily loss amount
        # 'preferred_markets' - Preferred trading markets
        fields = ('bio', 'location', 'birth_date', 'trading_experience',
                 'risk_tolerance', 'max_daily_loss', 'preferred_markets')
        # Custom widgets to control how fields are rendered in HTML
        widgets = {
            # Use HTML5 date input for birth_date field
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            # Use textarea for bio field with 4 rows
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
        """ Widgets control how form fields are rendered as HTML elements.
        By default, Django uses appropriate widgets based on field types,
        but we can customize them for better user experience.
        The attrs parameter allows us to add HTML attributes to the input element.
        For example, 'type': 'date' tells the browser to show a date picker interface."""