"""
============================================================
MARKETPULSE - CORE FORMS
============================================================

SHORT PURPOSE:

This file controls MarketPulse Alert forms.

It receives data entered by the user, prepares the form fields,
checks whether the data is valid, cleans the data, and connects
the validated data to the Alert and AlertRule Django models.

FRAMEWORK:

Browser / Dashboard
    ↓
HTML Form / Modal
    ↓
core/views.py
    ↓
core/forms.py
    ↓
Validation / Cleaning
    ↓
core/models.py
    ↓
Django ORM
    ↓
PostgreSQL / Neon

If validation fails:

core/forms.py
    ↓
core/views.py
    ↓
Template
    ↓
Error shown to user


LECTURE - PROGRAMMING LANGUAGE FEATURES / CONCEPTS:

Module
    → This Python file is a module.

Import
    → Imports Django forms and MarketPulse models.

Class
    → AlertEditForm and AlertRuleForm are Python classes.

Inheritance
    → Both forms inherit from Django forms.ModelForm.

Object-Oriented Programming
    → Forms combine data and behaviour inside classes.

Nested Class
    → Meta is a class inside each ModelForm class.

Functions / Methods
    → clean_title(), clean_symbol(), clean(), etc.

Parameters
    → self, *args and **kwargs pass information to methods.

Variables
    → title, message, symbol, threshold and cooldown.

Lists
    → fields stores ordered collections of field names.

Dictionaries
    → widgets, labels, help_texts and attrs use key/value pairs.

Sets
    → allowed_characters stores unique permitted characters.

Strings
    → Used for labels, messages, field names and HTML attributes.

Conditionals
    → if statements make decisions during validation.

Boolean Logic
    → and / not / comparisons combine conditions.

Iteration
    → The generator expression checks each symbol character.

Exceptions
    → ValidationError stops invalid form data.

Return Values
    → Cleaning methods return validated values.

Method Overriding
    → clean() and __init__() extend Django's existing methods.

super()
    → Calls the inherited Django ModelForm implementation.

============================================================
FRAMEWORK MAPPING
============================================================

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
# Programming concept: MODULES AND IMPORTS
# Imports let this module reuse code provided by Django.
# ============================================================

from django import forms  # Imports Django's forms framework into this Python module.


# ============================================================
# 2. CORE MODELS
# Programming concept: RELATIVE IMPORTS / REUSING CLASSES
# "." means import from the current Django application.
# ============================================================

from .models import (  # Imports model classes defined inside core/models.py.
    Alert,  # Imports the Alert model representing an alert already created.
    AlertRule,  # Imports the AlertRule model representing a condition to monitor.
)


# ============================================================
# 3. ALERT EDIT FORM
# Programming concepts:
# CLASS + INHERITANCE + OBJECT-ORIENTED PROGRAMMING
#
# AlertEditForm becomes a specialised version of ModelForm.
# Django provides ModelForm behaviour and this class customises it.
# ============================================================

class AlertEditForm(
    forms.ModelForm  # Inheritance: this form receives ModelForm functionality from Django.
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
    # Programming concept: NESTED CLASS
    #
    # Meta is a class inside AlertEditForm.
    # Django reads it as configuration for the ModelForm.
    # ========================================================

    class Meta:
        model = Alert  # Associates this ModelForm with the Alert database model.

        # ----------------------------------------------------
        # USER-EDITABLE ALERT FIELDS
        # Programming concept: LIST
        #
        # A list keeps several values together in an ordered
        # collection.
        # ----------------------------------------------------

        fields = [
            "alert_type",  # Makes the Alert alert_type field available in the form.
            "severity",  # Makes the Alert severity field available in the form.
            "title",  # Makes the Alert title field available in the form.
            "message",  # Makes the Alert message field available in the form.
            "action_url",  # Makes the Alert action URL available in the form.
            "is_read",  # Makes the Alert read-status field available in the form.
        ]

        # ----------------------------------------------------
        # BOOTSTRAP FORM WIDGETS
        # Programming concept: DICTIONARY
        #
        # A dictionary stores key:value pairs.
        # Here:
        #
        # field name → Django HTML widget
        # ----------------------------------------------------

        widgets = {
            # ------------------------------------------------
            # ALERT TYPE
            # ------------------------------------------------
            "alert_type":
                forms.Select(  # Creates an HTML <select> control for alert_type.
                    attrs={  # Dictionary containing HTML attributes for the widget.
                        "class":
                            "form-select",  # Adds Bootstrap's form-select CSS class.
                    }
                ),

            # ------------------------------------------------
            # SEVERITY
            # ------------------------------------------------
            "severity":
                forms.Select(  # Creates an HTML <select> control for severity.
                    attrs={  # Supplies HTML attributes to the select element.
                        "class":
                            "form-select",  # Applies Bootstrap select styling.
                    }
                ),

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------
            "title":
                forms.TextInput(  # Creates a normal HTML text input.
                    attrs={  # Defines extra HTML attributes.
                        "class":
                            "form-control",  # Applies Bootstrap text-input styling.
                        "placeholder":
                            "Alert title",  # Displays guidance before the user enters a title.
                    }
                ),

            # ------------------------------------------------
            # MESSAGE
            # ------------------------------------------------
            "message":
                forms.Textarea(  # Creates a multi-line HTML textarea.
                    attrs={  # Stores textarea HTML attributes.
                        "class":
                            "form-control",  # Applies Bootstrap form-control styling.
                        "rows":
                            4,  # Displays the textarea approximately four rows high.
                        "placeholder":
                            (
                                "Explain what requires "
                                "attention."
                            ),  # Gives the user instructions inside the empty textarea.
                    }
                ),

            # ------------------------------------------------
            # ACTION URL
            # ------------------------------------------------
            "action_url":
                forms.TextInput(  # Creates a text field for the optional action URL.
                    attrs={  # Defines HTML attributes for this input.
                        "class":
                            "form-control",  # Applies Bootstrap input styling.
                        "placeholder":
                            "/data/import/?symbol=AAPL",  # Shows an example internal application URL.
                    }
                ),

            # ------------------------------------------------
            # READ STATUS
            # ------------------------------------------------
            "is_read":
                forms.CheckboxInput(  # Creates an HTML checkbox for the Boolean field.
                    attrs={  # Defines attributes belonging to the checkbox.
                        "class":
                            "form-check-input",  # Applies Bootstrap checkbox styling.
                    }
                ),
        }

    # ========================================================
    # 3.2 CLEAN TITLE
    # Programming concepts:
    # METHOD + VARIABLE + DICTIONARY LOOKUP + RETURN VALUE
    #
    # Django automatically calls clean_title() while validating
    # the field named "title".
    # ========================================================

    def clean_title(
        self,  # self represents the current AlertEditForm object.
    ):
        """
        Remove unnecessary leading/trailing whitespace from the
        Alert title.
        """

        title = (  # Creates a local variable containing the submitted title.
            self.cleaned_data  # cleaned_data stores form values Django has already processed.
            .get(  # get() safely retrieves a dictionary value.
                "title",  # Looks for the title field.
                "",  # Uses an empty string if title is unavailable.
            )
        )

        return (  # Sends the cleaned title back to Django.
            str(  # Converts the value to a Python string.
                title  # Uses the submitted title.
                or  # Boolean operator: if title is false/empty, use the next value.
                ""  # Provides a safe empty-string fallback.
            )
            .strip()  # Removes whitespace from the beginning and end.
        )

    # ========================================================
    # 3.3 CLEAN MESSAGE
    # Programming concept: FIELD-SPECIFIC VALIDATION METHOD
    # ========================================================

    def clean_message(
        self,  # self refers to this specific form instance.
    ):
        """
        Remove unnecessary whitespace from the alert message.

        The message content itself is not changed.
        """

        message = (  # Stores the submitted message in a local variable.
            self.cleaned_data  # Accesses Django's cleaned form-data dictionary.
            .get(  # Safely reads a value by its dictionary key.
                "message",  # Requests the message field.
                "",  # Uses an empty string when no value exists.
            )
        )

        return (  # Returns the final cleaned message to Django.
            str(  # Makes sure the value is represented as text.
                message  # Uses the submitted message.
                or  # Falls back when message evaluates to false.
                ""  # Empty-string fallback.
            )
            .strip()  # Removes unwanted whitespace from both ends.
        )

    # ========================================================
    # 3.4 CLEAN ACTION URL
    # Programming concept: DATA NORMALISATION
    #
    # Normalisation converts equivalent user inputs into one
    # consistent stored representation.
    # ========================================================

    def clean_action_url(
        self,  # self gives this method access to the current form object.
    ):
        """
        Normalise the optional Alert action URL.

        Example:

            "  /data/import/?symbol=AAPL  "

        becomes:

            "/data/import/?symbol=AAPL"
        """

        action_url = (  # Stores the submitted URL in a local variable.
            self.cleaned_data  # Reads from Django's cleaned form-data dictionary.
            .get(  # Gets a dictionary value safely.
                "action_url",  # Requests the action_url field.
                "",  # Uses an empty string if the field has no value.
            )
        )

        return (  # Returns the normalised URL.
            str(  # Converts the value into text.
                action_url  # Uses the URL entered by the user.
                or  # Uses the fallback if no URL was supplied.
                ""  # Safe empty-string fallback.
            )
            .strip()  # Removes spaces from the beginning and end.
        )


# ============================================================
# 4. ALERT RULE FORM
# Programming concepts:
# CLASS + INHERITANCE + ABSTRACTION
#
# The form hides much of Django's database/form machinery and
# exposes only the fields needed to define an alert rule.
# ============================================================

class AlertRuleForm(
    forms.ModelForm  # Inherits Django ModelForm functionality.
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
    # Programming concept: DECLARATIVE CONFIGURATION
    #
    # Instead of manually programming every HTML field, Meta
    # describes what Django should build.
    # ========================================================

    class Meta:
        model = AlertRule  # Connects this form with the AlertRule model.

        # ----------------------------------------------------
        # USER-EDITABLE ALERT RULE FIELDS
        # Programming concept: LIST
        # ----------------------------------------------------

        fields = [
            "symbol",  # Market ticker that the rule should monitor.
            "metric",  # Measurement such as price, volume or volatility.
            "operator",  # Comparison operation used by the rule.
            "threshold",  # Number against which the metric is compared.
            "message",  # Optional custom message for generated alerts.
            "cooldown_minutes",  # Minimum delay between repeated alerts.
            "is_enabled",  # Boolean controlling whether the rule is active.
        ]

        # ----------------------------------------------------
        # BOOTSTRAP FORM WIDGETS
        # Programming concepts:
        # DICTIONARIES + OBJECT CREATION + KEYWORD ARGUMENTS
        # ----------------------------------------------------

        widgets = {
            # ------------------------------------------------
            # MARKET SYMBOL
            # ------------------------------------------------
            "symbol":
                forms.TextInput(  # Creates a text-input widget object.
                    attrs={  # Dictionary of HTML attributes.
                        "class":
                            "form-control",  # Bootstrap styling class.
                        "placeholder":
                            "AAPL, MSFT, SPY...",  # Example ticker symbols.
                        "autocomplete":
                            "off",  # Asks the browser not to autofill previous values.
                        "maxlength":
                            "20",  # Limits the HTML input to twenty characters.
                    }
                ),

            # ------------------------------------------------
            # METRIC
            # ------------------------------------------------
            "metric":
                forms.Select(  # Creates a dropdown/select element.
                    attrs={  # Supplies HTML attributes.
                        "class":
                            "form-select",  # Adds Bootstrap dropdown styling.
                    }
                ),

            # ------------------------------------------------
            # COMPARISON OPERATOR
            # ------------------------------------------------
            "operator":
                forms.Select(  # Creates a dropdown for the comparison operator.
                    attrs={  # Stores HTML attributes.
                        "class":
                            "form-select",  # Applies Bootstrap select styling.
                    }
                ),

            # ------------------------------------------------
            # THRESHOLD
            # ------------------------------------------------
            "threshold":
                forms.NumberInput(  # Creates an HTML numeric input.
                    attrs={  # Contains its HTML attributes.
                        "class":
                            "form-control",  # Adds Bootstrap input styling.
                        "step":
                            "0.01",  # Allows decimal increments such as 0.01.
                        "placeholder":
                            "Enter threshold",  # Explains what value the user should enter.
                    }
                ),

            # ------------------------------------------------
            # CUSTOM ALERT MESSAGE
            # ------------------------------------------------
            "message":
                forms.TextInput(  # Creates a single-line text field.
                    attrs={  # Defines browser-side HTML attributes.
                        "class":
                            "form-control",  # Applies Bootstrap styling.
                        "placeholder":
                            (
                                "Optional alert message"
                            ),  # Explains that this field does not have to be populated.
                        "maxlength":
                            "255",  # Limits the browser input to 255 characters.
                    }
                ),

            # ------------------------------------------------
            # COOLDOWN
            # ------------------------------------------------
            "cooldown_minutes":
                forms.NumberInput(  # Creates a numeric cooldown input.
                    attrs={  # Dictionary containing HTML attributes.
                        "class":
                            "form-control",  # Applies Bootstrap styling.
                        "min":
                            "1",  # Browser-side minimum value is one.
                        "step":
                            "1",  # Allows whole-number increments.
                        "placeholder":
                            "60",  # Displays an example cooldown.
                    }
                ),

            # ------------------------------------------------
            # ENABLE / DISABLE
            # ------------------------------------------------
            "is_enabled":
                forms.CheckboxInput(  # Creates a Boolean checkbox.
                    attrs={  # Provides the checkbox HTML attributes.
                        "class":
                            "form-check-input",  # Bootstrap checkbox styling.
                    }
                ),
        }

        # ----------------------------------------------------
        # FIELD LABELS
        # Programming concept: DICTIONARY
        #
        # key   = Django/model field name
        # value = user-friendly label
        # ----------------------------------------------------

        labels = {
            "symbol":
                "Market Symbol",  # User-facing label for symbol.
            "metric":
                "Alert Metric",  # User-facing label for metric.
            "operator":
                "Condition",  # User-facing label for operator.
            "threshold":
                "Threshold",  # User-facing label for threshold.
            "message":
                "Alert Message",  # User-facing label for message.
            "cooldown_minutes":
                "Cooldown (Minutes)",  # User-facing label for cooldown.
            "is_enabled":
                "Enable Alert Rule",  # User-facing label for enabled status.
        }

        # ----------------------------------------------------
        # FIELD HELP TEXT
        # Programming concept: DICTIONARY OF STRINGS
        # ----------------------------------------------------

        help_texts = {
            "symbol":
                (
                    "Enter the ticker MarketPulse should "
                    "monitor, for example AAPL, SPY or QQQ."
                ),  # Explains what the symbol field expects.
            "metric":
                (
                    "Select the market measurement that should "
                    "trigger the rule."
                ),  # Explains the purpose of the metric.
            "operator":
                (
                    "Choose how the current market value should "
                    "be compared with the threshold."
                ),  # Explains the comparison operator.
            "threshold":
                (
                    "Enter the value that should trigger the "
                    "alert condition."
                ),  # Explains the threshold value.
            "message":
                (
                    "Optional message shown when MarketPulse "
                    "creates an Alert."
                ),  # Explains the optional alert message.
            "cooldown_minutes":
                (
                    "Minimum time before the same rule may "
                    "trigger another alert."
                ),  # Explains why cooldown exists.
            "is_enabled":
                (
                    "Disabled rules remain stored but are not "
                    "evaluated."
                ),  # Explains the Boolean enabled state.
        }

    # ========================================================
    # 4.2 INITIAL FORM CONFIGURATION
    # Programming concepts:
    # CONSTRUCTOR + PARAMETERS + *ARGS + **KWARGS + SUPER()
    #
    # __init__() runs when an AlertRuleForm object is created.
    #
    # *args:
    # collects positional arguments.
    #
    # **kwargs:
    # collects named/keyword arguments.
    #
    # super():
    # calls Django ModelForm's existing __init__() method.
    # ========================================================

    def __init__(
        self,  # Current AlertRuleForm object.
        *args,  # Collects any positional arguments supplied to the form.
        **kwargs,  # Collects any keyword arguments supplied to the form.
    ):
        """
        Apply small usability improvements after Django creates
        the ModelForm fields.
        """

        super().__init__(  # Calls the inherited Django ModelForm constructor.
            *args,  # Passes positional arguments to the parent constructor.
            **kwargs,  # Passes keyword arguments to the parent constructor.
        )

        # ----------------------------------------------------
        # SYMBOL INPUT
        # Programming concept: CONDITIONAL
        #
        # The if statement checks whether a condition is true
        # before executing the indented block.
        # ----------------------------------------------------

        if "symbol" in self.fields:  # Checks that Django created a field named symbol.
            self.fields[  # Accesses the form's dictionary of fields.
                "symbol"  # Selects the symbol field by its dictionary key.
            ].widget.attrs.update(  # Adds attributes to the symbol field's HTML widget.
                {
                    "aria-label":
                        "Market symbol",  # Adds an accessibility label.
                }
            )

        # ----------------------------------------------------
        # THRESHOLD INPUT
        # ----------------------------------------------------

        if "threshold" in self.fields:  # Checks that the threshold field exists.
            self.fields[  # Accesses the current form's fields.
                "threshold"  # Selects the threshold field.
            ].widget.attrs.update(  # Adds another HTML attribute to its widget.
                {
                    "aria-label":
                        "Alert threshold",  # Provides an accessible name for the input.
                }
            )

        # ----------------------------------------------------
        # DEFAULT COOLDOWN
        # ----------------------------------------------------

        if (  # Starts a multi-line Boolean condition.
            "cooldown_minutes"  # Field name being searched for.
            in  # Membership operator checks whether the key exists.
            self.fields  # Dictionary containing the form fields.
        ):
            self.fields[  # Accesses the form fields collection.
                "cooldown_minutes"  # Selects the cooldown field.
            ].widget.attrs.update(  # Adds attributes to its HTML widget.
                {
                    "aria-label":
                        "Alert cooldown minutes",  # Accessibility label for the cooldown field.
                }
            )

    # ========================================================
    # 4.3 CLEAN MARKET SYMBOL
    # Programming concepts:
    # METHOD + NORMALISATION + STRING METHODS + CONDITIONALS
    # + SETS + ITERATION + GENERATOR EXPRESSION + EXCEPTIONS
    # ========================================================

    def clean_symbol(
        self,  # Current AlertRuleForm object.
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

        symbol = (  # Creates a local variable for the submitted ticker.
            self.cleaned_data  # Dictionary containing Django-cleaned values.
            .get(  # Retrieves a dictionary value safely.
                "symbol",  # Requests the symbol field.
                "",  # Provides an empty-string default.
            )
        )

        symbol = (  # Reassigns symbol with its normalised value.
            str(  # Converts the value to a string.
                symbol  # Uses the value previously retrieved.
                or  # Boolean OR supplies the fallback when necessary.
                ""  # Empty-string fallback.
            )
            .strip()  # Removes leading and trailing spaces.
            .upper()  # Converts letters to uppercase.
        )

        if not symbol:  # Tests whether the cleaned symbol is empty.
            raise forms.ValidationError(  # Raises a Django validation exception.
                (
                    "A market symbol is required."
                )  # Message that Django can display beside the form.
            )

        # ----------------------------------------------------
        # SIMPLE TICKER VALIDATION
        # Programming concepts:
        # SET + MEMBERSHIP + ITERATION
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

        allowed_characters = set(  # Creates a set containing unique allowed characters.
            (
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # Allows uppercase letters.
                "0123456789"  # Allows numeric digits.
                ".-"  # Allows periods and hyphens.
            )
        )

        if not all(  # all() is true only when every generated Boolean value is true.
            character  # Current character being inspected.
            in  # Membership operator.
            allowed_characters  # Checks whether the character belongs to the allowed set.

            for character  # Iteration variable representing one symbol character at a time.
            in  # Starts iteration through the following value.
            symbol  # Iterates over every character in the ticker symbol.
        ):
            raise forms.ValidationError(  # Stops validation for an invalid ticker.
                (
                    "Enter a valid market symbol using letters, "
                    "numbers, periods or hyphens only."
                )  # Explains the accepted characters to the user.
            )

        if len(  # len() calculates how many characters are in the symbol.
            symbol  # Value whose length Django needs to validate.
        ) > 20:  # Comparison operator checks whether it exceeds twenty characters.
            raise forms.ValidationError(  # Creates a form validation error.
                (
                    "The market symbol is too long."
                )  # User-facing validation message.
            )

        return symbol  # Returns the validated uppercase symbol to Django.

    # ========================================================
    # 4.4 CLEAN THRESHOLD
    # Programming concepts:
    # VARIABLE + NONE + CONDITIONAL + EXCEPTION + RETURN
    # ========================================================

    def clean_threshold(
        self,  # Current form object.
    ):
        """
        Validate the numeric condition threshold.

        Negative thresholds are deliberately allowed because
        they are useful for percentage-change rules.

        Example:

            Percent Change < -3
        """

        threshold = (  # Stores the submitted threshold.
            self.cleaned_data  # Reads Django's cleaned values.
            .get(  # Safely accesses the dictionary.
                "threshold"  # Requests the threshold value.
            )
        )

        if threshold is None:  # Checks specifically whether no threshold value exists.
            raise forms.ValidationError(  # Raises a form validation exception.
                (
                    "A threshold value is required."
                )  # Error displayed to the user.
            )

        return threshold  # Returns the valid numeric threshold.

    # ========================================================
    # 4.5 CLEAN COOLDOWN
    # Programming concepts:
    # CONDITIONAL BRANCHING + COMPARISON + RETURN VALUES
    # ========================================================

    def clean_cooldown_minutes(
        self,  # Current form object.
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

        cooldown = (  # Creates a local variable holding the submitted cooldown.
            self.cleaned_data  # Accesses Django's cleaned form data.
            .get(  # Retrieves the requested dictionary value.
                "cooldown_minutes"  # Field being retrieved.
            )
        )

        if cooldown is None:  # Checks whether the user supplied no cooldown.
            return 60  # Uses sixty minutes as the default return value.

        if cooldown < 1:  # Checks the lower numerical boundary.
            raise forms.ValidationError(  # Rejects values below one.
                (
                    "Cooldown must be at least 1 minute."
                )  # Error message for the user.
            )

        # Very large cooldowns are technically possible but are
        # unlikely to be intentional in this educational
        # application.
        if cooldown > 525600:  # Checks the upper numerical boundary of one year.
            raise forms.ValidationError(  # Rejects a cooldown that exceeds this limit.
                (
                    "Cooldown cannot exceed one year."
                )  # Explains why the submitted value failed.
            )

        return cooldown  # Returns the validated cooldown value.

    # ========================================================
    # 4.6 CLEAN OPTIONAL MESSAGE
    # Programming concepts:
    # STRING CONVERSION + METHOD CHAINING + RETURN
    # ========================================================

    def clean_message(
        self,  # Current form instance.
    ):
        """
        Strip unnecessary whitespace from the optional user
        message.
        """

        message = (  # Stores the submitted custom message.
            self.cleaned_data  # Accesses Django's cleaned form-data dictionary.
            .get(  # Safely retrieves a dictionary value.
                "message",  # Requests the message field.
                "",  # Provides an empty-string default.
            )
        )

        return (  # Returns the cleaned message.
            str(  # Converts the value into a Python string.
                message  # Uses the user-provided message.
                or  # Falls back if the message is empty/falsy.
                ""  # Empty-string fallback.
            )
            .strip()  # Removes whitespace from the beginning and end.
        )

    # ========================================================
    # 4.7 CROSS-FIELD VALIDATION
    # Programming concepts:
    # METHOD OVERRIDING + SUPER() + MULTIPLE VARIABLES
    # + BOOLEAN EXPRESSIONS + COMPARISON + ERROR HANDLING
    #
    # clean_<field>() validates one field.
    #
    # clean() can compare several fields together.
    # ========================================================

    def clean(
        self,  # Current AlertRuleForm object.
    ):
        """
        Perform validation involving more than one field.

        This lets MarketPulse explain obvious invalid
        combinations before the rule reaches the database.
        """

        cleaned_data = (  # Stores all values validated so far.
            super().clean()  # Calls Django ModelForm's normal clean() implementation first.
        )

        metric = (  # Stores the selected metric in a local variable.
            cleaned_data.get(  # Safely reads from the cleaned-data dictionary.
                "metric"  # Retrieves the metric field.
            )
        )

        threshold = (  # Stores the cleaned threshold in a local variable.
            cleaned_data.get(  # Safely reads from the dictionary.
                "threshold"  # Retrieves the threshold field.
            )
        )

        # ----------------------------------------------------
        # VOLUME CANNOT BE NEGATIVE
        # Programming concept: COMPOUND BOOLEAN CONDITION
        #
        # All three expressions connected with "and" must be
        # true before the body of this if statement executes.
        # ----------------------------------------------------

        if (
            metric  # Current rule metric.
            ==
            AlertRule.METRIC_VOLUME  # Checks whether the metric is volume.
            and  # Logical AND requires the next condition to also be true.
            threshold is not None  # Makes sure a threshold exists before comparing it.
            and  # Logical AND combines another condition.
            threshold < 0  # Tests whether the numeric threshold is negative.
        ):
            self.add_error(  # Adds a validation error to a specific form field.
                "threshold",  # Attaches the error to the threshold input.
                (
                    "Volume thresholds cannot be negative."
                ),  # Message displayed to the user.
            )

        # ----------------------------------------------------
        # PRICE CANNOT BE NEGATIVE
        # ----------------------------------------------------

        if (
            metric  # Selected alert-rule metric.
            ==
            AlertRule.METRIC_PRICE  # Checks whether the rule monitors price.
            and  # Requires the following condition too.
            threshold is not None  # Confirms a threshold exists.
            and  # Combines the final condition.
            threshold < 0  # Checks whether the price threshold is negative.
        ):
            self.add_error(  # Adds an error without immediately throwing away cleaned_data.
                "threshold",  # Associates the error with the threshold field.
                (
                    "Price thresholds cannot be negative."
                ),  # User-facing validation message.
            )

        # ----------------------------------------------------
        # VOLATILITY CANNOT BE NEGATIVE
        # ----------------------------------------------------

        if (
            metric  # Current selected metric.
            ==
            AlertRule.METRIC_VOLATILITY  # Checks whether the metric represents volatility.
            and  # Requires another true expression.
            threshold is not None  # Makes sure threshold has a value.
            and  # Requires the final test as well.
            threshold < 0  # Checks whether volatility threshold is negative.
        ):
            self.add_error(  # Adds a field-specific Django validation error.
                "threshold",  # Places the error beside the threshold form field.
                (
                    "Volatility thresholds cannot be negative."
                ),  # Explains the invalid combination.
            )

        return cleaned_data  # Returns all validated form values back to Django.