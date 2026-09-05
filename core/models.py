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


ALERT WORKFLOW:

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
# Django's configured user model instead of hard-coding
# a particular User class.
from django.conf import settings


# Django's models module provides the field types and database
# model functionality used throughout this file.
from django.db import models


# timezone provides timezone-aware timestamps when alerts are
# resolved.
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

    Alerts should therefore represent meaningful conditions
    rather than ordinary information.

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
    #
    # Examples:
    #
    # /data/import/?symbol=AAPL
    #
    # /strategy/robustness/
    #
    # /risk/stress-test/results/
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
    #
    # Example:
    #
    # {
    #     "symbol": "AAPL",
    #     "days_old": 4,
    #     "provider": "Alpaca"
    # }
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
            #
            # Example:
            #
            # user1
            # +
            # DATA_STALE_AAPL
            # +
            # active
            #
            # may only exist once.
            #
            # Once an alert has been resolved, the same condition
            # can generate a new active alert in the future.
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

        This is important for the Dashboard because automatic
        checks may run many times.

        Without this helper:

            Refresh Dashboard
                ↓
            Alert created

            Refresh Dashboard again
                ↓
            Duplicate alert created

        With this helper:

            Condition detected
                ↓
            Existing active alert?
                ↓
            YES → update it
            NO  → create it

        The user's is_read status is deliberately preserved when
        an existing alert is updated.
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


        # update_or_create looks for an already-active alert
        # belonging to this user and condition.
        #
        # If one exists, its descriptive information is updated.
        #
        # If one does not exist, Django creates a new record.
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

        This is useful for automatic checks.

        Example:

        AAPL was stale
            ↓
        DATA_STALE_AAPL created

        Data refreshed
            ↓
        resolve_by_key(
            user=user,
            alert_key="DATA_STALE_AAPL"
        )

        The database record remains available as historical
        evidence that the condition previously occurred.
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
        preserves an alert history instead of deleting it.
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

        Normally automatic Dashboard logic should use
        create_or_update(), but this helper remains useful for
        manually reopening a specific historical record.
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
        Convenience property used by templates and views.

        Returns True when the alert is no longer active.
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
        Return a Bootstrap-compatible class name for the alert
        severity.

        This allows templates to use:

            alert-{{ alert.bootstrap_class }}

        rather than containing repeated severity mapping logic.
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