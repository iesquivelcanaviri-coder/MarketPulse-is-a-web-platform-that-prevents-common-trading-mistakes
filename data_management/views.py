from django.shortcuts import render, redirect
# render: Renders a template with a context dictionary
# redirect: Redirects to a specific URL
from django.contrib.auth.decorators import login_required
# login_required: Decorator that ensures a user is logged in before accessing a view
from django.contrib import messages
# messages: Framework for displaying one-time notifications to users
from .models import DataImport, DataSource
# Importing our models from the current app's models.py file
# DataImport: Tracks data import requests and their status
# DataSource: Information about where data comes from (APIs, etc.)
from .utils import import_yahoo_finance_data
# Importing our utility function that actually fetches data from Yahoo Finance
from .forms import DataImportForm
# Importing the form class that validates user input for data imports

@login_required
# This decorator ensures only authenticated users can access this view
# If a non-authenticated user tries to access, they'll be redirected to the login page
def data_import(request):
    """ View function for handling data import requests from users.
    This view displays a form for users to specify what data they want to import,
    processes the form submission, and triggers the actual data import process.
    Connected to:
    - URL: Defined in data_management/urls.py
    - Template: data_management/import.html
    - Form: DataImportForm (from forms.py)
    - Utility: import_yahoo_finance_data (from utils.py)
    - Model: DataImport (from models.py)  """
    
    # Check if the form was submitted (POST request)
    if request.method == 'POST':
        # Create a form instance with the submitted data
        # DataImportForm validates the input and ensures required fields are provided
        form = DataImportForm(request.POST)
        # Check if the form data is valid according to the form's validation rules
        if form.is_valid():
            # Create a DataImport object from the form data but don't save to database yet
            # commit=False allows us to modify the object before saving
            data_import = form.save(commit=False)
            # Set the user field to the currently logged-in user
            # This associates the import request with the user who made it
            data_import.user = request.user
            # Now save the DataImport object to the database
            # At this point, the status is still 'pending' (default value)
            data_import.save()
            # Now we need to actually fetch the data from Yahoo Finance
            # We wrap this in a try/except block to handle potential errors
            try:
                # Call our utility function to fetch data from Yahoo Finance
                # Pass the symbol, start date, and end date from the form
                records = import_yahoo_finance_data(
                    data_import.symbol,
                    data_import.start_date,
                    data_import.end_date
                )
                # Update the DataImport record with the results
                # records_imported: Number of records successfully imported
                data_import.records_imported = records
                # Update the status to 'completed' to indicate success
                data_import.status = 'completed'
                # Save the updated record to the database
                data_import.save()
                # Display a success message to the user
                # This message will appear on the next page the user sees
                messages.success(request, f'Successfully imported {records} records for {data_import.symbol}')
            except Exception as e:
                # If anything went wrong during the import process
                # Update the status to 'failed' to indicate the import didn't succeed
                data_import.status = 'failed'
                # Store the error message for debugging purposes
                data_import.error_message = str(e)
                # Save the updated record to the database
                data_import.save()
                # Display an error message to the user
                # This message will appear on the next page the user sees
                messages.error(request, f'Failed to import data: {str(e)}')
            
            # Redirect the user to the import history page
            # This shows them all their import attempts and their status
            return redirect('data_management:import_history')
    else:
        # If it's a GET request (not a form submission), create an empty form
        # This is what users see when they first visit the import page
        form = DataImportForm()
    # Render the template with the form
    # The form will be displayed to the user for filling out
    return render(request, 'data_management/import.html', {'form': form})


@login_required
# This decorator ensures only authenticated users can access this view
def import_history(request):
    """  View function for displaying a user's data import history.
    This shows all the import requests a user has made and their status.
    Connected to:
    - URL: Defined in data_management/urls.py
    - Template: data_management/history.html
    - Model: DataImport (from models.py)  """
    # Query the database for all DataImport objects belonging to the current user
    # filter(user=request.user): Only get imports for the current user
    # order_by('-created_at'): Order by creation date, newest first
    imports = DataImport.objects.filter(user=request.user).order_by('-created_at')
    # Render the template with the imports data
    # The template will display each import in a table or list
    return render(request, 'data_management/history.html', {'imports': imports})