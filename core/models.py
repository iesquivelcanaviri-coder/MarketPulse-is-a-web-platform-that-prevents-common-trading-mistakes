"""
============================================================
CORE - SHARED MODELS
============================================================

PURPOSE:

The core app contains the shared database models used across
MarketPulse.

These models provide the central data structures that connect
the different parts of the application.


FRAMEWORK MAPPING:

Alpaca
    ↓
data_management
    ↓
MarketData
    ↓
PostgreSQL
    ↓
Data / Strategies / Risk / Dashboard


STRATEGY WORKFLOW:

User
    ↓
Strategy
    ↓
StrategyRule
    ↓
Backtest
    ↓
Performance results


MARKET DATA WORKFLOW:

Alpaca Historical Market Data
    ↓
MarketData
    ↓
Historical OHLCV observations
    ↓
Market Condition
Backtesting
Strategy Robustness
Risk Calculations
Stress Testing


CONFIGURABLE ALERT WORKFLOW:

User
    ↓
Dashboard
    ↓
AlertRule
    ↓
MarketPulse monitors:
    Price / Volume / % Change / Volatility
    ↓
Rule condition becomes true
    ↓
Alert.create_or_update()
    ↓
Dashboard notification


ALERT EVENT WORKFLOW:

MarketPulse detects a condition
    ↓
Alert.create_or_update()
    ↓
Existing active alert updated
OR
New alert created
    ↓
Dashboard displays the alert
    ↓
User investigates the issue
    ↓
Alert.resolve()
    ↓
Alert remains stored for history


IMPORTANT DISTINCTION:

AlertRule
    Defines WHAT MarketPulse should monitor.

Alert
    Records WHAT happened or what requires attention.


IMPORTANT:

The old separate Analysis tab is no longer part of the
user-facing application.

analysis_tools remains an INTERNAL analytics layer used by:

Data
    → Market Condition

Strategies
    → Strategy Robustness

Risk
    → Stress Testing

============================================================
"""

# ============================================================
# 1. DJANGO IMPORTS
# Programming concept: modules and imports
# Django concept: ORM configuration and model field tools
# ============================================================

# settings is used so ForeignKey relationships point to
# Django's configured user model instead of hard-coding a
# particular User class.
from django.conf import settings  # Import: brings Django project settings into this Python module.

# Django's models module provides the field types and database
# model functionality used throughout this file.
from django.db import models  # Import: gives access to Model, fields, Q objects, indexes and constraints.

# timezone provides timezone-aware timestamps when alerts are
# resolved or triggered.
from django.utils import timezone  # Import: gives Django-aware current date/time handling.

# ============================================================
# 2. SHARED TIMESTAMP MODEL
# Programming concepts: class, inheritance and abstraction
# Django concept: abstract base model
# ============================================================

class TimeStampedModel(models.Model):  # Class + inheritance: this model inherits Django's Model behaviour.
    """
    Abstract base model used by other MarketPulse models.

    Models inheriting from this class automatically receive:

    created_at
        The date and time when the database record was created.

    updated_at
        The date and time when the database record was most
        recently changed.

    This model is abstract, so Django does not create a separate
    TimeStampedModel database table.
    """

    # --------------------------------------------------------
    # 2.1 CREATED TIMESTAMP
    # Programming concept: class attribute
    # Django concept: model field
    # --------------------------------------------------------

    created_at = models.DateTimeField(  # Attribute: defines a date/time database column inherited by child models.
        auto_now_add=True,  # Keyword argument: automatically stores the time when a record is first created.
    )  # Function call ends here.

    # --------------------------------------------------------
    # 2.2 UPDATED TIMESTAMP
    # --------------------------------------------------------

    updated_at = models.DateTimeField(  # Attribute: defines the last-updated date/time column.
        auto_now=True,  # Boolean value: Django automatically updates this timestamp whenever the object is saved.
    )  # Function call ends here.

    # --------------------------------------------------------
    # 2.3 MODEL METADATA
    # Programming concept: nested class
    # Django concept: Meta configuration
    # --------------------------------------------------------

    class Meta:  # Nested class: supplies configuration about the parent Django model.
        abstract = True  # Boolean: tells Django not to create a TimeStampedModel database table.

# ============================================================
# 3. MARKET DATA
# Programming concepts: inheritance, attributes and objects
# Django concept: database entity/model
# ============================================================

class MarketData(TimeStampedModel):  # Inheritance: MarketData receives created_at and updated_at automatically.
    """
    Stores historical OHLCV market observations.

    OHLCV means:

    Open
    High
    Low
    Close
    Volume

    MarketPulse stores historical observations in PostgreSQL
    rather than repeatedly requesting the same data from an
    external provider.

    This allows the same historical dataset to be reused for:

    - Data analysis
    - Market Condition analysis
    - Strategy backtesting
    - Strategy robustness testing
    - Risk calculations
    - Stress testing

    The external provider can therefore change without forcing
    every analytical feature to be rewritten.
    """

    # ========================================================
    # 3.1 ASSET IDENTIFIER
    # Programming concept: string data
    # ========================================================

    symbol = models.CharField(  # Attribute: stores a short text value such as SPY or AAPL.
        max_length=20,  # Integer argument: limits the stored string to 20 characters.
        db_index=True,  # Boolean argument: creates a database index to improve symbol searches.
    )  # Field definition ends here.

    # ========================================================
    # 3.2 OBSERVATION DATE
    # Programming concept: date data
    # ========================================================

    date = models.DateField(  # Attribute: stores the date represented by this market-data row.
        db_index=True,  # Database optimisation: creates an index for faster date queries.
    )  # Field definition ends here.

    # ========================================================
    # 3.3 OHLC PRICES
    # Programming concept: decimal numeric data
    # ========================================================

    open_price = models.DecimalField(  # DecimalField: stores the opening price accurately.
        max_digits=14,  # Integer: maximum total number of decimal digits.
        decimal_places=4,  # Integer: keeps four digits after the decimal point.
    )  # Field definition ends here.

    high_price = models.DecimalField(  # DecimalField: stores the highest price in the observation.
        max_digits=14,  # Field configuration: maximum total digits.
        decimal_places=4,  # Field configuration: four decimal places.
    )  # Field definition ends here.

    low_price = models.DecimalField(  # DecimalField: stores the lowest price in the observation.
        max_digits=14,  # Field configuration: maximum total digits.
        decimal_places=4,  # Field configuration: four decimal places.
    )  # Field definition ends here.

    close_price = models.DecimalField(  # DecimalField: stores the closing price.
        max_digits=14,  # Field configuration: maximum total digits.
        decimal_places=4,  # Field configuration: four decimal places.
    )  # Field definition ends here.

    # ========================================================
    # 3.4 TRADING VOLUME
    # Programming concept: integer data
    # ========================================================

    volume = models.BigIntegerField(  # BigIntegerField: stores potentially very large trading-volume values.
        default=0,  # Default value: new records use zero when no value is supplied.
    )  # Field definition ends here.

    # ========================================================
    # 3.5 DATABASE CONFIGURATION
    # Programming concepts: nested class, list and constraint
    # ========================================================

    class Meta:  # Nested configuration class used by Django's ORM.
        # ----------------------------------------------------
        # Prevent duplicate daily observations
        # ----------------------------------------------------

        # MarketPulse should only contain one historical record
        # for one symbol on one particular date.
        constraints = [  # List: contains database integrity constraints for this model.
            models.UniqueConstraint(  # Object construction: creates a uniqueness rule.
                fields=[  # List: identifies the fields that must be unique together.
                    "symbol",  # String: first field used by the unique constraint.
                    "date",  # String: second field used by the unique constraint.
                ],  # List ends here.
                name="unique_symbol_date",  # String: gives this database constraint a stable name.
            ),  # UniqueConstraint construction ends here.
        ]  # Constraint list ends here.

        # ----------------------------------------------------
        # Default ordering
        # ----------------------------------------------------

        # The newest market observations appear first unless a
        # particular query asks for another ordering.
        ordering = [  # List: specifies Django's default query ordering.
            "-date",  # String: minus sign means descending order by date.
        ]  # Ordering list ends here.

    # ========================================================
    # 3.6 STRING REPRESENTATION
    # Programming concepts: method, self and f-string
    # ========================================================

    def __str__(self):  # Special method: controls the readable text representation of a MarketData object.
        return (  # Return statement: sends the generated string back to the caller.
            f"{self.symbol} "  # F-string: inserts this object's symbol into text.
            f"{self.date}"  # F-string: inserts this object's date into text.
        )  # Returned expression ends here.

