""" Core models for MarketPulse application.
This module contains the fundamental data models that form the backbone of our trading platform.
These models handle market data, trading strategies, backtesting results, and user alerts.
Each model is designed to be extensible and maintain data integrity."""

from django.db import models
from django.contrib.auth import get_user_model

# Get the custom User model (defined in accounts/models.py)
# This allows us to reference the User model without creating circular imports
User = get_user_model()


class TimeStampedModel(models.Model):
    """ Abstract base model that provides timestamp fields for all other models.
    This is a common Django pattern where we create a base model with fields that
    multiple other models will need. By making it abstract (Meta.abstract = True),
    Django won't create a database table for this model, but will instead copy
    its fields to any model that inherits from it.
    Attributes:
        created_at (DateTimeField): Automatically set when the object is first created
        updated_at (DateTimeField): Automatically updated every time the object is saved """
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the record was last updated")

    class Meta:
        abstract = True  # This makes the model abstract - no database table is created


class MarketData(TimeStampedModel):
    """ Model for storing historical market data for various financial instruments.
    This model stores OHLCV (Open, High, Low, Close, Volume) data for stocks,
    ETFs, indices, etc. Each record represents one day of price data for a symbol.
    The model inherits from TimeStampedModel, so it automatically gets created_at
    and updated_at fields.
    Attributes:
        symbol (CharField): Trading symbol (e.g., 'AAPL', 'GOOGL')
        date (DateField): Date of the market data
        open_price (DecimalField): Opening price for the day
        high_price (DecimalField): Highest price during the day
        low_price (DecimalField): Lowest price during the day
        close_price (DecimalField): Closing price for the day
        volume (BigIntegerField): Trading volume for the day  """
    symbol = models.CharField(max_length=20, help_text="Trading symbol (e.g., AAPL)")
    date = models.DateField(help_text="Date of the market data")
    # Using DecimalField instead of FloatField for financial data to avoid rounding errors
    # max_digits=10 allows for values up to 99999999.9999
    # decimal_places=4 stores 4 decimal places, which is sufficient for most stock prices
    open_price = models.DecimalField(max_digits=10, decimal_places=4, help_text="Opening price")
    high_price = models.DecimalField(max_digits=10, decimal_places=4, help_text="Highest price")
    low_price = models.DecimalField(max_digits=10, decimal_places=4, help_text="Lowest price")
    close_price = models.DecimalField(max_digits=10, decimal_places=4, help_text="Closing price")
    # BigIntegerField for volume as trading volume can be very large
    volume = models.BigIntegerField(default=0, help_text="Trading volume for the day")

    class Meta:
        # Ensures that there's only one record per symbol per date
        # This prevents duplicate data entries
        unique_together = ('symbol', 'date')
        # Default ordering for queries - newest dates first
        # The '-' prefix indicates descending order
        ordering = ['-date']

    def __str__(self):
        """String representation of the model instance.
        This is used in Django admin and other places where the model is displayed.
        Returns a human-readable representation of the market data record. """
        return f"{self.symbol} - {self.date}"


class Strategy(TimeStampedModel):
    """Model for storing trading strategies created by users.
    A strategy represents a set of rules and conditions that determine when
    to buy or sell financial instruments. Each strategy is owned by a user
    and can be activated or deactivated.
    The rules field uses JSONField to store flexible rule definitions that
    can vary between different strategies.
    Attributes:
        name (CharField): Human-readable name for the strategy
        description (TextField): Detailed description of how the strategy works
        user (ForeignKey): User who created this strategy
        is_active (BooleanField): Whether the strategy is currently active
        rules (JSONField): Flexible storage for strategy rules and parameters  """
    name = models.CharField(max_length=100, help_text="Name of the trading strategy")
    description = models.TextField(blank=True, help_text="Description of how the strategy works")
    # ForeignKey creates a many-to-one relationship with User
    # Each strategy belongs to exactly one user, but a user can have many strategies
    # on_delete=models.CASCADE means if the user is deleted, all their strategies are also deleted
    # related_name='strategies' allows us to access a user's strategies with user.strategies.all()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategies')
    is_active = models.BooleanField(default=True, help_text="Whether the strategy is currently active")
    # JSONField allows us to store structured data (like dictionaries) in the database
    # This is perfect for storing flexible rule definitions that can vary between strategies
    # default=dict ensures the field always has a valid JSON object (empty dict if no rules)
    rules = models.JSONField(default=dict, help_text="Strategy rules and parameters in JSON format")

    def __str__(self):
        """ String representation showing the strategy name and creator."""
        return f"{self.name} by {self.user.username}"


