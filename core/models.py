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
# ============================================================

# settings is used so ForeignKey relationships point to
# Django's configured user model instead of hard-coding a
# particular User class.
from django.conf import settings


# Django's models module provides the field types and database
# model functionality used throughout this file.
from django.db import models


# timezone provides timezone-aware timestamps when alerts are
# resolved or triggered.
from django.utils import timezone


# ============================================================
# 2. SHARED TIMESTAMP MODEL
# ============================================================

class TimeStampedModel(models.Model):
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
    # Created timestamp
    # --------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
    )


    # --------------------------------------------------------
    # Updated timestamp
    # --------------------------------------------------------

    updated_at = models.DateTimeField(
        auto_now=True,
    )


    class Meta:

        abstract = True


# ============================================================
# 3. MARKET DATA
# ============================================================

class MarketData(TimeStampedModel):
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
    # ========================================================

    symbol = models.CharField(
        max_length=20,
        db_index=True,
    )


    # ========================================================
    # 3.2 OBSERVATION DATE
    # ========================================================

    date = models.DateField(
        db_index=True,
    )


    # ========================================================
    # 3.3 OHLC PRICES
    # ========================================================

    open_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
    )


    high_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
    )


    low_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
    )


    close_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
    )


    # ========================================================
    # 3.4 TRADING VOLUME
    # ========================================================

    volume = models.BigIntegerField(
        default=0,
    )


    # ========================================================
    # 3.5 DATABASE CONFIGURATION
    # ========================================================

    class Meta:

        # ----------------------------------------------------
        # Prevent duplicate daily observations
        # ----------------------------------------------------

        # MarketPulse should only contain one historical record
        # for one symbol on one particular date.
        constraints = [

            models.UniqueConstraint(
                fields=[
                    "symbol",
                    "date",
                ],
                name="unique_symbol_date",
            ),

        ]


        # ----------------------------------------------------
        # Default ordering
        # ----------------------------------------------------

        # The newest market observations appear first unless a
        # particular query asks for another ordering.
        ordering = [
            "-date",
        ]


    # ========================================================
    # 3.6 STRING REPRESENTATION
    # ========================================================

    def __str__(self):

        return (
            f"{self.symbol} "
            f"{self.date}"
        )


# ============================================================
# 4. STRATEGY
# ============================================================

class Strategy(TimeStampedModel):
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
    # ========================================================

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="strategies",
    )


    # ========================================================
    # 4.2 STRATEGY INFORMATION
    # ========================================================

    name = models.CharField(
        max_length=120,
    )


    description = models.TextField(
        blank=True,
    )


    # ========================================================
    # 4.3 STRATEGY STATUS
    # ========================================================

    is_active = models.BooleanField(
        default=True,
    )


    # ========================================================
    # 4.4 STRATEGY CONFIGURATION
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
    rule_config = models.JSONField(
        default=dict,
    )


    # ========================================================
    # 4.5 DATABASE CONFIGURATION
    # ========================================================

    class Meta:

        ordering = [
            "name",
        ]


    # ========================================================
    # 4.6 STRING REPRESENTATION
    # ========================================================

    def __str__(self):

        return self.name


# ============================================================
# 5. BACKTEST
# ============================================================

class Backtest(TimeStampedModel):
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

    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name="backtests",
    )


    # ========================================================
    # 5.2 HISTORICAL DATASET
    # ========================================================

    symbol = models.CharField(
        max_length=20,
    )


    start_date = models.DateField()


    end_date = models.DateField()


    # ========================================================
    # 5.3 PORTFOLIO VALUES
    # ========================================================

    initial_capital = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=10000,
    )


    final_capital = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )


    # ========================================================
    # 5.4 PERFORMANCE MEASURES
    # ========================================================

    total_return = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
    )


    max_drawdown = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
    )


    sharpe_ratio = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
    )


    win_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
    )


    # ========================================================
    # 5.5 TRADING STATISTICS
    # ========================================================

    total_trades = models.PositiveIntegerField(
        default=0,
    )


    transaction_costs = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )


    # ========================================================
    # 5.6 ADDITIONAL CALCULATED OUTPUT
    # ========================================================

    results = models.JSONField(
        default=dict,
    )


    # ========================================================
    # 5.7 DATABASE CONFIGURATION
    # ========================================================

    class Meta:

        # Most recently completed backtests appear first.
        ordering = [
            "-created_at",
        ]


    # ========================================================
    # 5.8 STRING REPRESENTATION
    # ========================================================

    def __str__(self):

        return (
            f"{self.strategy.name}: "
            f"{self.start_date} to {self.end_date}"
        )


# ============================================================
# 6. ALERT
# ============================================================