# ============================================================
# 4. STRATEGY
# Programming concepts: class, relationships and JSON data
# ============================================================

class Strategy(TimeStampedModel):  # Inheritance: Strategy also receives the shared timestamp fields.
    """
    Represents a strategy created by a MarketPulse user.

    Detailed StrategyRule objects belong to the
    strategy_builder app.

    This shared model stores the information needed by:

    - Strategy Builder
    - Backtesting
    - Dashboard
    - Strategy Robustness
    - Stress Testing
    """

    # ========================================================
    # 4.1 STRATEGY OWNER
    # Programming concept: object relationship
    # Django concept: ForeignKey / many-to-one relationship
    # ========================================================

    user = models.ForeignKey(  # ForeignKey: each Strategy belongs to one user.
        settings.AUTH_USER_MODEL,  # Configuration value: references MarketPulse's configured Django user model.
        on_delete=models.CASCADE,  # Relationship rule: deleting the user also deletes their strategies.
        related_name="strategies",  # Reverse relationship: user.strategies accesses the user's Strategy records.
    )  # ForeignKey definition ends here.

    # ========================================================
    # 4.2 STRATEGY INFORMATION
    # ========================================================

    name = models.CharField(  # String field: stores the strategy's name.
        max_length=120,  # Integer: allows a maximum of 120 characters.
    )  # Field definition ends here.

    description = models.TextField(  # Text field: stores a longer description.
        blank=True,  # Boolean: Django forms are allowed to leave this field empty.
    )  # Field definition ends here.

    # ========================================================
    # 4.3 STRATEGY STATUS
    # Programming concept: Boolean data
    # ========================================================

    is_active = models.BooleanField(  # Boolean field: represents an on/off strategy state.
        default=True,  # Default Boolean value: a new strategy begins active.
    )  # Field definition ends here.

    # ========================================================
    # 4.4 STRATEGY CONFIGURATION
    # Programming concepts: dictionary-like structured data
    # ========================================================

    # This field is deliberately named rule_config rather than
    # rules.
    #
    # StrategyRule already uses:
    #
    # strategy.rules.all()
    #
    # as its reverse relationship.
    #
    # Using rule_config avoids a Django related-name collision.
    rule_config = models.JSONField(  # JSONField: stores flexible structured configuration data.
        default=dict,  # Callable default: creates a new empty Python dictionary for each object.
    )  # Field definition ends here.

    # ========================================================
    # 4.5 DATABASE CONFIGURATION
    # ========================================================

    class Meta:  # Nested class: configures this Django model.
        ordering = [  # List: sets default sorting.
            "name",  # String: sorts Strategy objects alphabetically by name.
        ]  # Ordering list ends here.

    # ========================================================
    # 4.6 STRING REPRESENTATION
    # ========================================================

    def __str__(self):  # Special method: returns a readable Strategy representation.
        return self.name  # Return statement: uses the strategy name as its display text.

# ============================================================
# 5. BACKTEST
# Programming concepts: relationships, numeric types and object state
# ============================================================

