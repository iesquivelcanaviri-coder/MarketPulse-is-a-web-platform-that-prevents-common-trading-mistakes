"""
============================================================
MARKETPULSE - STRATEGY BUILDER MODELS
============================================================

Framework mapping:

core.models.Strategy
        ↓
StrategyRule
        ↓
Defines the individual IF / THEN rules belonging to a strategy
        ↓
strategy_builder/backtesting.py


core.models.Backtest
        ↓
BacktestTrade
        ↓
Stores individual simulated trades produced during a backtest


StrategyLibraryItem
        ↓
strategy_builder/library.py
        ↓
Strategy Library
        +
Data tab model selector
        ↓
Future Model Runner
        ↓
Forecasting / Simulation / Backtesting / Risk Analysis


IMPORTANT:

Strategy and Backtest remain inside:

core/models.py


StrategyRule and BacktestTrade intentionally match the
existing database structure defined in:

strategy_builder/migrations/0001_initial.py


StrategyLibraryItem is the NEW model being added for the
MarketPulse quantitative model library.
============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

from django.db import models

from core.models import (
    Backtest,
    Strategy,
    TimeStampedModel,
)


# ============================================================
# 2. STRATEGY RULE MODEL
# ============================================================

class StrategyRule(TimeStampedModel):
    """
    ============================================================
    STRATEGY RULE
    ============================================================

    Framework mapping:

    core.Strategy
        ↓
    StrategyRule
        ↓
    strategy.rules
        ↓
    strategy_builder/backtesting.py


    PURPOSE:

    A Strategy can contain multiple StrategyRule records.

    The rule identifies:

    - The strategy it belongs to
    - The market symbol
    - The type of condition
    - The action to perform
    - Parameters used by the condition
    - Whether the rule is currently active


    IMPORTANT:

    This model intentionally matches the original
    strategy_builder/0001_initial.py migration.

    Existing database fields must be preserved so Django
    does not attempt to redesign the original table.
    ============================================================
    """


    # ========================================================
    # 2.1 STRATEGY RELATIONSHIP
    # ========================================================

    # Links this rule to its parent Strategy.
    #
    # related_name="rules" allows:
    #
    # strategy.rules.all()
    #
    # to retrieve all rules belonging to one strategy.
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name="rules",
    )


    # ========================================================
    # 2.2 RULE NAME
    # ========================================================

    # Human-readable name for the rule.
    #
    # Examples:
    #
    # Golden Cross Entry
    # Death Cross Exit
    name = models.CharField(
        max_length=160,
    )


    # ========================================================
    # 2.3 MARKET SYMBOL
    # ========================================================

    # Market ticker that this rule applies to.
    #
    # Examples:
    #
    # AAPL
    # MSFT
    # NVDA
    # SPY
    # BTC-USD
    symbol = models.CharField(
        max_length=20,
    )


    # ========================================================
    # 2.4 CONDITION TYPE
    # ========================================================

    # The original MarketPulse strategy engine supports
    # moving-average crossover rules.
    #
    # These values intentionally match 0001_initial.py.
    condition_type = models.CharField(
        max_length=30,
        choices=[
            (
                "ma_cross_up",
                "Fast MA crosses above Slow MA",
            ),
            (
                "ma_cross_down",
                "Fast MA crosses below Slow MA",
            ),
        ],
    )


    # ========================================================
    # 2.5 ACTION
    # ========================================================

    # Action performed when the rule condition is triggered.
    #
    # These values intentionally match 0001_initial.py.
    action = models.CharField(
        max_length=10,
        choices=[
            (
                "buy",
                "Buy",
            ),
            (
                "sell",
                "Sell",
            ),
        ],
    )


    # ========================================================
    # 2.6 RULE PARAMETERS
    # ========================================================

    # JSON allows each strategy rule to store the numerical
    # settings required by its condition.
    #
    # Example:
    #
    # {
    #     "fast_period": 20,
    #     "slow_period": 50
    # }
    parameters = models.JSONField(
        default=dict,
    )


    # ========================================================
    # 2.7 ACTIVE STATUS
    # ========================================================

    # Allows a rule to be disabled without deleting it.
    is_active = models.BooleanField(
        default=True,
    )


    # ========================================================
    # 2.8 STRING REPRESENTATION
    # ========================================================

    def __str__(self):
        """
        Used by Django Admin, debugging output and dropdowns.
        """

        return (
            f"{self.name} - "
            f"{self.symbol} - "
            f"{self.get_action_display()}"
        )


# ============================================================
# 3. BACKTEST TRADE MODEL
# ============================================================

class BacktestTrade(TimeStampedModel):
    """
    ============================================================
    BACKTEST TRADE
    ============================================================

    Framework mapping:

    core.Backtest
        ↓
    BacktestTrade
        ↓
    strategy_builder/backtesting.py
        ↓
    Simulated historical trades
        ↓
    Performance calculations


    PURPOSE:

    Every simulated trade created during a historical
    backtest is stored as one BacktestTrade record.


    IMPORTANT:

    This model intentionally matches the original
    strategy_builder/0001_initial.py migration.

    We are NOT adding trade_type here because that field
    did not exist in the original database schema.
    ============================================================
    """


    # ========================================================
    # 3.1 BACKTEST RELATIONSHIP
    # ========================================================

    # Links the trade to the Backtest that generated it.
    #
    # related_name="trades" allows:
    #
    # backtest.trades.all()
    backtest = models.ForeignKey(
        Backtest,
        on_delete=models.CASCADE,
        related_name="trades",
    )


    # ========================================================
    # 3.2 MARKET SYMBOL
    # ========================================================

    # Examples:
    #
    # AAPL
    # MSFT
    # SPY
    # BTC-USD
    symbol = models.CharField(
        max_length=20,
    )


    # ========================================================
    # 3.3 ENTRY DATE
    # ========================================================

    # Date the simulated position was opened.
    entry_date = models.DateField()


    # ========================================================
    # 3.4 EXIT DATE
    # ========================================================

    # May remain empty while the simulated trade is open.
    exit_date = models.DateField(
        null=True,
        blank=True,
    )


    # ========================================================
    # 3.5 ENTRY PRICE
    # ========================================================

    # max_digits=14 intentionally matches the original
    # 0001_initial.py migration.
    entry_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
    )


    # ========================================================
    # 3.6 EXIT PRICE
    # ========================================================

    # May remain empty while the simulated trade is open.
    #
    # max_digits=14 intentionally matches the original
    # migration.
    exit_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
    )


    # ========================================================
    # 3.7 REQUESTED QUANTITY
    # ========================================================

    # Number of units that the strategy originally attempted
    # to buy or sell.
    #
    # This is useful when comparing requested execution
    # against simulated actual execution.
    requested_quantity = models.PositiveIntegerField(
        default=0,
    )


    # ========================================================
    # 3.8 ACTUAL QUANTITY
    # ========================================================

    # Number of units actually filled during the simulated
    # transaction.
    quantity = models.PositiveIntegerField()


    # ========================================================
    # 3.9 PARTIAL FILL
    # ========================================================

    # True when the requested quantity could not be filled
    # completely by the execution simulation.
    partial_fill = models.BooleanField(
        default=False,
    )


    # ========================================================
    # 3.10 TRANSACTION COST
    # ========================================================

    # Stores simulated commission, transaction costs or other
    # execution costs associated with this trade.
    transaction_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )


    # ========================================================
    # 3.11 PROFIT / LOSS
    # ========================================================

    # Profit or loss produced by the trade.
    #
    # It can remain empty while a trade is still open.
    profit_loss = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )


    # ========================================================
    # 3.12 TRADE STATUS
    # ========================================================

    status = models.CharField(
        max_length=20,
        choices=[
            (
                "open",
                "Open",
            ),
            (
                "closed",
                "Closed",
            ),
        ],
        default="open",
    )


    # ========================================================
    # 3.13 STRING REPRESENTATION
    # ========================================================

    def __str__(self):
        """
        Used by Django Admin and debugging output.
        """

        return (
            f"{self.symbol} "
            f"Backtest Trade #{self.pk}"
        )


# ============================================================
# 4. STRATEGY / MODEL LIBRARY ITEM
# ============================================================

class StrategyLibraryItem(TimeStampedModel):
    """
    ============================================================
    MARKETPULSE - STRATEGY & MODEL LIBRARY
    ============================================================

    Framework mapping:

    StrategyLibraryItem
        ↓
    strategy_builder/library.py
        ↓
    Strategy Library page
        +
    Data tab model selector
        ↓
    User chooses a model
        ↓
    Future Model Runner
        ↓
    Backtesting / Forecasting / Simulation / Risk Results


    PURPOSE:

    This model stores the catalogue of quantitative strategies,
    financial models and analytical methods available inside
    MarketPulse.

    It stores metadata including:

    - Model name
    - Category
    - Purpose
    - Required market data
    - Default parameters
    - Expected output
    - Implementation status


    IMPORTANT:

    This model stores MODEL METADATA.

    It does NOT perform the actual mathematical calculations.

    The numerical implementations of models such as:

    - GBM
    - Ornstein-Uhlenbeck
    - Heston
    - ARIMA
    - GARCH
    - Random Forest
    - SVM
    - Black-Scholes
    - Monte Carlo

    will live in separate Python execution modules.

    ============================================================
    """


    # ========================================================
    # 4.1 MODEL CATEGORIES
    # ========================================================

    CATEGORY_CHOICES = [

        # ----------------------------------------------------
        # Stochastic Price Dynamics
        # ----------------------------------------------------

        (
            "stochastic",
            "1. Stochastic Models",
        ),


        # ----------------------------------------------------
        # Time-Series Forecasting
        # ----------------------------------------------------

        (
            "time_series",
            "2. Time-Series Models",
        ),


        # ----------------------------------------------------
        # Machine Learning
        # ----------------------------------------------------

        (
            "machine_learning",
            "3. Machine Learning Models",
        ),


        # ----------------------------------------------------
        # Academic / Investment Factors
        # ----------------------------------------------------

        (
            "factor",
            "4. Factor Models",
        ),


        # ----------------------------------------------------
        # Portfolio Construction
        # ----------------------------------------------------

        (
            "portfolio",
            "5. Portfolio Optimisation",
        ),


        # ----------------------------------------------------
        # Derivatives Valuation
        # ----------------------------------------------------

        (
            "derivatives",
            "6. Derivatives Pricing",
        ),


        # ----------------------------------------------------
        # Simulation
        # ----------------------------------------------------

        (
            "monte_carlo",
            "7. Simulation & Monte Carlo",
        ),

    ]


    # ========================================================
    # 4.2 IMPLEMENTATION STATUS OPTIONS
    # ========================================================

    IMPLEMENTATION_STATUS_CHOICES = [

        # ----------------------------------------------------
        # Model exists in catalogue only
        # ----------------------------------------------------

        (
            "catalogued",
            "Catalogued",
        ),


        # ----------------------------------------------------
        # Numerical implementation exists
        # ----------------------------------------------------

        (
            "ready",
            "Ready to Run",
        ),


        # ----------------------------------------------------
        # Numerical implementation exists but is still being
        # evaluated or developed
        # ----------------------------------------------------

        (
            "experimental",
            "Experimental",
        ),

    ]


    # ========================================================
    # 4.3 INTERNAL MODEL CODE
    # ========================================================

    # Unique internal identifier used by the future Model
    # Runner.
    #
    # Examples:
    #
    # gbm
    # arima
    # random_forest
    # black_scholes
    # monte_carlo_var_es
    code = models.SlugField(
        max_length=100,
        unique=True,
    )


    # ========================================================
    # 4.4 MODEL NAME
    # ========================================================

    # Human-readable name displayed in the interface.
    name = models.CharField(
        max_length=150,
    )


    # ========================================================
    # 4.5 MODEL CATEGORY
    # ========================================================

    # Groups models inside the Strategy Library and the
    # Data-tab selector.
    category = models.CharField(
        max_length=40,
        choices=CATEGORY_CHOICES,
    )


    # ========================================================
    # 4.6 DESCRIPTION
    # ========================================================

    # Short explanation of what the model does.
    description = models.TextField()


    # ========================================================
    # 4.7 PURPOSE
    # ========================================================

    # Explains why a user might select the model.
    purpose = models.TextField(
        blank=True,
    )


    # ========================================================
    # 4.8 DEFAULT PARAMETERS
    # ========================================================

    # Different quantitative models require different
    # numerical parameters.
    #
    # JSONField gives MarketPulse flexibility without
    # requiring separate database columns for every model.
    #
    # Example - GBM:
    #
    # {
    #     "horizon_days": 30,
    #     "simulations": 1000,
    #     "drift": 0.08,
    #     "volatility": 0.20
    # }
    #
    # Example - ARIMA:
    #
    # {
    #     "p": 1,
    #     "d": 1,
    #     "q": 1,
    #     "forecast_steps": 20
    # }
    default_parameters = models.JSONField(
        default=dict,
        blank=True,
    )


    # ========================================================
    # 4.9 DATA REQUIREMENTS
    # ========================================================

    # Describes which market-data inputs are needed.
    #
    # Example:
    #
    # [
    #     "close_price",
    #     "volume"
    # ]
    #
    # This will later allow the application to determine
    # whether an imported dataset is compatible with a
    # selected model.
    data_requirements = models.JSONField(
        default=list,
        blank=True,
    )


    # ========================================================
    # 4.10 EXPECTED OUTPUT
    # ========================================================

    # Examples:
    #
    # Simulated price paths
    # Forecast values
    # Conditional volatility
    # Portfolio weights
    # Option fair value
    # VaR and Expected Shortfall
    output_type = models.CharField(
        max_length=250,
        blank=True,
    )


    # ========================================================
    # 4.11 IMPLEMENTATION STATUS
    # ========================================================

    # Initially the library items are catalogued.
    #
    # When a numerical runner is implemented, the item's
    # status can be changed to "ready".
    implementation_status = models.CharField(
        max_length=20,
        choices=IMPLEMENTATION_STATUS_CHOICES,
        default="catalogued",
    )


    # ========================================================
    # 4.12 ACTIVE STATUS
    # ========================================================

    # Allows a model to be hidden from the interface without
    # deleting its database record.
    is_active = models.BooleanField(
        default=True,
    )


    # ========================================================
    # 4.13 DISPLAY ORDER
    # ========================================================

    # Controls model ordering inside each category.
    display_order = models.PositiveIntegerField(
        default=0,
    )


    # ========================================================
    # 4.14 DATABASE CONFIGURATION
    # ========================================================

    class Meta:

        # Models are grouped first by category and then by
        # their manually assigned display order.
        ordering = [
            "category",
            "display_order",
            "name",
        ]

        verbose_name = (
            "Strategy Library Item"
        )

        verbose_name_plural = (
            "Strategy Library Items"
        )


    # ========================================================
    # 4.15 STRING REPRESENTATION
    # ========================================================

    def __str__(self):
        """
        Makes each library item readable inside Django Admin,
        dropdowns and debugging output.
        """

        return (
            f"{self.name} "
            f"({self.get_category_display()})"
        )