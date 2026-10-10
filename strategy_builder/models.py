"""
MARKETPULSE - STRATEGY BUILDER MODELS

Purpose:
Define strategy rules, simulated backtest trades and model-library metadata.

Framework interaction:
Strategy -> StrategyRule -> backtesting engine.
Backtest -> BacktestTrade -> saved simulated trade results.
StrategyLibraryItem -> library and Data-tab model selector.

Strategy and Backtest are imported from core.models.
These models describe stored data; calculation engines perform analysis.
"""

# ============================================================
# 1. IMPORTS
# ============================================================
from django.db import models  # Import: I access Django's model fields and relationship tools.
from core.models import (  # Import grouping: I bring in existing core model classes.
    Backtest,  # Imported class: I use Backtest as the parent of simulated trades.
    Strategy,  # Imported class: I use Strategy as the parent of strategy rules.
    TimeStampedModel,  # Imported base class: I inherit its shared fields and behaviour.
)  # Closing parenthesis: I finish the grouped import.

# ============================================================
# 2. STRATEGY RULE MODEL
# ============================================================
class StrategyRule(TimeStampedModel):  # Class inheritance: I define a rule model using the shared base class.
    """Store one strategy rule, its condition, action and parameters."""

    # --------------------------------------------------------
    # 2.1 PARENT STRATEGY RELATIONSHIP
    # --------------------------------------------------------
    strategy = models.ForeignKey(  # Field assignment: I create a many-to-one relationship with Strategy.
        Strategy,  # Positional argument: I identify the related model.
        on_delete=models.CASCADE,  # Keyword argument: Django deletes related rules when their parent strategy is deleted.
        related_name="rules",  # Reverse relationship: I can retrieve rules with strategy.rules.all().
    )  # Closing parenthesis: I finish the relationship definition.

    # --------------------------------------------------------
    # 2.2 RULE NAME AND ASSET SYMBOL
    # --------------------------------------------------------
    name = models.CharField(  # Text field: I store a readable rule name.
        max_length=160,  # Integer argument: I limit the name to 160 characters.
    )  # Closing parenthesis: I finish the name field.
    symbol = models.CharField(  # Text field: I store the asset ticker used by this rule.
        max_length=20,  # Integer argument: I limit the symbol to 20 characters.
    )  # Closing parenthesis: I finish the symbol field.

    # --------------------------------------------------------
    # 2.3 CONDITION CHOICES
    # --------------------------------------------------------
    condition_type = models.CharField(  # Text field: I store the selected condition code.
        max_length=30,  # Integer argument: I limit the stored code to 30 characters.
        choices=[  # List: I define permitted choices for model validation and generated forms.
            (  # Tuple: I pair a stored value with a readable label.
                "ma_cross_up",  # String: I store this code for an upward moving-average crossover.
                "Fast MA crosses above Slow MA",  # String: I display this readable condition label.
            ),  # Closing tuple: I finish the upward-crossover choice.
            (  # Tuple: I begin the downward-crossover choice.
                "ma_cross_down",  # String: I store this code for a downward crossover.
                "Fast MA crosses below Slow MA",  # String: I display this readable condition label.
            ),  # Closing tuple: I finish the downward-crossover choice.
        ],  # Closing list: I finish the condition choices.
    )  # Closing parenthesis: I finish the condition field.

    # --------------------------------------------------------
    # 2.4 ACTION CHOICES
    # --------------------------------------------------------
    action = models.CharField(  # Text field: I store the rule's action code.
        max_length=10,  # Integer argument: I limit the action to 10 characters.
        choices=[  # List: I define the available action choices.
            (  # Tuple: I pair the buy code with its label.
                "buy",  # Stored value: I identify a buy action.
                "Buy",  # Display label: I show the readable action name.
            ),  # Closing tuple: I finish the buy choice.
            (  # Tuple: I pair the sell code with its label.
                "sell",  # Stored value: I identify a sell action.
                "Sell",  # Display label: I show the readable action name.
            ),  # Closing tuple: I finish the sell choice.
        ],  # Closing list: I finish the action choices.
    )  # Closing parenthesis: I finish the action field.

    # --------------------------------------------------------
    # 2.5 PARAMETERS AND ACTIVE STATUS
    # --------------------------------------------------------
    parameters = models.JSONField(  # JSON field: I store settings such as fast_period and slow_period.
        default=dict,  # Callable default: Django creates a fresh dictionary for each new instance.
    )  # Closing parenthesis: I finish the parameters field.
    is_active = models.BooleanField(  # Boolean field: I store whether the rule is enabled.
        default=True,  # Boolean default: New rules begin active.
    )  # Closing parenthesis: I finish the active-status field.

    # --------------------------------------------------------
    # 2.6 READABLE STRING REPRESENTATION
    # --------------------------------------------------------
    def __str__(self):  # Special method and parameter: I define the text representation of this instance.
        """Return a readable rule description."""
        return (  # Return statement: I provide the combined description.
            f"{self.name} - "  # Formatted string and attribute access: I insert the rule name.
            f"{self.symbol} - "  # Adjacent string concatenation: I append the symbol.
            f"{self.get_action_display()}"  # Method call: I append Django's readable action-choice label.
        )  # Closing parenthesis: I finish the returned string.