class Alert(TimeStampedModel):
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
    # ========================================================

    TYPE_PRICE = "price"

    TYPE_DATA = "data"

    TYPE_STRATEGY = "strategy"

    TYPE_RISK = "risk"

    TYPE_STRESS = "stress"

    TYPE_REGIME = "regime"

    TYPE_SYSTEM = "system"


    # ========================================================
    # 6.2 ALERT TYPE CHOICES
    # ========================================================

    TYPES = [

        (
            TYPE_PRICE,
            "Price",
        ),

        (
            TYPE_DATA,
            "Data",
        ),

        (
            TYPE_STRATEGY,
            "Strategy",
        ),

        (
            TYPE_RISK,
            "Risk",
        ),

        (
            TYPE_STRESS,
            "Stress Test",
        ),

        (
            TYPE_REGIME,
            "Market Condition",
        ),

        (
            TYPE_SYSTEM,
            "System",
        ),

    ]


    # ========================================================
    # 6.2.1 BACKWARD-COMPATIBLE ALERT TYPE ALIAS
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
    ALERT_TYPES = TYPES


    # ========================================================
    # 6.3 SEVERITY CONSTANTS
    # ========================================================

    SEVERITY_INFO = "info"

    SEVERITY_SUCCESS = "success"

    SEVERITY_WARNING = "warning"

    SEVERITY_DANGER = "danger"


    # ========================================================
    # 6.4 SEVERITY CHOICES
    # ========================================================

    SEVERITIES = [

        (
            SEVERITY_INFO,
            "Information",
        ),

        (
            SEVERITY_SUCCESS,
            "Success",
        ),

        (
            SEVERITY_WARNING,
            "Warning",
        ),

        (
            SEVERITY_DANGER,
            "High Priority",
        ),

    ]


    # ========================================================
    # 6.5 USER
    # ========================================================

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alerts",
    )


    # ========================================================
    # 6.6 ALERT CLASSIFICATION
    # ========================================================

    alert_type = models.CharField(
        max_length=20,
        choices=TYPES,
    )


    severity = models.CharField(
        max_length=20,
        choices=SEVERITIES,
        default=SEVERITY_INFO,
    )


    # ========================================================
    # 6.7 ALERT CONTENT
    # ========================================================

    title = models.CharField(
        max_length=200,
    )


    message = models.TextField()


    # ========================================================
    # 6.8 ALERT KEY
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
    alert_key = models.CharField(
        max_length=160,
        blank=True,
        db_index=True,
    )


    # ========================================================
    # 6.9 ACTION LINK
    # ========================================================

    # action_url allows an alert to direct the user to the part
    # of MarketPulse where the problem can be investigated.
    action_url = models.CharField(
        max_length=500,
        blank=True,
    )


    # ========================================================
    # 6.10 STRUCTURED METADATA
    # ========================================================

    # Optional JSON metadata can preserve values related to the
    # detected condition without requiring a new database field
    # for every possible alert type.
    metadata = models.JSONField(
        default=dict,
        blank=True,
    )


    # ========================================================
    # 6.11 ALERT STATE
    # ========================================================

    # is_read indicates whether the user has already seen or
    # acknowledged the notification.
    is_read = models.BooleanField(
        default=False,
    )


    # is_active indicates whether the underlying condition still
    # requires attention.
    #
    # An alert can be read while remaining active.
    is_active = models.BooleanField(
        default=True,
    )


    # resolved_at stores when the underlying condition stopped
    # requiring attention.
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )


    # ========================================================
    # 6.12 DATABASE CONFIGURATION
    # ========================================================

    class Meta:

        # Newer alerts appear first by default.
        ordering = [
            "-created_at",
        ]


        constraints = [

            # ------------------------------------------------
            # UNIQUE ACTIVE ALERT
            # ------------------------------------------------
            #
            # One user should not have multiple active alerts
            # representing exactly the same condition.
            models.UniqueConstraint(
                fields=[
                    "user",
                    "alert_key",
                ],
                condition=(
                    models.Q(
                        is_active=True,
                    )
                    &
                    ~models.Q(
                        alert_key="",
                    )
                ),
                name=(
                    "unique_active_alert_key_per_user"
                ),
            ),

        ]


    # ========================================================
    # 6.13 STRING REPRESENTATION
    # ========================================================

    def __str__(self):

        return (
            f"{self.get_severity_display()}: "
            f"{self.title}"
        )


    # ========================================================
    # 6.14 CREATE OR UPDATE ACTIVE ALERT
    # ========================================================

    @classmethod
    def create_or_update(
        cls,
        *,
        user,
        alert_key,
        alert_type,
        severity,
        title,
        message,
        action_url="",
        metadata=None,
    ):
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
        if not alert_key:

            raise ValueError(
                "alert_key is required when creating "
                "a managed MarketPulse alert."
            )


        # Ensure metadata is always stored as a dictionary.
        if metadata is None:

            metadata = {}


        alert, created = (
            cls.objects.update_or_create(

                user=user,

                alert_key=alert_key,

                is_active=True,

                defaults={

                    "alert_type":
                        alert_type,

                    "severity":
                        severity,

                    "title":
                        title,

                    "message":
                        message,

                    "action_url":
                        action_url,

                    "metadata":
                        metadata,

                    "resolved_at":
                        None,
                },
            )
        )


        return (
            alert,
            created,
        )


    # ========================================================
    # 6.15 RESOLVE ALERT BY KEY
    # ========================================================

    @classmethod
    def resolve_by_key(
        cls,
        *,
        user,
        alert_key,
    ):
        """
        Resolve an active alert using its stable alert key.

        The record remains in PostgreSQL as historical evidence.
        """


        now = (
            timezone.now()
        )


        return (
            cls.objects
            .filter(
                user=user,
                alert_key=alert_key,
                is_active=True,
            )
            .update(
                is_active=False,
                resolved_at=now,
                updated_at=now,
            )
        )


    # ========================================================
    # 6.16 MARK ALERT AS READ
    # ========================================================

    def mark_as_read(self):
        """
        Mark the alert as having been seen by the user.

        This does not resolve the underlying condition.
        """

        if not self.is_read:

            self.is_read = True


            self.save(
                update_fields=[
                    "is_read",
                    "updated_at",
                ]
            )


    # ========================================================
    # 6.17 RESOLVE ONE ALERT
    # ========================================================

    def resolve(self):
        """
        Resolve this particular alert.

        The record remains in PostgreSQL so MarketPulse
        preserves alert history instead of deleting it.
        """

        if self.is_active:

            self.is_active = False

            self.resolved_at = (
                timezone.now()
            )


            self.save(
                update_fields=[
                    "is_active",
                    "resolved_at",
                    "updated_at",
                ]
            )


    # ========================================================
    # 6.18 REOPEN ALERT
    # ========================================================

    def reopen(self):
        """
        Reopen this alert record if the same condition becomes
        relevant again.
        """

        self.is_active = True

        self.is_read = False

        self.resolved_at = None


        self.save(
            update_fields=[
                "is_active",
                "is_read",
                "resolved_at",
                "updated_at",
            ]
        )


    # ========================================================
    # 6.19 RESOLUTION STATUS
    # ========================================================

    @property
    def is_resolved(self):
        """
        Return True when the alert is no longer active.
        """

        return (
            not self.is_active
        )


    # ========================================================
    # 6.20 BOOTSTRAP DISPLAY CLASS
    # ========================================================

    @property
    def bootstrap_class(self):
        """
        Return a Bootstrap-compatible severity class.
        """

        mapping = {

            self.SEVERITY_INFO:
                "info",

            self.SEVERITY_SUCCESS:
                "success",

            self.SEVERITY_WARNING:
                "warning",

            self.SEVERITY_DANGER:
                "danger",

        }


        return (
            mapping.get(
                self.severity,
                "secondary",
            )
        )


    # ========================================================
    # 6.21 HAS ACTION
    # ========================================================

    @property
    def has_action(self):
        """
        Return True when the alert contains a destination that
        the Dashboard can send the user to.
        """

        return bool(
            self.action_url
        )