class Backtest(TimeStampedModel):
    """Model for storing results of strategy backtests.
    A backtest simulates how a strategy would have performed on historical data.
    This model stores the input parameters and calculated performance metrics.
    Each backtest is associated with a specific strategy and contains various
    performance metrics that help evaluate the strategy's effectiveness.
    Attributes:
        strategy (ForeignKey): The strategy being tested
        start_date (DateField): Start date of the backtest period
        end_date (DateField): End date of the backtest period
        initial_capital (DecimalField): Starting capital for the backtest
        final_capital (DecimalField): Ending capital after the backtest
        total_return (DecimalField): Total return as a percentage (e.g., 0.1523 for 15.23%)
        max_drawdown (DecimalField): Maximum drawdown experienced (e.g., 0.0875 for 8.75%)
        sharpe_ratio (DecimalField): Risk-adjusted return metric
        win_rate (DecimalField): Percentage of winning trades (e.g., 0.65 for 65%)
        total_trades (IntegerField): Total number of trades executed
        results (JSONField): Detailed results in JSON format """
    # Each backtest belongs to exactly one strategy
    # related_name='backtests' allows us to access a strategy's backtests with strategy.backtests.all()
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='backtests')
    start_date = models.DateField(help_text="Start date of the backtest period")
    end_date = models.DateField(help_text="End date of the backtest period")
    # Using larger max_digits for capital values as they can be substantial
    initial_capital = models.DecimalField(max_digits=12, decimal_places=2, help_text="Starting capital")
    final_capital = models.DecimalField(max_digits=12, decimal_places=2, help_text="Ending capital")
    # Performance metrics with appropriate precision
    total_return = models.DecimalField(max_digits=8, decimal_places=4, help_text="Total return as decimal (e.g., 0.1523 for 15.23%)")
    max_drawdown = models.DecimalField(max_digits=8, decimal_places=4, help_text="Maximum drawdown as decimal")
    sharpe_ratio = models.DecimalField(max_digits=8, decimal_places=4, help_text="Sharpe ratio (risk-adjusted return)")
    # Win rate stored as decimal (e.g., 0.65 for 65%) with precision for 2 decimal places
    win_rate = models.DecimalField(max_digits=5, decimal_places=4, help_text="Win rate as decimal (e.g., 0.65 for 65%)")
    total_trades = models.IntegerField(default=0, help_text="Total number of trades executed")
    # Store detailed results like trade-by-trade data, equity curve, etc.
    results = models.JSONField(default=dict, help_text="Detailed backtest results in JSON format")

    def __str__(self):
        """ String representation showing which strategy was tested and the period."""
        return f"Backtest for {self.strategy.name} ({self.start_date} to {self.end_date})"


class Alert(TimeStampedModel):
    """Model for storing user notifications and alerts.
    Alerts are generated by the system to notify users of important events
    like price movements, strategy signals, or risk warnings.
    Each alert is associated with a user and can be marked as read or unread.
    The alert_type field categorizes alerts for better organization.
    Attributes:
        ALERT_TYPES (tuple): Choices for alert types
        user (ForeignKey): User who will receive this alert
        alert_type (CharField): Type of alert (price, strategy, or risk)
        title (CharField): Brief title of the alert
        message (TextField): Detailed message content
        is_read (BooleanField): Whether the user has read this alert
        is_active (BooleanField): Whether this alert is currently active"""
    # Define choices for alert_type field
    # This creates a dropdown in Django admin and validates input
    ALERT_TYPES = (
        ('price', 'Price Alert'),      # Alert for price movements
        ('strategy', 'Strategy Alert'), # Alert for strategy signals
        ('risk', 'Risk Alert'),        # Alert for risk management
    )
    # Each alert belongs to exactly one user
    # related_name='alerts' allows us to access a user's alerts with user.alerts.all()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    # Use choices to restrict values to those defined in ALERT_TYPES
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, help_text="Type of alert")
    title = models.CharField(max_length=200, help_text="Brief title of the alert")
    message = models.TextField(help_text="Detailed alert message")
    is_read = models.BooleanField(default=False, help_text="Whether the user has read this alert")
    is_active = models.BooleanField(default=True, help_text="Whether this alert is currently active")

    def __str__(self):
        """String representation showing the alert type and title."""
        return f"{self.alert_type}: {self.title}"