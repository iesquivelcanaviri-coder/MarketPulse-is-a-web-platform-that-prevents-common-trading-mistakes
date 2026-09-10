"""
============================================================
MARKETPULSE - CORE FORMS
============================================================

Framework mapping:

Dashboard
    ↓
Alert / Alert Rule Forms
    ↓
core/forms.py
    ↓
core/models.py
    ↓
Django ORM
    ↓
PostgreSQL / Neon


============================================================
FORM RESPONSIBILITIES
============================================================

This module contains two separate concepts.


1. AlertEditForm
------------------------------------------------------------

Used to edit an Alert that has already been generated.

Example:

    MarketPulse generated:
        "SPY volatility has increased."

The user may edit presentation fields such as:

    - alert type
    - severity
    - title
    - message
    - action URL
    - read status


2. AlertRuleForm
------------------------------------------------------------

Used to configure a condition that MarketPulse should monitor.

Example:

    Symbol:
        SPY

    Metric:
        Price

    Operator:
        Greater Than

    Threshold:
        800

This represents:

        SPY price > 800


AlertRule therefore defines:

    WHAT MarketPulse should monitor.

Alert defines:

    WHAT MarketPulse has already detected.


============================================================
SECURITY / DATA INTEGRITY
============================================================

System-managed fields are deliberately excluded from forms.

Examples include:

    Alert:
        alert_key
        created_at
        updated_at
        resolved_at

    AlertRule:
        user
        created_at
        updated_at
        last_triggered_at

The authenticated user is attached to AlertRule inside
core/views.py rather than being supplied by the browser.

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

from django import forms


# ============================================================
# 2. CORE MODELS
# ============================================================

from .models import (
    Alert,
    AlertRule,
)


# ============================================================
# 3. ALERT EDIT FORM
# ============================================================

class AlertEditForm(
    forms.ModelForm
):
    """
    ============================================================
    EDIT GENERATED ALERT
    ============================================================

    Allow the user to modify selected presentation and
    acknowledgement information belonging to an existing Alert.

    Alert activation and resolution are handled separately by
    dedicated views.

    This is important because resolving an Alert should also
    correctly update fields such as:

        resolved_at

    rather than allowing the user to manually change system
    state from an ordinary form.
    ============================================================
    """


    # ========================================================
    # 3.1 FORM CONFIGURATION
    # ========================================================

    class Meta:

        model = Alert


        # ----------------------------------------------------
        # USER-EDITABLE ALERT FIELDS
        # ----------------------------------------------------

        fields = [

            "alert_type",

            "severity",

            "title",

            "message",

            "action_url",

            "is_read",

        ]


        # ----------------------------------------------------
        # BOOTSTRAP FORM WIDGETS
        # ----------------------------------------------------

        widgets = {


            # ------------------------------------------------
            # ALERT TYPE
            # ------------------------------------------------

            "alert_type":
                forms.Select(
                    attrs={

                        "class":
                            "form-select",

                    }
                ),


            # ------------------------------------------------
            # SEVERITY
            # ------------------------------------------------

            "severity":
                forms.Select(
                    attrs={

                        "class":
                            "form-select",

                    }
                ),


            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            "title":
                forms.TextInput(
                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            "Alert title",

                    }
                ),


            # ------------------------------------------------
            # MESSAGE
            # ------------------------------------------------

            "message":
                forms.Textarea(
                    attrs={

                        "class":
                            "form-control",

                        "rows":
                            4,

                        "placeholder":
                            (
                                "Explain what requires "
                                "attention."
                            ),

                    }
                ),


            # ------------------------------------------------
            # ACTION URL
            # ------------------------------------------------

            "action_url":
                forms.TextInput(
                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            "/data/import/?symbol=AAPL",

                    }
                ),


            # ------------------------------------------------
            # READ STATUS
            # ------------------------------------------------

            "is_read":
                forms.CheckboxInput(
                    attrs={

                        "class":
                            "form-check-input",

                    }
                ),

        }


    # ========================================================
    # 3.2 CLEAN TITLE
    # ========================================================

    def clean_title(
        self,
    ):
        """
        Remove unnecessary leading/trailing whitespace from the
        Alert title.
        """

        title = (
            self.cleaned_data
            .get(
                "title",
                "",
            )
        )


        return (
            str(
                title
                or
                ""
            )
            .strip()
        )


    # ========================================================
    # 3.3 CLEAN MESSAGE
    # ========================================================

    def clean_message(
        self,
    ):
        """
        Remove unnecessary whitespace from the alert message.

        The message content itself is not changed.
        """

        message = (
            self.cleaned_data
            .get(
                "message",
                "",
            )
        )


        return (
            str(
                message
                or
                ""
            )
            .strip()
        )


    # ========================================================
    # 3.4 CLEAN ACTION URL
    # ========================================================

    def clean_action_url(
        self,
    ):
        """
        Normalise the optional Alert action URL.

        Example:

            "  /data/import/?symbol=AAPL  "

        becomes:

            "/data/import/?symbol=AAPL"
        """

        action_url = (
            self.cleaned_data
            .get(
                "action_url",
                "",
            )
        )


        return (
            str(
                action_url
                or
                ""
            )
            .strip()
        )


# ============================================================
# 4. ALERT RULE FORM
# ============================================================

class AlertRuleForm(
    forms.ModelForm
):
    """
    ============================================================
    CREATE / EDIT CONFIGURABLE ALERT RULE
    ============================================================

    This form represents a condition MarketPulse should monitor.

    Example:

        Symbol:
            AAPL

        Metric:
            Price

        Operator:
            Greater Than

        Threshold:
            260

    Meaning:

        AAPL price > 260


    Another example:

        Symbol:
            IWM

        Metric:
            Percent Change

        Operator:
            Less Than

        Threshold:
            -3

    Meaning:

        IWM daily percentage change < -3%


    Framework mapping:

    Dashboard Alert Rule Modal
        ↓
    AlertRuleForm
        ↓
    Validation
        ↓
    core.models.AlertRule
        ↓
    PostgreSQL
    ============================================================
    """


    # ========================================================
    # 4.1 FORM CONFIGURATION
    # ========================================================

    class Meta:

        model = AlertRule


        # ----------------------------------------------------
        # USER-EDITABLE ALERT RULE FIELDS
        # ----------------------------------------------------

        fields = [

            "symbol",

            "metric",

            "operator",

            "threshold",

            "message",

            "cooldown_minutes",

            "is_enabled",

        ]


        # ----------------------------------------------------
        # BOOTSTRAP FORM WIDGETS
        # ----------------------------------------------------

        widgets = {


            # ------------------------------------------------
            # MARKET SYMBOL
            # ------------------------------------------------

            "symbol":
                forms.TextInput(
                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            "AAPL, MSFT, SPY...",

                        "autocomplete":
                            "off",

                        "maxlength":
                            "20",

                    }
                ),


            # ------------------------------------------------
            # METRIC
            # ------------------------------------------------

            "metric":
                forms.Select(
                    attrs={

                        "class":
                            "form-select",

                    }
                ),


            # ------------------------------------------------
            # COMPARISON OPERATOR
            # ------------------------------------------------

            "operator":
                forms.Select(
                    attrs={

                        "class":
                            "form-select",

                    }
                ),


            # ------------------------------------------------
            # THRESHOLD
            # ------------------------------------------------

            "threshold":
                forms.NumberInput(
                    attrs={

                        "class":
                            "form-control",

                        "step":
                            "0.01",

                        "placeholder":
                            "Enter threshold",

                    }
                ),


            # ------------------------------------------------
            # CUSTOM ALERT MESSAGE
            # ------------------------------------------------

            "message":
                forms.TextInput(
                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            (
                                "Optional alert message"
                            ),

                        "maxlength":
                            "255",

                    }
                ),


            # ------------------------------------------------
            # COOLDOWN
            # ------------------------------------------------

            "cooldown_minutes":
                forms.NumberInput(
                    attrs={

                        "class":
                            "form-control",

                        "min":
                            "1",

                        "step":
                            "1",

                        "placeholder":
                            "60",

                    }
                ),


            # ------------------------------------------------
            # ENABLE / DISABLE
            # ------------------------------------------------

            "is_enabled":
                forms.CheckboxInput(
                    attrs={

                        "class":
                            "form-check-input",

                    }
                ),

        }


        # ----------------------------------------------------
        # FIELD LABELS
        # ----------------------------------------------------

        labels = {

            "symbol":
                "Market Symbol",

            "metric":
                "Alert Metric",

            "operator":
                "Condition",

            "threshold":
                "Threshold",

            "message":
                "Alert Message",

            "cooldown_minutes":
                "Cooldown (Minutes)",

            "is_enabled":
                "Enable Alert Rule",

        }


        # ----------------------------------------------------
        # FIELD HELP TEXT
        # ----------------------------------------------------

        help_texts = {

            "symbol":
                (
                    "Enter the ticker MarketPulse should "
                    "monitor, for example AAPL, SPY or QQQ."
                ),

            "metric":
                (
                    "Select the market measurement that should "
                    "trigger the rule."
                ),

            "operator":
                (
                    "Choose how the current market value should "
                    "be compared with the threshold."
                ),

            "threshold":
                (
                    "Enter the value that should trigger the "
                    "alert condition."
                ),

            "message":
                (
                    "Optional message shown when MarketPulse "
                    "creates an Alert."
                ),

            "cooldown_minutes":
                (
                    "Minimum time before the same rule may "
                    "trigger another alert."
                ),

            "is_enabled":
                (
                    "Disabled rules remain stored but are not "
                    "evaluated."
                ),

        }


    # ========================================================
    # 4.2 INITIAL FORM CONFIGURATION
    # ========================================================

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """
        Apply small usability improvements after Django creates
        the ModelForm fields.
        """

        super().__init__(
            *args,
            **kwargs,
        )


        # ----------------------------------------------------
        # SYMBOL INPUT
        # ----------------------------------------------------

        if "symbol" in self.fields:

            self.fields[
                "symbol"
            ].widget.attrs.update(
                {

                    "aria-label":
                        "Market symbol",

                }
            )


        # ----------------------------------------------------
        # THRESHOLD INPUT
        # ----------------------------------------------------

        if "threshold" in self.fields:

            self.fields[
                "threshold"
            ].widget.attrs.update(
                {

                    "aria-label":
                        "Alert threshold",

                }
            )


        # ----------------------------------------------------
        # DEFAULT COOLDOWN
        # ----------------------------------------------------

        if (
            "cooldown_minutes"
            in
            self.fields
        ):

            self.fields[
                "cooldown_minutes"
            ].widget.attrs.update(
                {

                    "aria-label":
                        "Alert cooldown minutes",

                }
            )


    # ========================================================
    # 4.3 CLEAN MARKET SYMBOL
    # ========================================================

    def clean_symbol(
        self,
    ):
        """
        Normalise the selected asset ticker.

        Example:

            "  aapl  "

        becomes:

            "AAPL"

        This makes database filtering more reliable because
        MarketPulse consistently stores symbols in uppercase.
        """

        symbol = (
            self.cleaned_data
            .get(
                "symbol",
                "",
            )
        )


        symbol = (
            str(
                symbol
                or
                ""
            )
            .strip()
            .upper()
        )


        if not symbol:

            raise forms.ValidationError(
                (
                    "A market symbol is required."
                )
            )


        # ----------------------------------------------------
        # SIMPLE TICKER VALIDATION
        # ----------------------------------------------------
        #
        # Alpaca ticker symbols may include some punctuation
        # such as:
        #
        # BRK.B
        #
        # or:
        #
        # BRK-B
        #
        # Therefore the form allows:
        #
        # letters
        # numbers
        # periods
        # hyphens
        # ----------------------------------------------------

        allowed_characters = set(
            (
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789"
                ".-"
            )
        )


        if not all(
            character
            in
            allowed_characters

            for character
            in
            symbol
        ):

            raise forms.ValidationError(
                (
                    "Enter a valid market symbol using letters, "
                    "numbers, periods or hyphens only."
                )
            )


        if len(
            symbol
        ) > 20:

            raise forms.ValidationError(
                (
                    "The market symbol is too long."
                )
            )


        return symbol


    # ========================================================
    # 4.4 CLEAN THRESHOLD
    # ========================================================

    def clean_threshold(
        self,
    ):
        """
        Validate the numeric condition threshold.

        Negative thresholds are deliberately allowed because
        they are useful for percentage-change rules.

        Example:

            Percent Change < -3
        """

        threshold = (
            self.cleaned_data
            .get(
                "threshold"
            )
        )


        if threshold is None:

            raise forms.ValidationError(
                (
                    "A threshold value is required."
                )
            )


        return threshold


    # ========================================================
    # 4.5 CLEAN COOLDOWN
    # ========================================================

    def clean_cooldown_minutes(
        self,
    ):
        """
        Require a positive cooldown interval.

        The cooldown prevents the same condition from creating
        alerts repeatedly within a very short period.

        Example:

            cooldown = 60

        means MarketPulse should wait at least 60 minutes before
        allowing that rule to trigger another Alert.
        """

        cooldown = (
            self.cleaned_data
            .get(
                "cooldown_minutes"
            )
        )


        if cooldown is None:

            return 60


        if cooldown < 1:

            raise forms.ValidationError(
                (
                    "Cooldown must be at least 1 minute."
                )
            )


        # Very large cooldowns are technically possible but are
        # unlikely to be intentional in this educational
        # application.
        if cooldown > 525600:

            raise forms.ValidationError(
                (
                    "Cooldown cannot exceed one year."
                )
            )


        return cooldown


    # ========================================================
    # 4.6 CLEAN OPTIONAL MESSAGE
    # ========================================================

    def clean_message(
        self,
    ):
        """
        Strip unnecessary whitespace from the optional user
        message.
        """

        message = (
            self.cleaned_data
            .get(
                "message",
                "",
            )
        )


        return (
            str(
                message
                or
                ""
            )
            .strip()
        )


    # ========================================================
    # 4.7 CROSS-FIELD VALIDATION
    # ========================================================

    def clean(
        self,
    ):
        """
        Perform validation involving more than one field.

        This lets MarketPulse explain obvious invalid
        combinations before the rule reaches the database.
        """

        cleaned_data = (
            super().clean()
        )


        metric = (
            cleaned_data.get(
                "metric"
            )
        )


        threshold = (
            cleaned_data.get(
                "threshold"
            )
        )


        # ----------------------------------------------------
        # VOLUME CANNOT BE NEGATIVE
        # ----------------------------------------------------

        if (
            metric
            ==
            AlertRule.METRIC_VOLUME
            and
            threshold is not None
            and
            threshold < 0
        ):

            self.add_error(
                "threshold",
                (
                    "Volume thresholds cannot be negative."
                ),
            )


        # ----------------------------------------------------
        # PRICE CANNOT BE NEGATIVE
        # ----------------------------------------------------

        if (
            metric
            ==
            AlertRule.METRIC_PRICE
            and
            threshold is not None
            and
            threshold < 0
        ):

            self.add_error(
                "threshold",
                (
                    "Price thresholds cannot be negative."
                ),
            )


        # ----------------------------------------------------
        # VOLATILITY CANNOT BE NEGATIVE
        # ----------------------------------------------------

        if (
            metric
            ==
            AlertRule.METRIC_VOLATILITY
            and
            threshold is not None
            and
            threshold < 0
        ):

            self.add_error(
                "threshold",
                (
                    "Volatility thresholds cannot be negative."
                ),
            )


        return cleaned_data