# ============================================================
# 3. BACKTEST TRADE MODEL
# ============================================================
class BacktestTrade(TimeStampedModel):  # Class inheritance: I define a simulated-trade model using the shared base.
    """Store one simulated trade belonging to a historical backtest."""

    # --------------------------------------------------------
    # 3.1 PARENT BACKTEST AND ASSET SYMBOL
    # --------------------------------------------------------
    backtest = models.ForeignKey(  # Relationship field: Many simulated trades can belong to one backtest.
        Backtest,  # Positional argument: I identify the parent model.
        on_delete=models.CASCADE,  # Deletion behaviour: Django deletes related trades when their backtest is deleted.
        related_name="trades",  # Reverse relationship: I can use backtest.trades.all().
    )  # Closing parenthesis: I finish the backtest relationship.
    symbol = models.CharField(  # Text field: I store the traded asset's symbol.
        max_length=20,  # Integer argument: I limit the symbol to 20 characters.
    )  # Closing parenthesis: I finish the symbol field.

    # --------------------------------------------------------
    # 3.2 ENTRY AND EXIT DATES
    # --------------------------------------------------------
    entry_date = models.DateField()  # Date field: I store when the simulated position opened.
    exit_date = models.DateField(  # Date field: I store when the position closed, if available.
        null=True,  # Database option: I permit a NULL value when no exit date exists.
        blank=True,  # Validation option: I permit an empty value in forms and model validation.
    )  # Closing parenthesis: I finish the exit-date field.

    # --------------------------------------------------------
    # 3.3 ENTRY AND EXIT PRICES
    # --------------------------------------------------------
    entry_price = models.DecimalField(  # Decimal field: I store the simulated entry price with fixed decimal precision.
        max_digits=14,  # Precision limit: I allow 14 total digits, including decimal digits.
        decimal_places=4,  # Decimal precision: I reserve four digits after the decimal point.
    )  # Closing parenthesis: I finish the entry-price field.
    exit_price = models.DecimalField(  # Decimal field: I store the exit price when available.
        max_digits=14,  # Precision limit: I allow 14 total digits.
        decimal_places=4,  # Decimal precision: I reserve four decimal places.
        null=True,  # Database option: An open trade can have no exit price.
        blank=True,  # Validation option: I allow the exit price to remain empty.
    )  # Closing parenthesis: I finish the exit-price field.

    # --------------------------------------------------------
    # 3.4 REQUESTED AND FILLED QUANTITIES
    # --------------------------------------------------------
    requested_quantity = models.PositiveIntegerField(  # Integer field: I store the requested number of units; zero is allowed.
        default=0,  # Integer default: I use zero when no requested quantity is supplied.
    )  # Closing parenthesis: I finish the requested-quantity field.
    quantity = models.PositiveIntegerField()  # Integer field: I store the simulated filled quantity; zero is allowed.
    partial_fill = models.BooleanField(  # Boolean field: I record whether execution was only partially filled.
        default=False,  # Boolean default: I begin with the partial-fill flag unset.
    )  # Closing parenthesis: I finish the partial-fill field.

    # --------------------------------------------------------
    # 3.5 TRANSACTION COST AND PROFIT OR LOSS
    # --------------------------------------------------------
    transaction_cost = models.DecimalField(  # Decimal field: I store simulated execution costs.
        max_digits=14,  # Precision limit: I allow 14 total digits.
        decimal_places=2,  # Decimal precision: I store two digits after the decimal point.
        default=0,  # Numeric default: I use zero when no cost is supplied.
    )  # Closing parenthesis: I finish the transaction-cost field.
    profit_loss = models.DecimalField(  # Decimal field: I store the trade's calculated profit or loss.
        max_digits=14,  # Precision limit: I allow 14 total digits.
        decimal_places=2,  # Decimal precision: I store two decimal places.
        null=True,  # Database option: I allow no result while the trade remains open.
        blank=True,  # Validation option: I permit an empty profit-or-loss value.
    )  # Closing parenthesis: I finish the profit-or-loss field.

    # --------------------------------------------------------
    # 3.6 TRADE STATUS
    # --------------------------------------------------------
    status = models.CharField(  # Text field: I store whether the simulated trade is open or closed.
        max_length=20,  # Integer argument: I limit the status code to 20 characters.
        choices=[  # List: I define the available status choices.
            (  # Tuple: I begin the open-status choice.
                "open",  # Stored value: I identify an open trade.
                "Open",  # Display label: I show the readable status.
            ),  # Closing tuple: I finish the open choice.
            (  # Tuple: I begin the closed-status choice.
                "closed",  # Stored value: I identify a closed trade.
                "Closed",  # Display label: I show the readable status.
            ),  # Closing tuple: I finish the closed choice.
        ],  # Closing list: I finish the status choices.
        default="open",  # String default: New trade records begin with open status.
    )  # Closing parenthesis: I finish the status field.

    # --------------------------------------------------------
    # 3.7 READABLE STRING REPRESENTATION
    # --------------------------------------------------------
    def __str__(self):  # Special method: I define a readable description of this trade instance.
        """Return the symbol and trade record identifier."""
        return (  # Return statement: I provide the trade description.
            f"{self.symbol} "  # Formatted string: I insert the asset symbol.
            f"Backtest Trade #{self.pk}"  # Attribute access: I append the record's primary key.
        )  # Closing parenthesis: I finish the returned string.

