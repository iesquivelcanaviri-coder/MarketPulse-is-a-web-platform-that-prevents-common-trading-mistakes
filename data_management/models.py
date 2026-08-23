"""data_management/models.py
This module defines the data models for managing financial data sources and imports in MarketPulse.
It handles where our market data comes from and tracks the import process.
Key Concepts:
- DataSource: Represents external data providers like Yahoo Finance
- DataImport: Tracks individual data import requests and their status
- TimeStampedModel: Inherited from core.models to automatically track creation/update times"""

# Import Django's database models module - this provides all the field types and model functionality
from django.db import models
# Import our base model that automatically adds created_at and updated_at fields
from core.models import TimeStampedModel
# Import the User model - using get_user_model() is the proper way in Django
# This allows us to use a custom User model if we've defined one
from django.contrib.auth import get_user_model
# Get the active User model (either Django's default or our custom one)
User = get_user_model()


class DataSource(TimeStampedModel):
    """  Represents an external source of financial data.
    This model stores information about where we can get market data from.
    Examples include Yahoo Finance, Alpha Vantage, or other financial data providers.
    Inherits from TimeStampedModel which automatically provides:
    - created_at: When this data source was first added to our system
    - updated_at: When this data source was last modified  """
    # A human-readable name for the data source (e.g., "Yahoo Finance", "Alpha Vantage")
    # CharField is used for short text fields with a maximum length
    name = models.CharField(max_length=100)
    # The URL or endpoint where we can access this data source's API
    # URLField validates that the input is a properly formatted URL
    url = models.URLField()
    # Indicates whether this data source requires an API key for access
    # BooleanField stores True/False values - defaults to False (no API key needed)
    api_key_required = models.BooleanField(default=False)    
    # Whether this data source is currently active and available for use
    # This allows us to temporarily disable sources without deleting them
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        """  String representation of the DataSource model.
                This method defines how a DataSource object appears when printed or displayed
        in Django admin or other interfaces. It returns the name of the data source. """
        return self.name


class DataImport(TimeStampedModel):
    """Tracks individual data import requests and their status.
    This model records each time a user requests to import market data for a specific symbol.
    It tracks the progress and results of the import process, including any errors that occur.
    Inherits from TimeStampedModel which automatically provides:
    - created_at: When this import request was first made
    - updated_at: When this import request was last modified  """
    # Foreign key to the User who requested this data import
    # This creates a many-to-one relationship: one user can have many data imports
    # on_delete=models.CASCADE means if the user is deleted, all their data imports are also deleted
    # related_name='data_imports' allows us to access all imports for a user with user.data_imports
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_imports')
    # The stock symbol or ticker being imported (e.g., "AAPL", "GOOGL", "BTC-USD")
    # CharField with max_length=20 is sufficient for most stock symbols
    symbol = models.CharField(max_length=20)
    # Foreign key to the DataSource being used for this import
    # This connects this import to a specific data provider
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    # The start date for the historical data being imported
    # DateField stores date values (year, month, day) without time information
    start_date = models.DateField()
    # The end date for the historical data being imported
    end_date = models.DateField()
    # The current status of the import process
    # CharField with choices restricts the value to one of the predefined options
    # This ensures data consistency and makes the status easy to understand
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),        # Import request received but not yet processed
            ('processing', 'Processing'),  # Currently importing data
            ('completed', 'Completed'),    # Import completed successfully
            ('failed', 'Failed'),          # Import failed due to an error
        ],
        default='pending'  # New imports start with 'pending' status
    )
    # The number of records (data points) that were successfully imported
    # IntegerField stores whole numbers, defaulting to 0 when created
    records_imported = models.IntegerField(default=0)
    # Stores any error message if the import fails
    # TextField is used for longer text that doesn't have a length limit
    # blank=True allows this field to be empty in the database
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        """  String representation of the DataImport model.
        This method defines how a DataImport object appears when printed or displayed.
        It shows the symbol being imported and the source name for easy identification.
        Uses an f-string to format the output with the symbol and source name."""
        return f"{self.symbol} import from {self.source.name}"