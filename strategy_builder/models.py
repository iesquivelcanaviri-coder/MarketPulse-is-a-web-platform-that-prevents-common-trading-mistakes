""" strategy_builder/models.py
This module defines the database models for the strategy builder component of MarketPulse.
The strategy builder allows users to create trading strategies with specific rules and then
backtest those strategies against historical market data.
Key Models:
- StrategyRule: Defines individual rules within a trading strategy
- BacktestTrade: Records individual trades made during backtesting
This module connects with the core models (Strategy, Backtest) and user authentication. """

from django.db import models
from django.contrib.auth import get_user_model
from core.models import TimeStampedModel, Strategy, Backtest

# Get the custom User model (defined in accounts/models.py)
# This allows us to reference the User model without creating circular imports
User = get_user_model()


class StrategyRule(TimeStampedModel):
    """  Represents an individual rule within a trading strategy.
    A strategy consists of multiple rules that define when to buy, sell, or hold
    based on specific market conditions. Each rule has a condition (when it triggers)
    and an action (what to do when triggered).
    This model inherits from TimeStampedModel (defined in core/models.py) which
    automatically provides created_at and updated_at fields.
    Connected to:
    - Strategy (from core/models.py): The parent strategy this rule belongs to """
    # Foreign key relationship to the Strategy model
    # related_name='rules' allows us to access all rules of a strategy via strategy.rules
    # on_delete=models.CASCADE means if the strategy is deleted, all its rules are also deleted
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='rules')
    # Human-readable name for this rule (e.g., "Golden Cross", "RSI Oversold")
    name = models.CharField(max_length=100)
    # The condition that triggers this rule
    # This is stored as a string that will be parsed and evaluated during backtesting
    # Examples: "price > moving_average", "rsi < 30", "volume > average_volume"
    # In a production system, you might want to use a more structured approach
    condition = models.CharField(max_length=200)
    # The action to take when the condition is met
    # Using choices field restricts values to these predefined options
    # This ensures data consistency and provides a dropdown in forms
    action = models.CharField(
        max_length=20,
        choices=[
            ('buy', 'Buy'),      # Execute a buy order
            ('sell', 'Sell'),    # Execute a sell order
            ('hold', 'Hold'),    # Maintain current position
        ]
    )
    # JSON field to store parameters specific to this rule
    # This flexible field allows us to store different parameters for different rule types
    # Examples:
    # {"symbol": "AAPL", "period": 20, "threshold": 0.05}
    # {"indicator": "RSI", "oversold_level": 30}
    # Using default=dict ensures we always have a dictionary to work with
    parameters = models.JSONField(default=dict)
    # Boolean flag to enable/disable this rule
    # Allows users to temporarily turn off rules without deleting them
    is_active = models.BooleanField(default=True)
    def __str__(self):
        """ String representation of the StrategyRule object.
        This is used in Django admin and other places where objects need to be displayed. """
        return f"{self.name} - {self.action}"


class BacktestTrade(TimeStampedModel):
    """ Represents an individual trade made during a backtest.
    When a strategy is backtested against historical data, each buy/sell signal
    that gets executed creates a BacktestTrade record. These records are used
    to calculate performance metrics and analyze the strategy's behavior.
    This model inherits from TimeStampedModel (defined in core/models.py) which
    automatically provides created_at and updated_at fields.
    Connected to:
    - Backtest (from core/models.py): The backtest this trade belongs to """
    # Foreign key relationship to the Backtest model
    # related_name='trades' allows us to access all trades of a backtest via backtest.trades
    # on_delete=models.CASCADE means if the backtest is deleted, all its trades are also deleted
    backtest = models.ForeignKey(Backtest, on_delete=models.CASCADE, related_name='trades')
    # The stock/ETF/crypto symbol being traded (e.g., "AAPL", "BTC-USD")
    symbol = models.CharField(max_length=20)
    # The date when the trade was opened (buy for long, sell for short)
    entry_date = models.DateField()
    # The date when the trade was closed
    # null=True, blank=True allows this field to be empty for open trades
    exit_date = models.DateField(null=True, blank=True)
    # The price at which the trade was opened
    # Using DecimalField for financial calculations to avoid floating point errors
    # max_digits=10 allows for values up to 99,999.9999
    # decimal_places=4 provides precision to 4 decimal places (suitable for most stocks)
    entry_price = models.DecimalField(max_digits=10, decimal_places=4)
    # The price at which the trade was closed
    # null=True, blank=True allows this field to be empty for open trades
    exit_price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    # The number of shares/contracts traded
    quantity = models.IntegerField()
    # The type of trade (long or short)
    # Long: Betting the price will go up (buy then sell)
    # Short: Betting the price will go down (sell then buy)
    trade_type = models.CharField(
        max_length=10,
        choices=[
            ('long', 'Long'),    # Standard buy-low, sell-high trade
            ('short', 'Short'),  # Sell-high, buy-lower trade
        ]
    )
    # The profit or loss from this trade
    # Calculated as: (exit_price - entry_price) * quantity for long trades
    # or (entry_price - exit_price) * quantity for short trades
    # null=True, blank=True allows this field to be empty for open trades
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # The current status of the trade
    # Open: Trade has been opened but not yet closed
    # Closed: Trade has been completed with an exit
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),      # Trade is currently active
            ('closed', 'Closed'),  # Trade has been completed
        ],
        default='open'  # New trades start as open
    )
    def __str__(self):
        """ String representation of the BacktestTrade object.
        This is used in Django admin and other places where objects need to be displayed. """
        return f"{self.trade_type} {self.symbol} trade"