# ============================================================
# 4. STRATEGY AND MODEL LIBRARY
# ============================================================
class StrategyLibraryItem(TimeStampedModel):  # Class inheritance: I define a catalogue-entry model using the shared base.
    """Store model metadata, requirements and status, rather than calculations."""

    # --------------------------------------------------------
    # 4.1 MODEL CATEGORY CHOICES
    # --------------------------------------------------------
    CATEGORY_CHOICES = [  # Class attribute and list: I define reusable category value-label pairs.
        (  # Tuple: I begin the stochastic-model category.
            "stochastic",  # Stored code: I identify stochastic models.
            "1. Stochastic Models",  # Display label: I show the category's readable name.
        ),  # Closing tuple: I finish this category.
        (  # Tuple: I begin the time-series category.
            "time_series",  # Stored code: I identify time-series models.
            "2. Time-Series Models",  # Display label: I show the category name.
        ),  # Closing tuple: I finish this category.
        (  # Tuple: I begin the machine-learning category.
            "machine_learning",  # Stored code: I identify machine-learning models.
            "3. Machine Learning Models",  # Display label: I show the category name.
        ),  # Closing tuple: I finish this category.
        (  # Tuple: I begin the factor-model category.
            "factor",  # Stored code: I identify factor models.
            "4. Factor Models",  # Display label: I show the category name.
        ),  # Closing tuple: I finish this category.
        (  # Tuple: I begin the portfolio category.
            "portfolio",  # Stored code: I identify portfolio-optimisation models.
            "5. Portfolio Optimisation",  # Display label: I show the category name.
        ),  # Closing tuple: I finish this category.
        (  # Tuple: I begin the derivatives category.
            "derivatives",  # Stored code: I identify derivatives-pricing models.
            "6. Derivatives Pricing",  # Display label: I show the category name.
        ),  # Closing tuple: I finish this category.
        (  # Tuple: I begin the simulation category.
            "monte_carlo",  # Stored code: I identify simulation and Monte Carlo models.
            "7. Simulation & Monte Carlo",  # Display label: I show the category name.
        ),  # Closing tuple: I finish this category.
    ]  # Closing bracket: I finish the category-choice list.

    # --------------------------------------------------------
    # 4.2 IMPLEMENTATION STATUS CHOICES
    # --------------------------------------------------------
    IMPLEMENTATION_STATUS_CHOICES = [  # Class attribute: I define the available implementation-status labels.
        (  # Tuple: I begin the catalogue-only status.
            "catalogued",  # Stored code: I identify a catalogued entry.
            "Catalogued",  # Display label: I show the readable status.
        ),  # Closing tuple: I finish this status.
        (  # Tuple: I begin the ready status.
            "ready",  # Stored code: I identify an entry marked ready.
            "Ready to Run",  # Display label: I show the ready status; this label itself does not execute a model.
        ),  # Closing tuple: I finish this status.
        (  # Tuple: I begin the experimental status.
            "experimental",  # Stored code: I identify an entry marked experimental.
            "Experimental",  # Display label: I show the readable status.
        ),  # Closing tuple: I finish this status.
    ]  # Closing bracket: I finish the implementation-status choices.

    # --------------------------------------------------------
    # 4.3 INTERNAL CODE, NAME AND CATEGORY
    # --------------------------------------------------------
    code = models.SlugField(  # Slug field: I store a short identifier such as gbm or black_scholes.
        max_length=100,  # Integer argument: I limit the identifier to 100 characters.
        unique=True,  # Uniqueness option: I require each library entry to have a different code.
    )  # Closing parenthesis: I finish the code field.
    name = models.CharField(  # Text field: I store the model's readable name.
        max_length=150,  # Integer argument: I limit the name to 150 characters.
    )  # Closing parenthesis: I finish the name field.
    category = models.CharField(  # Text field: I store the model's category code.
        max_length=40,  # Integer argument: I limit the category code to 40 characters.
        choices=CATEGORY_CHOICES,  # Class-attribute reference: I reuse the category choices defined above.
    )  # Closing parenthesis: I finish the category field.

    # --------------------------------------------------------
    # 4.4 DESCRIPTION AND PURPOSE
    # --------------------------------------------------------
    description = models.TextField()  # Text field: I store a longer explanation of what the model does.
    purpose = models.TextField(  # Text field: I explain why a user might choose the model.
        blank=True,  # Validation option: I allow the purpose text to be empty.
    )  # Closing parenthesis: I finish the purpose field.

    # --------------------------------------------------------
    # 4.5 DEFAULT PARAMETERS AND DATA REQUIREMENTS
    # --------------------------------------------------------
    default_parameters = models.JSONField(  # JSON field: I store model-specific settings without separate columns for every parameter.
        default=dict,  # Callable default: I create a fresh dictionary for each new instance.
        blank=True,  # Validation option: I allow an empty parameter collection.
    )  # Closing parenthesis: I finish the default-parameters field.
    data_requirements = models.JSONField(  # JSON field: I store required inputs, such as close_price and volume.
        default=list,  # Callable default: I create a fresh list for each new instance.
        blank=True,  # Validation option: I allow an empty requirements collection.
    )  # Closing parenthesis: I finish the data-requirements field.

    # --------------------------------------------------------
    # 4.6 EXPECTED OUTPUT AND IMPLEMENTATION STATUS
    # --------------------------------------------------------
    output_type = models.CharField(  # Text field: I describe expected output, such as forecasts or portfolio weights.
        max_length=250,  # Integer argument: I limit the output description to 250 characters.
        blank=True,  # Validation option: I allow this description to be empty.
    )  # Closing parenthesis: I finish the output-type field.
    implementation_status = models.CharField(  # Text field: I store the model's declared implementation status.
        max_length=20,  # Integer argument: I limit the status code to 20 characters.
        choices=IMPLEMENTATION_STATUS_CHOICES,  # Class-attribute reference: I reuse the status choices defined above.
        default="catalogued",  # String default: New entries begin as catalogued.
    )  # Closing parenthesis: I finish the implementation-status field.

    # --------------------------------------------------------
    # 4.7 ACTIVE STATUS AND DISPLAY ORDER
    # --------------------------------------------------------
    is_active = models.BooleanField(  # Boolean field: I store whether the entry is active for application filtering.
        default=True,  # Boolean default: New entries begin active.
    )  # Closing parenthesis: I finish the active-status field.
    display_order = models.PositiveIntegerField(  # Integer field: I store a non-negative ordering value.
        default=0,  # Integer default: I use zero when no display order is supplied.
    )  # Closing parenthesis: I finish the display-order field.

    # --------------------------------------------------------
    # 4.8 MODEL METADATA AND DEFAULT ORDERING
    # --------------------------------------------------------
    class Meta:  # Nested class: I define configuration that Django applies to this model.
        ordering = [  # List assignment: I define the default database-query ordering.
            "category",  # First ordering field: I sort by the stored category code.
            "display_order",  # Second ordering field: I sort each category by its display-order value.
            "name",  # Third ordering field: I sort equal ordering values by model name.
        ]  # Closing bracket: I finish the ordering list.
        verbose_name = (  # Metadata assignment: I define the readable singular model name.
            "Strategy Library Item"  # String: I supply the singular label used by Django.
        )  # Closing parenthesis: I finish the singular-name assignment.
        verbose_name_plural = (  # Metadata assignment: I define the readable plural model name.
            "Strategy Library Items"  # String: I supply the plural label used by Django.
        )  # Closing parenthesis: I finish the plural-name assignment.

    # --------------------------------------------------------
    # 4.9 READABLE STRING REPRESENTATION
    # --------------------------------------------------------
    def __str__(self):  # Special method: I define the text representation of a library entry.
        """Return the model name and readable category label."""
        return (  # Return statement: I provide a readable library-entry description.
            f"{self.name} "  # Formatted string: I insert the model name.
            f"({self.get_category_display()})"  # Method call: I append Django's readable category-choice label.
        )  # Closing parenthesis: I finish the returned string.