class Backtest(TimeStampedModel):  # Inheritance: Backtest receives shared timestamp functionality.
    """
    Stores the result of testing a strategy against historical
    MarketData.

    Backtest results are saved in PostgreSQL instead of existing
    only temporarily in the browser.

    This allows MarketPulse to:

    - Preserve historical results
    - Compare different strategies
    - Calculate Dashboard statistics
    - Perform robustness checks
    - Support reproducible analysis
    """

    # ========================================================
    # 5.1 STRATEGY
    # ========================================================

    strategy = models.ForeignKey(  # ForeignKey: connects each Backtest to one Strategy object.
        Strategy,  # Class reference: Strategy is the related model.
        on_delete=models.CASCADE,  # Cascade rule: deleting the Strategy also deletes its Backtests.
        related_name="backtests",  # Reverse relation: strategy.backtests accesses related Backtest objects.
    )  # ForeignKey definition ends here.

    # ========================================================
    # 5.2 HISTORICAL DATASET
    # ========================================================

    symbol = models.CharField(  # String field: records which market symbol was tested.
        max_length=20,  # Maximum string length is 20 characters.
    )  # Field definition ends here.

    start_date = models.DateField()  # Date field: records the first date of the backtest period.

    end_date = models.DateField()  # Date field: records the final date of the backtest period.

    # ========================================================
    # 5.3 PORTFOLIO VALUES
    # ========================================================

    initial_capital = models.DecimalField(  # Decimal field: stores the starting portfolio capital.
        max_digits=14,  # Maximum total number of digits.
        decimal_places=2,  # Stores two digits after the decimal point.
        default=10000,  # Default numeric value: backtests start with 10,000 unless another value is supplied.
    )  # Field definition ends here.

    final_capital = models.DecimalField(  # Decimal field: stores capital remaining after the backtest.
        max_digits=14,  # Maximum total number of digits.
        decimal_places=2,  # Stores two digits after the decimal point.
        default=0,  # Default numeric value is zero.
    )  # Field definition ends here.

    # ========================================================
    # 5.4 PERFORMANCE MEASURES
    # ========================================================

    total_return = models.DecimalField(  # Decimal field: stores calculated total strategy return.
        max_digits=10,  # Maximum total digits.
        decimal_places=6,  # Six decimal places provide additional precision.
        default=0,  # Default numeric value.
    )  # Field definition ends here.

    max_drawdown = models.DecimalField(  # Decimal field: stores the maximum portfolio drawdown.
        max_digits=10,  # Maximum total digits.
        decimal_places=6,  # Six decimal places of precision.
        default=0,  # Default numeric value.
    )  # Field definition ends here.

    sharpe_ratio = models.DecimalField(  # Decimal field: stores the calculated Sharpe ratio.
        max_digits=10,  # Maximum total digits.
        decimal_places=6,  # Six decimal places of precision.
        default=0,  # Default numeric value.
    )  # Field definition ends here.

    win_rate = models.DecimalField(  # Decimal field: stores the proportion of successful trades.
        max_digits=10,  # Maximum total digits.
        decimal_places=6,  # Six decimal places of precision.
        default=0,  # Default numeric value.
    )  # Field definition ends here.

    # ========================================================
    # 5.5 TRADING STATISTICS
    # ========================================================

    total_trades = models.PositiveIntegerField(  # Positive integer: stores a non-negative trade count.
        default=0,  # Default number of trades.
    )  # Field definition ends here.

    transaction_costs = models.DecimalField(  # Decimal field: stores estimated or calculated trading costs.
        max_digits=14,  # Maximum total digits.
        decimal_places=2,  # Currency-style two decimal places.
        default=0,  # Default cost value.
    )  # Field definition ends here.

    # ========================================================
    # 5.6 ADDITIONAL CALCULATED OUTPUT
    # ========================================================

    results = models.JSONField(  # JSONField: stores additional calculated backtest information.
        default=dict,  # Callable default: creates a separate empty dictionary for each Backtest.
    )  # Field definition ends here.

    # ========================================================
    # 5.7 DATABASE CONFIGURATION
    # ========================================================

    class Meta:  # Nested class: configures Backtest database behaviour.
        # Most recently completed backtests appear first.
        ordering = [  # List: defines default sorting.
            "-created_at",  # Descending timestamp: newest Backtests appear first.
        ]  # Ordering list ends here.

    # ========================================================
    # 5.8 STRING REPRESENTATION
    # ========================================================

    def __str__(self):  # Special method: produces human-readable Backtest text.
        return (  # Return statement: sends a formatted string to the caller.
            f"{self.strategy.name}: "  # F-string: gets the name from the related Strategy object.
            f"{self.start_date} to {self.end_date}"  # F-string: inserts the tested date range.
        )  # Returned expression ends here.

# ============================================================
# 6. ALERT
# Programming concepts: constants, collections, methods,
# conditionals, decorators, properties and encapsulation
# ============================================================

