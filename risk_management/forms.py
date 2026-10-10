"""
============================================================
MARKETPULSE - RISK MANAGEMENT FORMS
============================================================
PURPOSE:
Collect and validate inputs for the Trade & Portfolio Risk Planner.
FRAMEWORK:
Browser / asset search → RiskPlannerForm → risk_management/views.py
→ Alpaca service + historical MarketData → calculators → results.
RESPONSIBILITIES:
Define fields, labels, help text, widgets, and input validation.
Normalise the selected symbol and check stop/target relationships.
This form does not call Alpaca or calculate the final risk plan.
LECTURE:
Imports, classes, inheritance, field assignments, keyword arguments,
strings, numbers, dictionaries, lists, tuples, methods, conditions,
comparison operators, exceptions, and return statements.
============================================================
"""  # Module docstring: explain this file's purpose.

# ============================================================
# 1. IMPORTS
# ============================================================
from django import forms  # Import: reuse Django's form fields, widgets, and validation tools.

# ============================================================
# 2. RISK PLANNER FORM
# ============================================================
class RiskPlannerForm(forms.Form):  # Class and inheritance: extend Django's standard Form class.
    """Collect risk inputs, style their controls, and validate relationships."""  # Class documentation.

    # --------------------------------------------------------
    # 2.1 ASSET / SYMBOL SEARCH
    # --------------------------------------------------------
    # The frontend supplies autocomplete; this field receives text.
    # Alpaca symbol-existence checks belong in the service/view layer.
    symbol = forms.CharField(  # Field assignment: define a text input for the symbol.
        label="Asset / Symbol",  # String keyword argument: set the displayed label.
        required=True,  # Boolean argument: require a non-empty value.
        max_length=20,  # Integer argument: limit the symbol to 20 characters.
        widget=forms.TextInput(  # Constructor call: choose an HTML text-input widget.
            attrs={  # Dictionary: configure the widget's HTML attributes.
                "class": "form-control",  # Apply the Bootstrap control class.
                "id": "id_symbol",  # Give the input an ID used by labels and JavaScript.
                "placeholder": (  # Start the placeholder string expression.
                    "Search symbol or company, "  # First part of the original placeholder.
                    "for example AAPL or Microsoft"  # Adjacent strings join automatically.
                ),  # Finish the placeholder value.
                "autocomplete": "off",  # Request that browser autocomplete be disabled.
                "spellcheck": "false",  # Request that browser spellchecking be disabled.
            }  # Close the HTML-attribute dictionary.
        ),  # Close the text widget.
        help_text=(  # Define explanatory text for the field.
            "Search Alpaca's active US-equity universe by "  # First part of the original help text.
            "ticker symbol or company name, then select an "  # Continue the help text.
            "asset from the search results."  # Finish the help text.
        ),  # Close the help-text expression.
    )  # Close the symbol field.

    # --------------------------------------------------------
    # 2.2 MARKET CURRENCY
    # --------------------------------------------------------
    # This form offers USD only; it does not perform FX conversion.
    currency = forms.ChoiceField(  # Field assignment: restrict input to the listed choices.
        label="Market Currency",  # Set the displayed label.
        choices=[  # List: contain the allowed value/label pairs.
            ("USD", "USD - US Dollar"),  # Tuple: first value is submitted; second is displayed.
        ],  # Close the choices list.
        initial="USD",  # Set the initial value for an unbound form.
        widget=forms.Select(  # Choose an HTML dropdown widget.
            attrs={  # Dictionary: set dropdown attributes.
                "class": "form-select",  # Apply Bootstrap dropdown styling.
                "id": "id_currency",  # Set the dropdown's HTML ID.
            }  # Close the attributes.
        ),  # Close the dropdown widget.
        help_text=(  # Start the original currency explanation.
            "Alpaca US-equity market prices are currently "  # First part of the explanation.
            "processed in US dollars by MarketPulse."  # Finish the explanation.
        ),  # Close the help-text expression.
    )  # Close the currency field.

    # --------------------------------------------------------
    # 2.3 TRADING CAPITAL / PORTFOLIO VALUE
    # --------------------------------------------------------
    trading_capital = forms.DecimalField(  # Define a numeric field cleaned into a Decimal value.
        label="Trading Capital / Portfolio Value",  # Set the field label.
        min_value=1,  # Server-side validation: require a value of at least one.
        max_digits=14,  # Allow up to 14 digits in total.
        decimal_places=2,  # Allow at most two decimal places.
        initial=10000,  # Set the initial capital value.
        widget=forms.NumberInput(  # Render an HTML numeric input.
            attrs={  # Configure its HTML attributes.
                "class": "form-control",  # Apply Bootstrap styling.
                "id": "id_trading_capital",  # Set the control ID.
                "step": "0.01",  # Set the browser's numeric step.
                "min": "1",  # Set the browser's minimum-value constraint.
                "placeholder": "Example: 10000",  # Display an example when empty.
            }  # Close the attributes dictionary.
        ),  # Close the numeric widget.
        help_text=(  # Start the original capital explanation.
            "Total simulated capital available for trading. "  # Describe the input.
            "This is not automatically the amount invested "  # Continue the explanation.
            "in the selected asset."  # Finish the explanation.
        ),  # Close the help text.
    )  # Close the capital field.

    # --------------------------------------------------------
    # 2.4 MAXIMUM RISK PER TRADE
    # --------------------------------------------------------
    # Input 1 represents 1%; conversion belongs in calculator code.
    risk_percentage = forms.DecimalField(  # Define the maximum-risk percentage input.
        label="Maximum Risk per Trade (%)",  # Set the displayed label.
        min_value=0.01,  # Require at least 0.01 percent.
        max_value=100,  # Allow no more than 100 percent.
        max_digits=6,  # Allow up to six digits in total.
        decimal_places=2,  # Allow at most two decimal places.
        initial=1,  # Initially display one percent.
        widget=forms.NumberInput(  # Choose a numeric HTML widget.
            attrs={  # Configure browser attributes.
                "class": "form-control",  # Apply Bootstrap styling.
                "id": "id_risk_percentage",  # Set the input ID.
                "step": "0.1",  # Preserve the original browser step.
                "min": "0.01",  # Set the browser minimum.
                "max": "100",  # Set the browser maximum.
                "placeholder": "Example: 1",  # Display the original example.
            }  # Close the attributes dictionary.
        ),  # Close the numeric widget.
        help_text=(  # Start the original risk explanation.
            "Percentage of trading capital that may be lost "  # Describe the risk budget.
            "if the planned stop-loss is reached. "  # Continue the explanation.
            "For example, entering 1 means 1%."  # Explain the input's units.
        ),  # Close the help text.
    )  # Close the risk-percentage field.

    # --------------------------------------------------------
    # 2.5 TRADE DIRECTION
    # --------------------------------------------------------
    direction = forms.ChoiceField(  # Define the allowed trade directions.
        label="Trade Direction",  # Set the displayed label.
        choices=[  # List: contain direction value/label tuples.
            ("long", "Long - price expected to rise"),  # Submit long for this option.
            ("short", "Short - price expected to fall"),  # Submit short for this option.
        ],  # Close the choices list.
        initial="long",  # Set the initial direction.
        widget=forms.Select(  # Render a dropdown.
            attrs={  # Configure its HTML attributes.
                "class": "form-select",  # Apply Bootstrap dropdown styling.
                "id": "id_direction",  # Set the control ID.
            }  # Close the attribute dictionary.
        ),  # Close the dropdown widget.
        help_text=(  # Start the original direction explanation.
            "Long positions normally place the stop below "  # Explain the long stop relationship.
            "entry. Short positions normally place the stop "  # Continue with the short relationship.
            "above entry."  # Finish the explanation.
        ),  # Close the help text.
    )  # Close the direction field.

    # --------------------------------------------------------
    # 2.6 PLANNED ENTRY PRICE
    # --------------------------------------------------------
    # When blank, the view obtains a price before calculating.
    entry_price = forms.DecimalField(  # Define the optional price of one share or unit.
        label="Planned Entry Price",  # Set the displayed label.
        required=False,  # Allow an empty input, cleaned as None.
        min_value=0.0001,  # Set the minimum accepted price.
        max_digits=14,  # Allow up to 14 digits in total.
        decimal_places=4,  # Allow at most four decimal places.
        widget=forms.NumberInput(  # Choose the numeric widget.
            attrs={  # Configure the HTML attributes.
                "class": "form-control",  # Apply Bootstrap styling.
                "id": "id_entry_price",  # Set the control ID.
                "step": "0.0001",  # Set the browser step.
                "min": "0.0001",  # Set the browser minimum.
                "placeholder": (  # Start the original placeholder.
                    "Leave blank to use the latest "  # First part of the placeholder.
                    "Alpaca market price"  # Finish the placeholder.
                ),  # Close the placeholder expression.
            }  # Close the attributes dictionary.
        ),  # Close the numeric widget.
        help_text=(  # Start the original entry-price explanation.
            "The assumed price of one share or unit when the "  # Describe the input.
            "hypothetical trade begins. Leave blank to use "  # Explain the blank-input workflow.
            "Alpaca's latest available market price."  # Finish the explanation.
        ),  # Close the help text.
    )  # Close the entry-price field.

    # --------------------------------------------------------
    # 2.7 STOP-LOSS METHOD
    # --------------------------------------------------------
    stop_method = forms.ChoiceField(  # Define the supported stop-method choices.
        label="Stop-Loss Method",  # Set the displayed label.
        choices=[  # List: contain three method value/label tuples.
            ("percentage", "Custom Percentage"),  # Submit percentage for this option.
            ("atr", "ATR-Based"),  # Submit atr for this option.
            ("fixed", "Fixed Stop Price"),  # Submit fixed for this option.
        ],  # Close the choices list.
        initial="percentage",  # Set the initial stop method.
        widget=forms.Select(  # Choose a dropdown widget.
            attrs={  # Define its HTML attributes.
                "class": "form-select",  # Apply Bootstrap styling.
                "id": "id_stop_method",  # Set the dropdown ID.
            }  # Close the attributes dictionary.
        ),  # Close the dropdown widget.
        help_text=(  # Start the original stop-method explanation.
            "Choose whether the stop-loss is calculated "  # First part of the explanation.
            "using a percentage, historical ATR, or an exact "  # List the supported approaches.
            "price."  # Finish the explanation.
        ),  # Close the help text.
    )  # Close the stop-method field.

    # --------------------------------------------------------
    # 2.8 PERCENTAGE STOP DISTANCE
    # --------------------------------------------------------
    stop_loss_percentage = forms.DecimalField(  # Define the percentage-distance input.
        label="Stop-Loss Distance (%)",  # Set the displayed label.
        required=False,  # Make it optional at field level; clean() requires it for percentage stops.
        min_value=0.01,  # Set the minimum percentage.
        max_value=100,  # Set the maximum percentage.
        max_digits=6,  # Allow up to six digits in total.
        decimal_places=2,  # Allow at most two decimal places.
        initial=5,  # Initially display five percent.
        widget=forms.NumberInput(  # Choose the numeric widget.
            attrs={  # Configure HTML attributes.
                "class": "form-control",  # Apply Bootstrap styling.
                "id": "id_stop_loss_percentage",  # Set the input ID.
                "step": "0.1",  # Preserve the original browser step.
                "min": "0.01",  # Set the browser minimum.
                "max": "100",  # Set the browser maximum.
                "placeholder": "Example: 5",  # Display the original example.
            }  # Close the attributes dictionary.
        ),  # Close the widget.
        help_text=(  # Start the original stop-distance explanation.
            "Example: entering 5 positions the stop "  # Describe the example input.
            "approximately 5% away from the entry price."  # Explain its percentage meaning.
        ),  # Close the help text.
    )  # Close the percentage-distance field.

    # --------------------------------------------------------
    # 2.9 ATR MULTIPLIER
    # --------------------------------------------------------
    atr_multiplier = forms.DecimalField(  # Define the multiplier applied to historical ATR by calculator code.
        label="ATR Multiplier",  # Set the displayed label.
        required=False,  # Make it optional at field level; clean() requires it for ATR stops.
        min_value=0.1,  # Set the minimum multiplier.
        max_value=20,  # Set the maximum multiplier.
        max_digits=6,  # Allow up to six digits in total.
        decimal_places=2,  # Allow at most two decimal places.
        initial=2,  # Initially display a multiplier of two.
        widget=forms.NumberInput(  # Choose the numeric widget.
            attrs={  # Define its HTML attributes.
                "class": "form-control",  # Apply Bootstrap styling.
                "id": "id_atr_multiplier",  # Set the control ID.
                "step": "0.1",  # Set the browser step.
                "min": "0.1",  # Set the browser minimum.
                "max": "20",  # Set the browser maximum.
                "placeholder": "Example: 2",  # Display an example multiplier.
            }  # Close the attributes dictionary.
        ),  # Close the widget.
        help_text=(  # Start the original ATR explanation.
            "ATR means Average True Range. "  # Explain the abbreviation.
            "For example, entering 2 uses a stop distance "  # Describe the multiplier example.
            "approximately equal to 2 × the 14-day ATR."  # Finish the explanation.
        ),  # Close the help text.
    )  # Close the ATR-multiplier field.

    # --------------------------------------------------------
    # 2.10 FIXED STOP PRICE
    # --------------------------------------------------------
    stop_price = forms.DecimalField(  # Define an exact stop-price input.
        label="Fixed Stop Price",  # Set the displayed label.
        required=False,  # Make it optional at field level; clean() requires it for fixed stops.
        min_value=0.0001,  # Set the minimum accepted price.
        max_digits=14,  # Allow up to 14 digits in total.
        decimal_places=4,  # Allow at most four decimal places.
        widget=forms.NumberInput(  # Choose the numeric widget.
            attrs={  # Define HTML attributes.
                "class": "form-control",  # Apply Bootstrap styling.
                "id": "id_stop_price",  # Set the control ID.
                "step": "0.0001",  # Set the browser step.
                "min": "0.0001",  # Set the browser minimum.
                "placeholder": "Example: 95.00",  # Display the original example.
            }  # Close the attributes dictionary.
        ),  # Close the widget.
        help_text=(  # Start the original fixed-stop explanation.
            "Enter the exact planned stop price when using "  # Describe the required input.
            "the Fixed Stop Price method."  # Identify the relevant method.
        ),  # Close the help text.
    )  # Close the fixed-stop field.

    # --------------------------------------------------------
    # 2.11 OPTIONAL PROFIT TARGET
    # --------------------------------------------------------
    target_price = forms.DecimalField(  # Define the optional favourable exit-price input.
        label="Profit Target (Optional)",  # Set the displayed label.
        required=False,  # Allow an empty target.
        min_value=0.0001,  # Set the minimum accepted target price.
        max_digits=14,  # Allow up to 14 digits in total.
        decimal_places=4,  # Allow at most four decimal places.
        widget=forms.NumberInput(  # Choose the numeric widget.
            attrs={  # Define HTML attributes.
                "class": "form-control",  # Apply Bootstrap styling.
                "id": "id_target_price",  # Set the control ID.
                "step": "0.0001",  # Set the browser step.
                "min": "0.0001",  # Set the browser minimum.
                "placeholder": "Example: 110.00",  # Display the original example.
            }  # Close the attributes dictionary.
        ),  # Close the widget.
        help_text=(  # Start the original target explanation.
            "Optional favourable exit price. If entered, "  # Explain that the input is optional.
            "MarketPulse calculates potential reward and the "  # Describe the later calculation.
            "reward-to-risk ratio."  # Finish the explanation.
        ),  # Close the help text.
    )  # Close the target-price field.

    # ========================================================
    # 3. SYMBOL CLEANING
    # ========================================================
    def clean_symbol(self):  # Method: Django calls this after the symbol field passes its standard validation.
        """Normalise symbol text; external symbol checks belong elsewhere."""  # Method documentation.
        symbol = self.cleaned_data["symbol"].strip().upper()  # Dictionary lookup and method chaining: trim and uppercase the symbol.
        if not symbol:  # Boolean negation: detect an empty normalised value.
            raise forms.ValidationError(  # Raise an exception that Django records as a field error.
                "Select an asset from the Alpaca search results."  # Preserve the original error message.
            )  # Close the ValidationError constructor.
        return symbol  # Return the normalised value to replace the cleaned symbol.

    # ========================================================
    # 4. COMPLETE FORM VALIDATION
    # ========================================================
    def clean(self):  # Override: define checks involving multiple form fields.
        """Require the selected stop input and check explicit entry-price relationships."""  # Method documentation.
        cleaned_data = super().clean()  # Inheritance: call the parent clean() method and obtain cleaned values.

        # ----------------------------------------------------
        # 4.1 READ CLEANED VALUES
        # ----------------------------------------------------
        stop_method = cleaned_data.get("stop_method")  # Dictionary lookup: read the method, or None if absent.
        direction = cleaned_data.get("direction")  # Read the cleaned long/short choice.
        entry_price = cleaned_data.get("entry_price")  # Read the optional entry Decimal value.
        stop_price = cleaned_data.get("stop_price")  # Read the optional fixed-stop Decimal value.
        target_price = cleaned_data.get("target_price")  # Read the optional target Decimal value.

        # ----------------------------------------------------
        # 4.2 REQUIRE THE PERCENTAGE STOP INPUT
        # ----------------------------------------------------
        if stop_method == "percentage" and cleaned_data.get("stop_loss_percentage") is None:  # Equality and Boolean AND: detect a missing percentage input for this method.
            self.add_error(  # Method call: attach an error to the relevant field.
                "stop_loss_percentage",  # Identify the field receiving the error.
                (  # Start the original combined error string.
                    "Enter a stop-loss percentage when "  # First part of the message.
                    "using the Custom Percentage method."  # Adjacent string: finish the message.
                ),  # Close the message expression.
            )  # Close the add_error() call.

        # ----------------------------------------------------
        # 4.3 REQUIRE THE ATR MULTIPLIER
        # ----------------------------------------------------
        if stop_method == "atr" and cleaned_data.get("atr_multiplier") is None:  # Check for a missing multiplier when ATR is selected.
            self.add_error(  # Attach a field-specific error.
                "atr_multiplier",  # Identify the multiplier field.
                (  # Start the original error message.
                    "Enter an ATR multiplier when "  # First part of the message.
                    "using the ATR-Based method."  # Finish the message.
                ),  # Close the message expression.
            )  # Close the error call.

        # ----------------------------------------------------
        # 4.4 REQUIRE THE FIXED STOP PRICE
        # ----------------------------------------------------
        if stop_method == "fixed" and stop_price is None:  # Check for a missing price when fixed stops are selected.
            self.add_error(  # Attach a field-specific error.
                "stop_price",  # Identify the fixed-stop field.
                (  # Start the original error message.
                    "Enter a fixed stop price when "  # First part of the message.
                    "using the Fixed Stop Price method."  # Finish the message.
                ),  # Close the message expression.
            )  # Close the error call.

        # ----------------------------------------------------
        # 4.5 VALIDATE FIXED STOP DIRECTION
        # ----------------------------------------------------
        # Without an explicit entry, these comparisons are deferred
        # to later calculator validation after the view obtains a price.
        if stop_method == "fixed" and entry_price is not None and stop_price is not None:  # Require a fixed method and both prices before comparing them.
            if direction == "long" and stop_price >= entry_price:  # Comparison: a long stop must be strictly below entry.
                self.add_error(  # Attach an invalid-long-stop error.
                    "stop_price",  # Identify the affected field.
                    (  # Start the original error message.
                        "For a long position, the fixed "  # First part of the message.
                        "stop price must be below the "  # State the required relationship.
                        "entry price."  # Finish the message.
                    ),  # Close the message expression.
                )  # Close the error call.
            if direction == "short" and stop_price <= entry_price:  # Comparison: a short stop must be strictly above entry.
                self.add_error(  # Attach an invalid-short-stop error.
                    "stop_price",  # Identify the affected field.
                    (  # Start the original error message.
                        "For a short position, the fixed "  # First part of the message.
                        "stop price must be above the "  # State the required relationship.
                        "entry price."  # Finish the message.
                    ),  # Close the message expression.
                )  # Close the error call.

        # ----------------------------------------------------
        # 4.6 VALIDATE PROFIT TARGET DIRECTION
        # ----------------------------------------------------
        if entry_price is not None and target_price is not None:  # Compare only when both cleaned prices are available.
            if direction == "long" and target_price <= entry_price:  # Comparison: a long target must be strictly above entry.
                self.add_error(  # Attach an invalid-long-target error.
                    "target_price",  # Identify the affected field.
                    (  # Start the original error message.
                        "For a long position, the profit "  # First part of the message.
                        "target must be above the entry price."  # State the required relationship.
                    ),  # Close the message expression.
                )  # Close the error call.
            if direction == "short" and target_price >= entry_price:  # Comparison: a short target must be strictly below entry.
                self.add_error(  # Attach an invalid-short-target error.
                    "target_price",  # Identify the affected field.
                    (  # Start the original error message.
                        "For a short position, the profit "  # First part of the message.
                        "target must be below the entry price."  # State the required relationship.
                    ),  # Close the message expression.
                )  # Close the error call.

        return cleaned_data  # Return the cleaned dictionary; errors remain attached to the form.