# ============================================================
# 7. ALERT RULE
# ============================================================

class AlertRule(TimeStampedModel):
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
    # ========================================================

    METRIC_PRICE = "price"

    METRIC_VOLUME = "volume"

    METRIC_PERCENT_CHANGE = "percent_change"

    METRIC_VOLATILITY = "volatility"


    # ========================================================
    # 7.2 METRIC CHOICES
    # ========================================================

    METRICS = [

        (
            METRIC_PRICE,
            "Price",
        ),

        (
            METRIC_VOLUME,
            "Volume",
        ),

        (
            METRIC_PERCENT_CHANGE,
            "Percent Change",
        ),

        (
            METRIC_VOLATILITY,
            "Volatility",
        ),

    ]


    # ========================================================
    # 7.3 OPERATOR CONSTANTS
    # ========================================================

    OPERATOR_GREATER_THAN = "gt"

    OPERATOR_GREATER_EQUAL = "gte"

    OPERATOR_LESS_THAN = "lt"

    OPERATOR_LESS_EQUAL = "lte"


    # ========================================================
    # 7.4 OPERATOR CHOICES
    # ========================================================

    OPERATORS = [

        (
            OPERATOR_GREATER_THAN,
            "Greater Than",
        ),

        (
            OPERATOR_GREATER_EQUAL,
            "Greater Than or Equal",
        ),

        (
            OPERATOR_LESS_THAN,
            "Less Than",
        ),

        (
            OPERATOR_LESS_EQUAL,
            "Less Than or Equal",
        ),

    ]


    # ========================================================
    # 7.5 USER
    # ========================================================

    # Every rule belongs to exactly one authenticated
    # MarketPulse user.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marketpulse_alert_rules",
    )


    # ========================================================
    # 7.6 MARKET SYMBOL
    # ========================================================

    # Examples:
    #
    # AAPL
    # MSFT
    # SPY
    # QQQ
    # DIA
    # IWM
    symbol = models.CharField(
        max_length=20,
        db_index=True,
        help_text=(
            "US equity or ETF symbol monitored by this rule."
        ),
    )


    # ========================================================
    # 7.7 METRIC
    # ========================================================

    # Defines which market quantity is monitored.
    metric = models.CharField(
        max_length=30,
        choices=METRICS,
        default=METRIC_PRICE,
    )


    # ========================================================
    # 7.8 COMPARISON OPERATOR
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
    operator = models.CharField(
        max_length=10,
        choices=OPERATORS,
        default=OPERATOR_GREATER_THAN,
    )


    # ========================================================
    # 7.9 THRESHOLD
    # ========================================================

    # DecimalField is used rather than FloatField because some
    # alert thresholds represent financial values.
    threshold = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text=(
            "Numeric threshold used when evaluating the rule."
        ),
    )


    # ========================================================
    # 7.10 OPTIONAL USER MESSAGE
    # ========================================================

    # Example:
    #
    # "AAPL has broken above my target level."
    message = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Optional explanation displayed when the rule "
            "creates an alert."
        ),
    )


    # ========================================================
    # 7.11 ENABLE / DISABLE
    # ========================================================

    # A disabled rule remains stored but MarketPulse should not
    # evaluate it until the user enables it again.
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
    )


    # ========================================================
    # 7.12 COOLDOWN
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
    cooldown_minutes = models.PositiveIntegerField(
        default=60,
        help_text=(
            "Minimum number of minutes before this rule may "
            "trigger another alert."
        ),
    )


    # ========================================================
    # 7.13 LAST TRIGGERED TIME
    # ========================================================

    # This is nullable because a newly created rule may never
    # have triggered.
    last_triggered_at = models.DateTimeField(
        null=True,
        blank=True,
    )


    # ========================================================
    # 7.14 DATABASE CONFIGURATION
    # ========================================================

    class Meta:

        # Enabled rules appear first.
        #
        # Rules are then grouped by symbol and metric.
        ordering = [

            "-is_enabled",

            "symbol",

            "metric",

            "-created_at",

        ]


        # This index makes common rule-monitoring queries more
        # efficient:
        #
        # AlertRule.objects.filter(
        #     user=user,
        #     symbol="SPY",
        #     is_enabled=True,
        # )
        indexes = [

            models.Index(
                fields=[
                    "user",
                    "symbol",
                    "is_enabled",
                ],
            ),

        ]


    # ========================================================
    # 7.15 NORMALISE SYMBOL BEFORE SAVING
    # ========================================================

    def save(
        self,
        *args,
        **kwargs,
    ):
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


        self.symbol = (

            str(
                self.symbol
                or
                ""
            )

            .strip()

            .upper()

        )


        super().save(
            *args,
            **kwargs,
        )


    # ========================================================
    # 7.16 OPERATOR SYMBOL
    # ========================================================

    @property
    def operator_symbol(self):
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


        symbols = {

            self.OPERATOR_GREATER_THAN:
                ">",

            self.OPERATOR_GREATER_EQUAL:
                "≥",

            self.OPERATOR_LESS_THAN:
                "<",

            self.OPERATOR_LESS_EQUAL:
                "≤",

        }


        return (
            symbols.get(
                self.operator,
                self.operator,
            )
        )


    # ========================================================
    # 7.17 CONDITION DISPLAY
    # ========================================================

    @property
    def condition_display(self):
        """
        Return a concise human-readable rule.

        Example:

            Price > 260.000000
        """


        return (

            f"{self.get_metric_display()} "
            f"{self.operator_symbol} "
            f"{self.threshold}"

        )


    # ========================================================
    # 7.18 RULE ACTIVE / PAUSED LABEL
    # ========================================================

    @property
    def status_display(self):
        """
        Return a user-friendly rule status for templates.
        """


        if self.is_enabled:

            return "Active"


        return "Paused"


    # ========================================================
    # 7.19 HAS TRIGGERED
    # ========================================================

    @property
    def has_triggered(self):
        """
        Return True when this rule has generated at least one
        alert event.
        """


        return (
            self.last_triggered_at
            is not None
        )


    # ========================================================
    # 7.20 STRING REPRESENTATION
    # ========================================================

    def __str__(self):
        """
        Example:

            SPY: Price > 800.000000
        """


        return (

            f"{self.symbol}: "
            f"{self.condition_display}"

        )