class Alert(TimeStampedModel):  # Class + inheritance: Alert is a persistent Django model with timestamps.
    """
    Stores actionable MarketPulse notifications.

    Alerts answer the question:

        "Is there something the user should investigate?"

    An Alert represents an EVENT or NOTIFICATION.

    AlertRule, defined later in this file, represents the user's
    configurable monitoring condition.

    Examples:

    DATA
        Historical AAPL data has become stale.

    STRATEGY
        A strategy shows substantial performance deterioration
        during robustness testing.

    RISK
        A calculated position exceeds the intended risk budget.

    STRESS
        A strategy performs poorly under a severe simulated
        market scenario.

    MARKET CONDITION
        A significant change in market behaviour was detected.

    PRICE
        A configurable AlertRule price threshold was reached.

    SYSTEM
        Alpaca market information could not be retrieved.

    Active alerts appear on the main Dashboard.
    """

    # ========================================================
    # 6.1 ALERT TYPE CONSTANTS
    # Programming concept: class constants
    # ========================================================

    TYPE_PRICE = "price"  # Constant: reusable internal value representing price alerts.
    TYPE_DATA = "data"  # Constant: reusable internal value representing data alerts.
    TYPE_STRATEGY = "strategy"  # Constant: reusable internal value representing strategy alerts.
    TYPE_RISK = "risk"  # Constant: reusable internal value representing risk alerts.
    TYPE_STRESS = "stress"  # Constant: reusable internal value representing stress-test alerts.
    TYPE_REGIME = "regime"  # Constant: reusable internal value representing market-condition alerts.
    TYPE_SYSTEM = "system"  # Constant: reusable internal value representing system alerts.

    # ========================================================
    # 6.2 ALERT TYPE CHOICES
    # Programming concepts: list and tuple collections
    # ========================================================

    TYPES = [  # List: contains allowed alert-type choices.
        (  # Tuple: pairs a stored database value with a user-readable label.
            TYPE_PRICE,  # Constant: database value.
            "Price",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: second allowed alert type.
            TYPE_DATA,  # Constant: database value.
            "Data",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: strategy alert choice.
            TYPE_STRATEGY,  # Constant: database value.
            "Strategy",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: risk alert choice.
            TYPE_RISK,  # Constant: database value.
            "Risk",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: stress alert choice.
            TYPE_STRESS,  # Constant: database value.
            "Stress Test",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: market-condition alert choice.
            TYPE_REGIME,  # Constant: database value.
            "Market Condition",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: system alert choice.
            TYPE_SYSTEM,  # Constant: database value.
            "System",  # String: display label.
        ),  # Tuple ends here.
    ]  # Choice list ends here.

    # ========================================================
    # 6.2.1 BACKWARD-COMPATIBLE ALERT TYPE ALIAS
    # Programming concept: variable alias/reference
    # ========================================================

    # Some earlier MarketPulse views referred to the alert
    # choices using:
    #
    #     Alert.ALERT_TYPES
    #
    # The canonical collection in this model is TYPES.
    #
    # Keeping this alias prevents older code from failing while
    # allowing new code to use either:
    #
    #     Alert.TYPES
    #
    # or preferably:
    #
    #     Alert._meta.get_field("alert_type").choices
    #
    # No additional database field is created by this alias.
    ALERT_TYPES = TYPES  # Assignment: another class name points to the same choices collection.

    # ========================================================
    # 6.3 SEVERITY CONSTANTS
    # ========================================================

    SEVERITY_INFO = "info"  # Constant: information severity value.
    SEVERITY_SUCCESS = "success"  # Constant: success severity value.
    SEVERITY_WARNING = "warning"  # Constant: warning severity value.
    SEVERITY_DANGER = "danger"  # Constant: highest-priority severity value.

    # ========================================================
    # 6.4 SEVERITY CHOICES
    # ========================================================

    SEVERITIES = [  # List: allowed severity choices.
        (  # Tuple: stored value plus display value.
            SEVERITY_INFO,  # Constant: stored database value.
            "Information",  # String: user-facing label.
        ),  # Tuple ends here.
        (  # Tuple: success severity option.
            SEVERITY_SUCCESS,  # Constant: stored database value.
            "Success",  # String: user-facing label.
        ),  # Tuple ends here.
        (  # Tuple: warning severity option.
            SEVERITY_WARNING,  # Constant: stored database value.
            "Warning",  # String: user-facing label.
        ),  # Tuple ends here.
        (  # Tuple: danger severity option.
            SEVERITY_DANGER,  # Constant: stored database value.
            "High Priority",  # String: user-facing label.
        ),  # Tuple ends here.
    ]  # Choice list ends here.

    # ========================================================
    # 6.5 USER
    # Programming concept: object relationship
    # ========================================================

    user = models.ForeignKey(  # ForeignKey: each Alert belongs to one MarketPulse user.
        settings.AUTH_USER_MODEL,  # Uses the configured user class instead of hard-coding User.
        on_delete=models.CASCADE,  # Cascade relationship: deleting the user deletes their alerts.
        related_name="alerts",  # Reverse accessor: user.alerts gives that user's alerts.
    )  # ForeignKey definition ends here.

    # ========================================================
    # 6.6 ALERT CLASSIFICATION
    # ========================================================

    alert_type = models.CharField(  # String field: stores the category of alert.
        max_length=20,  # Maximum stored string length.
        choices=TYPES,  # Restricts values to entries defined in TYPES.
    )  # Field definition ends here.

    severity = models.CharField(  # String field: stores alert severity.
        max_length=20,  # Maximum stored string length.
        choices=SEVERITIES,  # Restricts values to the severity choice collection.
        default=SEVERITY_INFO,  # Default value: new alerts start as informational.
    )  # Field definition ends here.

    # ========================================================
    # 6.7 ALERT CONTENT
    # ========================================================

    title = models.CharField(  # String field: stores the short alert heading.
        max_length=200,  # Maximum title length.
    )  # Field definition ends here.

    message = models.TextField()  # Text field: stores the longer alert explanation.

    # ========================================================
    # 6.8 ALERT KEY
    # Programming concept: identifier
    # ========================================================

    # alert_key gives one particular alert condition a stable
    # identifier.
    #
    # Examples:
    #
    # DATA_STALE_AAPL
    #
    # HIGH_VOLATILITY_SPY
    #
    # STRATEGY_ROBUSTNESS_12
    #
    # STRESS_FAILURE_7
    #
    # ALPACA_CONNECTION
    #
    # ALERT_RULE_15
    #
    # This prevents the Dashboard from creating another copy of
    # the same active warning every time the page is refreshed.
    alert_key = models.CharField(  # String field: stores a stable programmatic identifier for the condition.
        max_length=160,  # Maximum key length.
        blank=True,  # Form validation allows this field to be empty.
        db_index=True,  # Database index improves searches for a particular alert key.
    )  # Field definition ends here.

    # ========================================================
    # 6.9 ACTION LINK
    # ========================================================

    # action_url allows an alert to direct the user to the part
    # of MarketPulse where the problem can be investigated.
    action_url = models.CharField(  # String field: stores an internal destination URL.
        max_length=500,  # Maximum URL text length.
        blank=True,  # The destination is optional.
    )  # Field definition ends here.

    # ========================================================
    # 6.10 STRUCTURED METADATA
    # ========================================================

    # Optional JSON metadata can preserve values related to the
    # detected condition without requiring a new database field
    # for every possible alert type.
    metadata = models.JSONField(  # JSONField: holds flexible key/value metadata.
        default=dict,  # Callable default: supplies a new empty dictionary.
        blank=True,  # Form-level validation permits empty metadata.
    )  # Field definition ends here.

    # ========================================================
    # 6.11 ALERT STATE
    # Programming concept: Boolean state
    # ========================================================

    # is_read indicates whether the user has already seen or
    # acknowledged the notification.
    is_read = models.BooleanField(  # Boolean field: records whether the notification has been viewed.
        default=False,  # Default Boolean state: new alerts are unread.
    )  # Field definition ends here.

    # is_active indicates whether the underlying condition still
    # requires attention.
    #
    # An alert can be read while remaining active.
    is_active = models.BooleanField(  # Boolean field: records whether the condition is still active.
        default=True,  # Default state: a new alert requires attention.
    )  # Field definition ends here.

    # resolved_at stores when the underlying condition stopped
    # requiring attention.
    resolved_at = models.DateTimeField(  # Date/time field: stores when the alert became resolved.
        null=True,  # Database concept: SQL NULL is allowed.
        blank=True,  # Form concept: the value may be left empty.
    )  # Field definition ends here.

    # ========================================================
    # 6.12 DATABASE CONFIGURATION
    # Programming concepts: list, Boolean expression and objects
    # ========================================================

    class Meta:  # Nested class: configures Alert query/database behaviour.
        # Newer alerts appear first by default.
        ordering = [  # List: default model ordering.
            "-created_at",  # Descending order: newest alerts first.
        ]  # Ordering list ends here.

        constraints = [  # List: database integrity rules.
            # ------------------------------------------------
            # UNIQUE ACTIVE ALERT
            # ------------------------------------------------
            #
            # One user should not have multiple active alerts
            # representing exactly the same condition.
            models.UniqueConstraint(  # Database constraint: prevents specific duplicate active alerts.
                fields=[  # List: fields whose combination must be unique.
                    "user",  # String: user field participates in uniqueness.
                    "alert_key",  # String: alert key participates in uniqueness.
                ],  # Field list ends here.
                condition=(  # Conditional constraint: uniqueness only applies when this expression is true.
                    models.Q(  # Q object: creates a Django query-condition object.
                        is_active=True,  # Boolean comparison: alert must currently be active.
                    )  # First Q expression ends here.
                    &  # Boolean AND operator: both conditions must be true.
                    ~models.Q(  # Bitwise NOT is overloaded by Django to negate this Q condition.
                        alert_key="",  # Comparison: matches an empty alert key.
                    )  # Second Q expression ends here.
                ),  # Combined condition ends here.
                name=(  # Keyword argument: names the database constraint.
                    "unique_active_alert_key_per_user"  # String: stable database constraint name.
                ),  # Name expression ends here.
            ),  # UniqueConstraint ends here.
        ]  # Constraints list ends here.

    # ========================================================
    # 6.13 STRING REPRESENTATION
    # ========================================================

    def __str__(self):  # Special method: returns human-readable text for an Alert object.
        return (  # Return statement begins.
            f"{self.get_severity_display()}: "  # Method call: converts stored severity to its display label.
            f"{self.title}"  # F-string: adds this alert's title.
        )  # Returned string expression ends here.

    # ========================================================
    # 6.14 CREATE OR UPDATE ACTIVE ALERT
    # Programming concepts: decorator, class method, parameters,
    # conditional, exception, tuple unpacking and return values
    # ========================================================

    @classmethod  # Decorator: changes this function into a method that receives the class rather than an instance.
    def create_or_update(  # Method definition: encapsulates reusable alert creation/update behaviour.
        cls,  # Parameter: refers to the Alert class itself.
        *,  # Python syntax: all following parameters must be supplied by keyword.
        user,  # Parameter: identifies the alert owner.
        alert_key,  # Parameter: stable identifier used to avoid duplicate active alerts.
        alert_type,  # Parameter: category of alert.
        severity,  # Parameter: importance of alert.
        title,  # Parameter: short alert heading.
        message,  # Parameter: detailed alert message.
        action_url="",  # Default parameter: action URL becomes an empty string when omitted.
        metadata=None,  # Default parameter: no metadata supplied is represented by None.
    ):  # Method signature ends here.
        """
        Create one active alert or update the existing active
        alert representing the same condition.

        Automatic checks may run repeatedly.

        Instead of creating duplicate alerts:

            Condition detected
                ↓
            Existing active alert?
                ↓
            YES → update it
            NO  → create it
        """

        # A meaningful key is required because duplicate
        # prevention depends on it.
        if not alert_key:  # Conditional: runs only when alert_key is empty or otherwise false-like.
            raise ValueError(  # Exception: stops execution because the method cannot safely continue.
                "alert_key is required when creating "  # String literal: first part of the error message.
                "a managed MarketPulse alert."  # Adjacent string literal: Python joins this automatically.
            )  # Exception construction ends here.

        # Ensure metadata is always stored as a dictionary.
        if metadata is None:  # Conditional: checks explicitly whether no metadata object was supplied.
            metadata = {}  # Dictionary literal: replaces None with an empty dictionary.

        alert, created = (  # Tuple unpacking: receives two returned values into two variables.
            cls.objects.update_or_create(  # ORM method: updates a matching row or creates a new one.
                user=user,  # Keyword argument: query for this user.
                alert_key=alert_key,  # Keyword argument: query for this stable alert key.
                is_active=True,  # Keyword argument: only match a currently active alert.
                defaults={  # Dictionary: values to write when updating or creating the object.
                    "alert_type":  # Dictionary key: database field name.
                        alert_type,  # Dictionary value: alert type supplied to the method.
                    "severity":  # Dictionary key: database field name.
                        severity,  # Dictionary value: supplied severity.
                    "title":  # Dictionary key: database field name.
                        title,  # Dictionary value: supplied title.
                    "message":  # Dictionary key: database field name.
                        message,  # Dictionary value: supplied message.
                    "action_url":  # Dictionary key: database field name.
                        action_url,  # Dictionary value: supplied URL.
                    "metadata":  # Dictionary key: database field name.
                        metadata,  # Dictionary value: structured metadata dictionary.
                    "resolved_at":  # Dictionary key: database field name.
                        None,  # None: ensures an active managed alert is not marked resolved.
                },  # Defaults dictionary ends here.
            )  # ORM update_or_create() call ends here.
        )  # Tuple-unpacking expression ends here.

        return (  # Return statement: sends two pieces of information to the caller.
            alert,  # First tuple value: the Alert object.
            created,  # Second tuple value: Boolean saying whether Django created a new row.
        )  # Returned tuple ends here.

    # ========================================================
    # 6.15 RESOLVE ALERT BY KEY
    # Programming concepts: class method, local variable and
    # method chaining
    # ========================================================

    @classmethod  # Decorator: method operates through the Alert class.
    def resolve_by_key(  # Method definition: resolves an alert using its stable key.
        cls,  # Parameter: the class itself.
        *,  # Python syntax: following arguments are keyword-only.
        user,  # Parameter: identifies which user's alert should be changed.
        alert_key,  # Parameter: identifies the alert condition.
    ):  # Method signature ends here.
        """
        Resolve an active alert using its stable alert key.

        The record remains in PostgreSQL as historical evidence.
        """

        now = (  # Assignment: stores a timestamp in a local variable.
            timezone.now()  # Function call: gets the current timezone-aware date and time.
        )  # Assignment expression ends here.

        return (  # Return statement: returns the number of database rows Django updates.
            cls.objects  # ORM manager: starting point for querying Alert records.
            .filter(  # Method chaining: limits the queryset to matching alerts.
                user=user,  # Filter condition: correct user.
                alert_key=alert_key,  # Filter condition: correct stable key.
                is_active=True,  # Filter condition: alert must currently be active.
            )  # filter() call ends here.
            .update(  # ORM update: modifies matching rows directly in the database.
                is_active=False,  # Boolean update: marks the alert inactive.
                resolved_at=now,  # Timestamp update: records when resolution happened.
                updated_at=now,  # Timestamp update: also updates the shared modified time.
            )  # update() call ends here.
        )  # Returned expression ends here.

    # ========================================================
    # 6.16 MARK ALERT AS READ
    # Programming concepts: instance method and conditional
    # ========================================================

    def mark_as_read(self):  # Instance method: operates on one particular Alert object.
        """
        Mark the alert as having been seen by the user.

        This does not resolve the underlying condition.
        """

        if not self.is_read:  # Conditional: avoids writing to the database if the alert is already read.
            self.is_read = True  # Assignment: changes this object's Boolean state.
            self.save(  # Method call: persists the modified model object to the database.
                update_fields=[  # List: tells Django exactly which fields need updating.
                    "is_read",  # String: save the changed read state.
                    "updated_at",  # String: also save the automatically updated timestamp.
                ]  # List ends here.
            )  # save() call ends here.

    # ========================================================
    # 6.17 RESOLVE ONE ALERT
    # ========================================================

    def resolve(self):  # Instance method: resolves the current Alert object.
        """
        Resolve this particular alert.

        The record remains in PostgreSQL so MarketPulse
        preserves alert history instead of deleting it.
        """

        if self.is_active:  # Conditional: only performs work when the alert is currently active.
            self.is_active = False  # Assignment: changes active state to false.
            self.resolved_at = (  # Assignment: stores the resolution timestamp.
                timezone.now()  # Function call: obtains current timezone-aware time.
            )  # Assignment expression ends here.
            self.save(  # ORM persistence: writes modified instance fields to the database.
                update_fields=[  # List: restricts the database update to these fields.
                    "is_active",  # String: save changed active state.
                    "resolved_at",  # String: save resolution timestamp.
                    "updated_at",  # String: save modified timestamp.
                ]  # List ends here.
            )  # save() call ends here.

    # ========================================================
    # 6.18 REOPEN ALERT
    # Programming concepts: mutation / object state
    # ========================================================

    def reopen(self):  # Instance method: changes one Alert object back to an active state.
        """
        Reopen this alert record if the same condition becomes
        relevant again.
        """

        self.is_active = True  # Assignment: condition again requires attention.
        self.is_read = False  # Assignment: reopened notification becomes unread.
        self.resolved_at = None  # Assignment: removes its previous resolution timestamp.
        self.save(  # ORM persistence: writes the reopened state to the database.
            update_fields=[  # List: identifies the fields Django should update.
                "is_active",  # String: save active state.
                "is_read",  # String: save unread state.
                "resolved_at",  # String: save cleared resolution value.
                "updated_at",  # String: save updated timestamp.
            ]  # List ends here.
        )  # save() call ends here.

    # ========================================================
    # 6.19 RESOLUTION STATUS
    # Programming concepts: decorator, property, Boolean NOT
    # ========================================================

    @property  # Decorator: lets callers use alert.is_resolved instead of alert.is_resolved().
    def is_resolved(self):  # Property method: calculates a value from existing object state.
        """
        Return True when the alert is no longer active.
        """

        return (  # Return statement: produces a Boolean result.
            not self.is_active  # Boolean NOT: reverses the is_active value.
        )  # Returned expression ends here.

    # ========================================================
    # 6.20 BOOTSTRAP DISPLAY CLASS
    # Programming concepts: property and dictionary lookup
    # ========================================================

    @property  # Decorator: exposes this calculated method like an ordinary attribute.
    def bootstrap_class(self):  # Property method: converts severity into a Bootstrap CSS class name.
        """
        Return a Bootstrap-compatible severity class.
        """

        mapping = {  # Dictionary: maps internal severity constants to CSS-compatible text.
            self.SEVERITY_INFO:  # Dictionary key: informational severity constant.
                "info",  # Dictionary value: Bootstrap class suffix.
            self.SEVERITY_SUCCESS:  # Dictionary key: success severity constant.
                "success",  # Dictionary value: Bootstrap class suffix.
            self.SEVERITY_WARNING:  # Dictionary key: warning severity constant.
                "warning",  # Dictionary value: Bootstrap class suffix.
            self.SEVERITY_DANGER:  # Dictionary key: danger severity constant.
                "danger",  # Dictionary value: Bootstrap class suffix.
        }  # Dictionary ends here.

        return (  # Return statement begins.
            mapping.get(  # Dictionary method: safely looks up the current severity.
                self.severity,  # Lookup key: this Alert object's stored severity.
                "secondary",  # Default value: used if severity is not found in the dictionary.
            )  # get() call ends here.
        )  # Returned expression ends here.

    # ========================================================
    # 6.21 HAS ACTION
    # Programming concepts: type conversion and property
    # ========================================================

    @property  # Decorator: makes this calculated Boolean available as alert.has_action.
    def has_action(self):  # Property method: checks whether an action destination exists.
        """
        Return True when the alert contains a destination that
        the Dashboard can send the user to.
        """

        return bool(  # Type conversion: converts action_url to True or False.
            self.action_url  # Attribute: an empty string is False; a populated URL is True.
        )  # bool() call ends here.

# ============================================================
# 7. ALERT RULE
# Programming concepts: constants, state, operators, overriding,
# properties and string manipulation
# ============================================================

class AlertRule(TimeStampedModel):  # Class + inheritance: represents a persistent user-configured monitoring rule.
    """
    ============================================================
    MARKETPULSE - CONFIGURABLE ALERT RULE
    ============================================================

    PURPOSE:

    AlertRule stores a market condition configured by a user.

    It answers:

        "What should MarketPulse monitor for me?"


    EXAMPLES:

    PRICE ABOVE:

        Symbol:
            AAPL

        Metric:
            Price

        Operator:
            Greater Than

        Threshold:
            260


    PRICE BELOW:

        SPY
        Price
        Less Than
        730


    VOLUME:

        QQQ
        Volume
        Greater Than
        100000000


    PERCENTAGE MOVE:

        IWM
        Percent Change
        Less Than
        -3


    VOLATILITY:

        SPY
        Volatility
        Greater Than
        25


    WORKFLOW:

    Dashboard
        ↓
    User creates AlertRule
        ↓
    PostgreSQL
        ↓
    MarketPulse evaluates market information
        ↓
    Condition TRUE?
        ↓
    Alert.create_or_update()
        ↓
    Dashboard notification


    IMPORTANT:

    AlertRule and Alert are intentionally separate.

    AlertRule
        = user configuration

    Alert
        = generated event / notification
    ============================================================
    """

    # ========================================================
    # 7.1 METRIC CONSTANTS
    # Programming concept: named constants
    # ========================================================

    METRIC_PRICE = "price"  # Constant: internal value representing a price metric.
    METRIC_VOLUME = "volume"  # Constant: internal value representing volume.
    METRIC_PERCENT_CHANGE = "percent_change"  # Constant: internal value representing percentage movement.
    METRIC_VOLATILITY = "volatility"  # Constant: internal value representing volatility.

    # ========================================================
    # 7.2 METRIC CHOICES
    # Programming concepts: lists and tuples
    # ========================================================

    METRICS = [  # List: collection of metrics a user is allowed to monitor.
        (  # Tuple: database value plus readable label.
            METRIC_PRICE,  # Constant: stored value.
            "Price",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: volume metric choice.
            METRIC_VOLUME,  # Constant: stored value.
            "Volume",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: percentage-change metric choice.
            METRIC_PERCENT_CHANGE,  # Constant: stored value.
            "Percent Change",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: volatility metric choice.
            METRIC_VOLATILITY,  # Constant: stored value.
            "Volatility",  # String: display label.
        ),  # Tuple ends here.
    ]  # Choice list ends here.

    # ========================================================
    # 7.3 OPERATOR CONSTANTS
    # Programming concept: comparison operators represented as data
    # ========================================================

    OPERATOR_GREATER_THAN = "gt"  # Constant: means greater than.
    OPERATOR_GREATER_EQUAL = "gte"  # Constant: means greater than or equal.
    OPERATOR_LESS_THAN = "lt"  # Constant: means less than.
    OPERATOR_LESS_EQUAL = "lte"  # Constant: means less than or equal.

    # ========================================================
    # 7.4 OPERATOR CHOICES
    # ========================================================

    OPERATORS = [  # List: allowed comparison operations.
        (  # Tuple: stored operator code plus readable text.
            OPERATOR_GREATER_THAN,  # Constant: gt database value.
            "Greater Than",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: greater-than-or-equal option.
            OPERATOR_GREATER_EQUAL,  # Constant: gte database value.
            "Greater Than or Equal",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: less-than option.
            OPERATOR_LESS_THAN,  # Constant: lt database value.
            "Less Than",  # String: display label.
        ),  # Tuple ends here.
        (  # Tuple: less-than-or-equal option.
            OPERATOR_LESS_EQUAL,  # Constant: lte database value.
            "Less Than or Equal",  # String: display label.
        ),  # Tuple ends here.
    ]  # Choice list ends here.

    # ========================================================
    # 7.5 USER
    # Programming concept: association between objects
    # ========================================================

    # Every rule belongs to exactly one authenticated
    # MarketPulse user.
    user = models.ForeignKey(  # ForeignKey: establishes a many-rules-to-one-user relationship.
        settings.AUTH_USER_MODEL,  # References the application's configured user model.
        on_delete=models.CASCADE,  # Deleting a user also deletes their monitoring rules.
        related_name="marketpulse_alert_rules",  # Reverse accessor: user.marketpulse_alert_rules.
    )  # ForeignKey definition ends here.

    # ========================================================
    # 7.6 MARKET SYMBOL
    # Programming concept: string input
    # ========================================================

    # Examples:
    #
    # AAPL
    # MSFT
    # SPY
    # QQQ
    # DIA
    # IWM
    symbol = models.CharField(  # String field: stores the market ticker being monitored.
        max_length=20,  # Maximum ticker text length.
        db_index=True,  # Database optimisation: creates an index for symbol queries.
        help_text=(  # Keyword argument: documentation Django can display in forms/admin.
            "US equity or ETF symbol monitored by this rule."  # String: help message.
        ),  # help_text expression ends here.
    )  # Field definition ends here.

    # ========================================================
    # 7.7 METRIC
    # ========================================================

    # Defines which market quantity is monitored.
    metric = models.CharField(  # String field: stores the selected metric identifier.
        max_length=30,  # Maximum stored metric string length.
        choices=METRICS,  # Restriction: accepts values from the METRICS choices collection.
        default=METRIC_PRICE,  # Default constant: new rules monitor price unless changed.
    )  # Field definition ends here.

    # ========================================================
    # 7.8 COMPARISON OPERATOR
    # Programming concept: representing program logic as stored data
    # ========================================================

    # Examples:
    #
    # gt
    #     Price > threshold
    #
    # gte
    #     Price >= threshold
    #
    # lt
    #     Price < threshold
    #
    # lte
    #     Price <= threshold
    operator = models.CharField(  # String field: stores which comparison should be performed.
        max_length=10,  # Maximum operator-code length.
        choices=OPERATORS,  # Restricts this field to the defined comparison choices.
        default=OPERATOR_GREATER_THAN,  # Default constant: uses greater-than comparison.
    )  # Field definition ends here.

    # ========================================================
    # 7.9 THRESHOLD
    # Programming concept: decimal numeric data
    # ========================================================

    # DecimalField is used rather than FloatField because some
    # alert thresholds represent financial values.
    threshold = models.DecimalField(  # Decimal field: stores the number used in the comparison.
        max_digits=20,  # Maximum total number of digits.
        decimal_places=6,  # Six digits are preserved after the decimal point.
        help_text=(  # Django metadata: explanatory text for forms/admin.
            "Numeric threshold used when evaluating the rule."  # String: explains this field to the user.
        ),  # help_text expression ends here.
    )  # Field definition ends here.

    # ========================================================
    # 7.10 OPTIONAL USER MESSAGE
    # ========================================================

    # Example:
    #
    # "AAPL has broken above my target level."
    message = models.CharField(  # String field: optional custom notification text.
        max_length=255,  # Maximum message length.
        blank=True,  # Boolean: the user is allowed to leave this empty.
        help_text=(  # Django field metadata shown in forms/admin.
            "Optional explanation displayed when the rule "  # First adjacent string literal.
            "creates an alert."  # Second string literal; Python joins them automatically.
        ),  # help_text expression ends here.
    )  # Field definition ends here.

    # ========================================================
    # 7.11 ENABLE / DISABLE
    # Programming concept: Boolean state
    # ========================================================

    # A disabled rule remains stored but MarketPulse should not
    # evaluate it until the user enables it again.
    is_enabled = models.BooleanField(  # Boolean field: represents whether monitoring is switched on.
        default=True,  # Default state: new rules are enabled.
        db_index=True,  # Database index: helps efficiently find enabled rules.
    )  # Field definition ends here.

    # ========================================================
    # 7.12 COOLDOWN
    # Programming concept: integer state controlling behaviour
    # ========================================================

    # Prevent repeated alerts from being generated every time
    # the market-data refresh runs while a condition remains
    # true.
    #
    # Example:
    #
    # cooldown_minutes = 60
    #
    # means the rule cannot generate another notification for
    # at least one hour after being triggered.
    cooldown_minutes = models.PositiveIntegerField(  # Positive integer: stores a non-negative waiting period.
        default=60,  # Default integer: one-hour cooldown.
        help_text=(  # Django metadata: explains the field.
            "Minimum number of minutes before this rule may "  # First adjacent string literal.
            "trigger another alert."  # Second adjacent string literal.
        ),  # help_text expression ends here.
    )  # Field definition ends here.

    # ========================================================
    # 7.13 LAST TRIGGERED TIME
    # Programming concept: optional value / None
    # ========================================================

    # This is nullable because a newly created rule may never
    # have triggered.
    last_triggered_at = models.DateTimeField(  # Date/time field: records the most recent trigger time.
        null=True,  # Database rule: allows SQL NULL when no trigger has happened.
        blank=True,  # Form rule: allows this value to be empty.
    )  # Field definition ends here.

    # ========================================================
    # 7.14 DATABASE CONFIGURATION
    # Programming concepts: nested class, lists and indexing
    # ========================================================

    class Meta:  # Nested configuration class for AlertRule.
        # Enabled rules appear first.
        #
        # Rules are then grouped by symbol and metric.
        ordering = [  # List: controls default query ordering.
            "-is_enabled",  # Descending Boolean order: enabled rules appear before disabled rules.
            "symbol",  # Ascending string order: group rules alphabetically by ticker.
            "metric",  # Ascending string order: group by metric.
            "-created_at",  # Descending timestamp order: newest rules first within those groups.
        ]  # Ordering list ends here.

        # This index makes common rule-monitoring queries more
        # efficient:
        #
        # AlertRule.objects.filter(
        #     user=user,
        #     symbol="SPY",
        #     is_enabled=True,
        # )
        indexes = [  # List: defines additional database indexes.
            models.Index(  # Index object: helps PostgreSQL find commonly filtered rows faster.
                fields=[  # List: columns included in the compound index.
                    "user",  # String: first indexed model field.
                    "symbol",  # String: second indexed model field.
                    "is_enabled",  # String: third indexed model field.
                ],  # Field list ends here.
            ),  # Index construction ends here.
        ]  # Index list ends here.

    # ========================================================
    # 7.15 NORMALISE SYMBOL BEFORE SAVING
    # Programming concepts: method overriding, parameters,
    # string conversion, method chaining and super()
    # ========================================================

    def save(  # Method overriding: replaces/extends Django Model.save() for this class.
        self,  # Instance parameter: the AlertRule object being saved.
        *args,  # *args: collects additional positional arguments into a tuple.
        **kwargs,  # **kwargs: collects additional keyword arguments into a dictionary.
    ):  # Method signature ends here.
        """
        Store symbols consistently in uppercase.

        Examples:

            aapl
                ↓
            AAPL

            spy
                ↓
            SPY

        This avoids separate database records being treated as
        different assets merely because of letter casing.
        """

        self.symbol = (  # Assignment: replaces the object's symbol with a normalised version.
            str(  # Type conversion: guarantees the value is handled as a Python string.
                self.symbol  # Attribute access: current symbol value.
                or  # Boolean OR: if self.symbol is false-like, use the next value.
                ""  # Empty string: safe fallback when there is no symbol.
            )  # str() conversion ends here.
            .strip()  # String method: removes spaces from the beginning and end.
            .upper()  # String method: converts letters to uppercase.
        )  # Assignment expression ends here.

        super().save(  # Inheritance: calls the parent Django save() implementation after normalisation.
            *args,  # Argument unpacking: passes original positional arguments to the parent method.
            **kwargs,  # Keyword unpacking: passes original keyword arguments to the parent method.
        )  # Parent save() call ends here.

    # ========================================================
    # 7.16 OPERATOR SYMBOL
    # Programming concepts: property, dictionary and lookup
    # ========================================================

    @property  # Decorator: lets templates/code access rule.operator_symbol as an attribute.
    def operator_symbol(self):  # Property method: converts stored operator codes into mathematical symbols.
        """
        Convert the database-friendly operator into a
        user-friendly mathematical symbol.

        Examples:

            gt
                ↓
            >

            gte
                ↓
            ≥
        """

        symbols = {  # Dictionary: maps operator constants to readable symbols.
            self.OPERATOR_GREATER_THAN:  # Dictionary key: greater-than constant.
                ">",  # Dictionary value: greater-than symbol.
            self.OPERATOR_GREATER_EQUAL:  # Dictionary key: greater-or-equal constant.
                "≥",  # Dictionary value: greater-than-or-equal symbol.
            self.OPERATOR_LESS_THAN:  # Dictionary key: less-than constant.
                "<",  # Dictionary value: less-than symbol.
            self.OPERATOR_LESS_EQUAL:  # Dictionary key: less-or-equal constant.
                "≤",  # Dictionary value: less-than-or-equal symbol.
        }  # Dictionary ends here.

        return (  # Return statement: sends the selected symbol back to the caller.
            symbols.get(  # Dictionary method: performs a safe key lookup.
                self.operator,  # Lookup key: operator stored by this AlertRule.
                self.operator,  # Fallback value: return the original operator if it is not found.
            )  # get() call ends here.
        )  # Returned expression ends here.

    # ========================================================
    # 7.17 CONDITION DISPLAY
    # Programming concepts: property and f-strings
    # ========================================================

    @property  # Decorator: exposes this method as rule.condition_display.
    def condition_display(self):  # Property method: constructs readable text describing the monitoring rule.
        """
        Return a concise human-readable rule.

        Example:

            Price > 260.000000
        """

        return (  # Return statement begins.
            f"{self.get_metric_display()} "  # F-string + Django method: converts the metric choice to its label.
            f"{self.operator_symbol} "  # F-string: inserts the calculated operator symbol.
            f"{self.threshold}"  # F-string: inserts the stored numeric threshold.
        )  # Returned string expression ends here.

    # ========================================================
    # 7.18 RULE ACTIVE / PAUSED LABEL
    # Programming concepts: property, if statement and return
    # ========================================================

    @property  # Decorator: allows templates to use rule.status_display.
    def status_display(self):  # Property method: translates Boolean state into user-readable text.
        """
        Return a user-friendly rule status for templates.
        """

        if self.is_enabled:  # Conditional: checks whether monitoring is enabled.
            return "Active"  # Return statement: immediately returns the active label.

        return "Paused"  # Return statement: used when the preceding condition was false.

    # ========================================================
    # 7.19 HAS TRIGGERED
    # Programming concepts: property, identity comparison and None
    # ========================================================

    @property  # Decorator: exposes the calculated value as rule.has_triggered.
    def has_triggered(self):  # Property method: determines whether a trigger timestamp exists.
        """
        Return True when this rule has generated at least one
        alert event.
        """

        return (  # Return statement begins.
            self.last_triggered_at  # Attribute: timestamp of the most recent trigger.
            is not None  # Identity comparison: True only when the value is not Python's None object.
        )  # Boolean expression ends here.

    # ========================================================
    # 7.20 STRING REPRESENTATION
    # Programming concepts: special method, f-string and composition
    # ========================================================

    def __str__(self):  # Special method: defines the readable representation of an AlertRule object.
        """
        Example:

            SPY: Price > 800.000000
        """

        return (  # Return statement begins.
            f"{self.symbol}: "  # F-string: adds the rule's normalised market symbol.
            f"{self.condition_display}"  # F-string: reuses the condition_display property.
        )  # Returned string expression ends here.