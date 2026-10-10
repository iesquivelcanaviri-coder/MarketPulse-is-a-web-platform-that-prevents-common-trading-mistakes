"""
STRATEGY BUILDER - FORMS

Purpose:
Define inputs, widgets and validation for strategy creation,
historical backtesting and model-library entries.

Framework:
Template submits inputs -> view binds a form -> form validates.
StrategyCreateForm.save(user) creates a Strategy and two rules.
BacktestForm supplies cleaned inputs to the backtesting engine.
StrategyLibraryItemForm edits StrategyLibraryItem metadata.
"""

# ============================================================
# 1. IMPORTS
# ============================================================
from django import forms  # Import: I access Django's form classes, fields, widgets and validation errors.
from core.models import Strategy  # Model import: I use Strategy when saving a custom strategy.
from .models import (  # Relative import: I import models from this application.
    StrategyLibraryItem,  # Model class: I use this as the library form's database model.
    StrategyRule,  # Model class: I create the strategy's buy and sell rules.
)  # Closing parenthesis: I finish the grouped import.

# ============================================================
# 2. STRATEGY CREATION FORM
# ============================================================
class StrategyCreateForm(forms.Form):  # Class inheritance: I define a regular form with explicitly declared fields.
    """Validate inputs and create a moving-average crossover strategy."""

    # --------------------------------------------------------
    # 2.1 BASIC STRATEGY INFORMATION
    # --------------------------------------------------------
    name = forms.CharField(  # Class attribute and field: I define a required strategy-name input.
        max_length=120,  # Validation argument: I limit the name to 120 characters.
        widget=forms.TextInput(  # Widget construction: I render the field as a single-line text input.
            attrs={  # Dictionary: I define HTML attributes for the widget.
                "class": "form-control",  # Key-value pair: I apply Bootstrap input styling.
                "placeholder": "Example: Apple 10/30 MA Strategy",  # Hint text: I show an example without setting the field's value.
            }  # Closing brace: I finish the HTML-attribute dictionary.
        ),  # Closing call: I finish the text widget.
    )  # Closing call: I finish the name field.
    description = forms.CharField(  # Text field: I collect a strategy description.
        required=False,  # Boolean argument: I allow this field to be left empty.
        widget=forms.Textarea(  # Widget: I render a multiline text area.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
                "rows": 3,  # Integer attribute: I request three visible text rows.
                "placeholder": "Describe the purpose of this strategy.",  # String: I provide an input hint.
            }  # Closing brace: I finish the widget attributes.
        ),  # Closing call: I finish the text-area widget.
    )  # Closing call: I finish the description field.

    # --------------------------------------------------------
    # 2.2 MARKET SYMBOL
    # --------------------------------------------------------
    symbol = forms.CharField(  # Text field: I collect the strategy's asset ticker.
        max_length=20,  # Validation argument: I limit the symbol to 20 characters.
        initial="AAPL",  # Initial value: I display AAPL when the form is initially rendered.
        widget=forms.TextInput(  # Widget: I use a single-line text input.
            attrs={  # Dictionary: I configure the input's HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
                "placeholder": "AAPL",  # String: I show an example ticker as a hint.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the symbol widget.
        help_text=(  # Keyword argument: I provide guidance for the user.
            "Enter the market ticker used by the strategy, "  # String literal: I begin the guidance.
            "for example AAPL, MSFT or SPY."  # Adjacent string concatenation: Python joins this text to the preceding string.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the symbol field.

    # --------------------------------------------------------
    # 2.3 MOVING-AVERAGE PARAMETERS
    # --------------------------------------------------------
    fast_period = forms.IntegerField(  # Integer field: I collect the faster moving-average period.
        min_value=2,  # Validation limit: I require a value of at least two.
        initial=10,  # Initial value: I display ten observations as the starting setting.
        widget=forms.NumberInput(  # Widget: I render a numeric input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the numeric widget.
        help_text=(  # Keyword argument: I explain this parameter.
            "Number of observations used by the faster "  # String: I begin the explanation.
            "moving average."  # Adjacent string: I finish the explanation.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the fast-period field.
    slow_period = forms.IntegerField(  # Integer field: I collect the slower moving-average period.
        min_value=3,  # Validation limit: I require a value of at least three.
        initial=30,  # Initial value: I display thirty observations as the starting setting.
        widget=forms.NumberInput(  # Widget: I render a numeric input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the numeric widget.
        help_text=(  # Keyword argument: I explain this parameter.
            "Number of observations used by the slower "  # String: I begin the explanation.
            "moving average."  # Adjacent string: I finish the explanation.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the slow-period field.

    # --------------------------------------------------------
    # 2.4 RISK MANAGEMENT PARAMETERS
    # --------------------------------------------------------
    risk_per_trade = forms.DecimalField(  # Decimal field: I collect a fractional risk-per-trade value.
        min_value=0.001,  # Lower limit: I require at least 0.001.
        max_value=0.10,  # Upper limit: I allow at most 0.10.
        initial=0.01,  # Initial value: I display 0.01, representing 1%.
        decimal_places=3,  # Precision validation: I allow at most three decimal places.
        widget=forms.NumberInput(  # Widget: I render a numeric input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
                "step": "0.001",  # HTML attribute: I set the browser's numeric step.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the widget.
        help_text=(  # Keyword argument: I explain the fractional unit.
            "Fraction of capital risked per trade. "  # String: I describe what the input represents.
            "0.01 means 1%."  # Adjacent string: I provide a conversion example.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the risk-per-trade field.
    stop_loss_pct = forms.DecimalField(  # Decimal field: I collect the stop-loss fraction.
        min_value=0.005,  # Lower limit: I require at least 0.005.
        max_value=0.50,  # Upper limit: I allow at most 0.50.
        initial=0.05,  # Initial value: I display 0.05, representing 5%.
        decimal_places=3,  # Precision validation: I allow at most three decimal places.
        widget=forms.NumberInput(  # Widget: I render a numeric input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
                "step": "0.001",  # HTML attribute: I set a 0.001 numeric step.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the widget.
        help_text=(  # Keyword argument: I explain the input's units.
            "Stop-loss percentage expressed as a decimal. "  # String: I describe the expected format.
            "0.05 means 5%."  # Adjacent string: I provide an example.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the stop-loss field.

    # --------------------------------------------------------
    # 2.5 EXECUTION COST PARAMETERS
    # --------------------------------------------------------
    commission_pct = forms.DecimalField(  # Decimal field: I collect the simulated commission fraction.
        min_value=0,  # Lower limit: I allow zero commission.
        max_value=0.05,  # Upper limit: I allow at most 0.05.
        initial=0.001,  # Initial value: I display 0.001, representing 0.1%.
        decimal_places=4,  # Precision validation: I allow at most four decimal places.
        widget=forms.NumberInput(  # Widget: I render a numeric input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
                "step": "0.0001",  # HTML attribute: I set the browser's numeric step.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the widget.
        help_text=(  # Keyword argument: I explain the commission setting.
            "Simulated transaction commission. "  # String: I describe its purpose.
            "0.001 means 0.1%."  # Adjacent string: I explain the fractional value.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the commission field.
    slippage_pct = forms.DecimalField(  # Decimal field: I collect the simulated slippage fraction.
        min_value=0,  # Lower limit: I allow zero slippage.
        max_value=0.05,  # Upper limit: I allow at most 0.05.
        initial=0.0005,  # Initial value: I display 0.0005.
        decimal_places=4,  # Precision validation: I allow at most four decimal places.
        widget=forms.NumberInput(  # Widget: I render a numeric input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
                "step": "0.0001",  # HTML attribute: I set the browser's numeric step.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the widget.
        help_text=(  # Keyword argument: I explain where this setting is used.
            "Simulated slippage applied to backtest execution."  # String: I describe its purpose.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the slippage field.
    max_volume_pct = forms.DecimalField(  # Decimal field: I collect the simulated trading-volume limit.
        min_value=0.0001,  # Lower limit: I require at least 0.0001.
        max_value=0.10,  # Upper limit: I allow at most 0.10.
        initial=0.02,  # Initial value: I display 0.02.
        decimal_places=4,  # Precision validation: I allow at most four decimal places.
        widget=forms.NumberInput(  # Widget: I render a numeric input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
                "step": "0.0001",  # HTML attribute: I set the browser's numeric step.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the widget.
        help_text=(  # Keyword argument: I explain the volume constraint.
            "Maximum proportion of observed market volume that "  # String: I begin the explanation.
            "the simulation may attempt to trade."  # Adjacent string: I finish the explanation.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the volume-limit field.

    # --------------------------------------------------------
    # 2.6 DAILY LOSS LIMIT
    # --------------------------------------------------------
    max_daily_loss_pct = forms.DecimalField(  # Decimal field: I collect the backtest's daily-loss limit.
        min_value=0.001,  # Lower limit: I require at least 0.001.
        max_value=0.20,  # Upper limit: I allow at most 0.20.
        initial=0.03,  # Initial value: I display 0.03, representing 3%.
        decimal_places=3,  # Precision validation: I allow at most three decimal places.
        widget=forms.NumberInput(  # Widget: I render a numeric input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
                "step": "0.001",  # HTML attribute: I set the browser's numeric step.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the widget.
        help_text=(  # Keyword argument: I explain the setting.
            "Backtest discipline limit. "  # String: I identify its purpose.
            "0.03 means a maximum daily loss of 3%."  # Adjacent string: I explain the fractional value.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the daily-loss field.

    # --------------------------------------------------------
    # 2.7 CROSS-FIELD VALIDATION
    # --------------------------------------------------------
    def clean(self):  # Method override: I add validation involving more than one field.
        """Require the fast moving-average period to be shorter."""
        cleaned_data = super().clean()  # Inheritance and method call: I obtain the parent form's cleaned-data result.
        fast_period = cleaned_data.get("fast_period")  # Dictionary lookup: I retrieve the fast period or None if unavailable.
        slow_period = cleaned_data.get("slow_period")  # Dictionary lookup: I retrieve the slow period or None if unavailable.
        if (  # Conditional: I check that both values exist before comparing them.
            fast_period  # Truthiness check: I require a truthy fast-period value.
            and slow_period  # Logical AND: I also require a truthy slow-period value.
            and fast_period >= slow_period  # Comparison: I identify an invalid equal or longer fast period.
        ):  # Conditional boundary: I begin the error branch.
            raise forms.ValidationError(  # Exception raising: I report a form-wide validation error.
                (  # Grouping parentheses: I group the error message.
                    "Fast period must be smaller than "  # String: I begin the original message.
                    "slow period."  # Adjacent string: I finish the message.
                )  # Closing parenthesis: I finish grouping the message.
            )  # Closing call: I finish constructing the validation error.
        return cleaned_data  # Return statement: I provide the cleaned values to Django.

    # --------------------------------------------------------
    # 2.8 SAVE THE STRATEGY AND ITS RULES
    # --------------------------------------------------------
    def save(self, user):  # Custom method and parameters: I receive the user who will own the strategy.
        """Create a Strategy and its buy/sell moving-average rules."""

        # Standardise the symbol.
        symbol = (  # Variable assignment: I prepare the symbol for storage.
            self.cleaned_data["symbol"]  # Dictionary indexing: I read the validated symbol.
            .strip()  # String method: I remove surrounding whitespace.
            .upper()  # Method chaining: I convert the symbol to uppercase.
        )  # Closing parenthesis: I finish the symbol expression.

        # Collect risk and execution settings.
        configuration_fields = [  # List: I identify the cleaned fields to include in the strategy configuration.
            "risk_per_trade",  # String: I include the risk-per-trade setting.
            "stop_loss_pct",  # String: I include the stop-loss setting.
            "commission_pct",  # String: I include commission.
            "slippage_pct",  # String: I include slippage.
            "max_volume_pct",  # String: I include the volume limit.
            "max_daily_loss_pct",  # String: I include the daily-loss limit.
        ]  # Closing bracket: I finish the field-name list.
        rule_config = {  # Dictionary comprehension: I build a configuration dictionary from those fields.
            field_name: float(self.cleaned_data[field_name])  # Key-value expression: I convert each cleaned Decimal value to a float.
            for field_name in configuration_fields  # Iteration: I process each selected configuration field.
        }  # Closing brace: I finish the configuration dictionary.

        # Create the parent strategy.
        strategy = Strategy.objects.create(  # ORM method call: I create and save the Strategy record.
            user=user,  # Keyword argument: I assign the strategy's owner.
            name=self.cleaned_data["name"],  # Dictionary indexing: I use the validated name.
            description=self.cleaned_data["description"],  # Dictionary indexing: I use the validated description.
            rule_config=rule_config,  # Keyword argument: I store the prepared risk and execution configuration.
        )  # Closing call: I finish creating the strategy.

        # Prepare parameters shared by both rules.
        moving_average_parameters = {  # Dictionary: I collect the two moving-average periods.
            "fast_period": self.cleaned_data["fast_period"],  # Key-value pair: I store the validated fast period.
            "slow_period": self.cleaned_data["slow_period"],  # Key-value pair: I store the validated slow period.
        }  # Closing brace: I finish the shared parameters.

        # Create the buy rule.
        StrategyRule.objects.create(  # ORM method call: I create and save the entry rule.
            strategy=strategy,  # Relationship argument: I link this rule to the new strategy.
            name=(  # Keyword argument: I define a readable rule name.
                "IF fast MA crosses above "  # String: I describe the upward crossover.
                "slow MA THEN buy"  # Adjacent string: I describe the resulting buy action.
            ),  # Closing parenthesis: I finish the rule name.
            symbol=symbol,  # Keyword argument: I use the standardised asset symbol.
            condition_type="ma_cross_up",  # String code: I select the upward-crossover condition.
            action="buy",  # String code: I select the buy action.
            parameters=(moving_average_parameters),  # Dictionary reference: I supply the shared moving-average settings.
        )  # Closing call: I finish creating the buy rule.

        # Create the sell rule.
        StrategyRule.objects.create(  # ORM method call: I create and save the exit rule.
            strategy=strategy,  # Relationship argument: I link this rule to the same strategy.
            name=(  # Keyword argument: I define the readable exit-rule name.
                "IF fast MA crosses below "  # String: I describe the downward crossover.
                "slow MA THEN sell"  # Adjacent string: I describe the resulting sell action.
            ),  # Closing parenthesis: I finish the rule name.
            symbol=symbol,  # Keyword argument: I use the same standardised symbol.
            condition_type="ma_cross_down",  # String code: I select the downward-crossover condition.
            action="sell",  # String code: I select the sell action.
            parameters=(moving_average_parameters),  # Dictionary reference: I supply the same moving-average settings.
        )  # Closing call: I finish creating the sell rule.
        return strategy  # Return statement: I give the calling view the created strategy.

# ============================================================
# 3. HISTORICAL BACKTEST FORM
# ============================================================
class BacktestForm(forms.Form):  # Class inheritance: I define explicit inputs for a historical backtest.
    """Collect the historical period and starting simulated capital."""

    # --------------------------------------------------------
    # 3.1 START AND END DATES
    # --------------------------------------------------------
    start_date = forms.DateField(  # Date field: I validate and convert the starting date.
        widget=forms.DateInput(  # Widget: I render a date input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "type": "date",  # HTML input type: I request the browser's date-input interface.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the date widget.
    )  # Closing call: I finish the start-date field.
    end_date = forms.DateField(  # Date field: I validate and convert the ending date.
        widget=forms.DateInput(  # Widget: I render another date input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "type": "date",  # HTML input type: I request a date-input interface.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the date widget.
    )  # Closing call: I finish the end-date field.

    # --------------------------------------------------------
    # 3.2 INITIAL CAPITAL
    # --------------------------------------------------------
    initial_capital = forms.DecimalField(  # Decimal field: I collect the starting simulated capital.
        min_value=100,  # Validation limit: I require at least 100.
        initial=10000,  # Initial value: I display 10000 when initially rendering the form.
        widget=forms.NumberInput(  # Widget: I render a numeric input.
            attrs={  # Dictionary: I configure its HTML attributes.
                "class": "form-control",  # CSS class: I apply Bootstrap styling.
                "step": "100",  # HTML attribute: I set the browser's numeric step; this is not a server-side multiple-of-100 rule.
            }  # Closing brace: I finish the attributes.
        ),  # Closing call: I finish the widget.
        help_text=(  # Keyword argument: I explain this input.
            "Starting simulated capital for the historical backtest."  # String: I describe the capital setting.
        ),  # Closing parenthesis: I finish the help text.
    )  # Closing call: I finish the initial-capital field.

    # --------------------------------------------------------
    # 3.3 CROSS-FIELD DATE VALIDATION
    # --------------------------------------------------------
    def clean(self):  # Method override: I check the relationship between the two dates.
        """Require the end date to be later than the start date."""
        cleaned_data = super().clean()  # Parent method call: I obtain the cleaned values.
        start_date = cleaned_data.get("start_date")  # Dictionary lookup: I retrieve the start date if available.
        end_date = cleaned_data.get("end_date")  # Dictionary lookup: I retrieve the end date if available.
        if (  # Conditional: I compare the dates only when both are available.
            start_date  # Truthiness check: I require a start date.
            and end_date  # Logical AND: I also require an end date.
            and start_date >= end_date  # Comparison: I reject an equal or earlier end date.
        ):  # Conditional boundary: I begin the error branch.
            raise forms.ValidationError(  # Exception raising: I report a form-wide validation error.
                (  # Grouping parentheses: I group the message.
                    "End date must be after "  # String: I begin the original error message.
                    "start date."  # Adjacent string: I finish the message.
                )  # Closing parenthesis: I finish grouping the message.
            )  # Closing call: I finish constructing the error.
        return cleaned_data  # Return statement: I provide the cleaned values to Django.

# ============================================================
# 4. STRATEGY AND MODEL LIBRARY FORM
# ============================================================
class StrategyLibraryItemForm(forms.ModelForm):  # Class inheritance: I generate a form from the library model.
    """Edit library metadata; adding metadata does not implement a numerical engine."""

    # --------------------------------------------------------
    # 4.1 MODEL AND EDITABLE FIELDS
    # --------------------------------------------------------
    class Meta:  # Nested configuration class: I tell Django how to build this ModelForm.
        model = StrategyLibraryItem  # Class reference: I identify the database model represented by the form.
        fields = [  # List: I explicitly choose the editable fields and their order.
            "name",  # Field name: I include the model's readable name.
            "code",  # Field name: I include its internal identifier.
            "category",  # Field name: I include its model family.
            "description",  # Field name: I include how the model works.
            "purpose",  # Field name: I include why it might be used.
            "data_requirements",  # Field name: I include required data inputs.
            "default_parameters",  # Field name: I include default model settings.
            "output_type",  # Field name: I include the expected output description.
        ]  # Closing bracket: I finish the editable-field list.

        # ----------------------------------------------------
        # 4.2 FIELD WIDGETS
        # ----------------------------------------------------
        widgets = {  # Dictionary: I map each field name to its display widget.
            "name": forms.TextInput(  # Dictionary entry and widget: I render the name as a text input.
                attrs={  # Dictionary: I configure the widget's HTML attributes.
                    "class": "form-control",  # CSS class: I apply Bootstrap styling.
                    "placeholder": "Example: RSI Mean Reversion",  # String: I display an example name.
                }  # Closing brace: I finish the attributes.
            ),  # Closing call: I finish the name widget.
            "code": forms.TextInput(  # Widget: I render the internal code as a text input.
                attrs={  # Dictionary: I configure its HTML attributes.
                    "class": "form-control",  # CSS class: I apply Bootstrap styling.
                    "placeholder": "Example: rsi_mean_reversion",  # String: I display an example identifier.
                }  # Closing brace: I finish the attributes.
            ),  # Closing call: I finish the code widget.
            "category": forms.Select(  # Widget: I render model-category choices as a dropdown.
                attrs={  # Dictionary: I configure its HTML attributes.
                    "class": "form-select",  # CSS class: I apply Bootstrap dropdown styling.
                }  # Closing brace: I finish the attributes.
            ),  # Closing call: I finish the category widget.
            "description": forms.Textarea(  # Widget: I render a multiline description input.
                attrs={  # Dictionary: I configure its HTML attributes.
                    "class": "form-control",  # CSS class: I apply Bootstrap styling.
                    "rows": 4,  # Integer attribute: I request four visible text rows.
                    "placeholder": (  # String attribute: I begin a descriptive hint.
                        "Explain how the strategy or "  # String: I begin the hint text.
                        "model works."  # Adjacent string: I finish the hint.
                    ),  # Closing parenthesis: I finish the placeholder.
                }  # Closing brace: I finish the attributes.
            ),  # Closing call: I finish the description widget.
            "purpose": forms.Textarea(  # Widget: I render a multiline purpose input.
                attrs={  # Dictionary: I configure its HTML attributes.
                    "class": "form-control",  # CSS class: I apply Bootstrap styling.
                    "rows": 3,  # Integer attribute: I request three visible rows.
                    "placeholder": (  # String attribute: I begin the purpose hint.
                        "Explain why someone might use "  # String: I begin the hint.
                        "this model."  # Adjacent string: I finish the hint.
                    ),  # Closing parenthesis: I finish the placeholder.
                }  # Closing brace: I finish the attributes.
            ),  # Closing call: I finish the purpose widget.
            "data_requirements": forms.Textarea(  # Widget: I provide a multiline input for JSON requirements.
                attrs={  # Dictionary: I configure its HTML attributes.
                    "class": "form-control",  # CSS class: I apply Bootstrap styling.
                    "rows": 3,  # Integer attribute: I request three visible rows.
                    "placeholder": (  # String attribute: I begin an example JSON list.
                        '["close_price", '  # Python string: I include JSON double quotes inside single quotes.
                        '"volume"]'  # Adjacent string: I complete the example list.
                    ),  # Closing parenthesis: I finish the placeholder.
                }  # Closing brace: I finish the attributes.
            ),  # Closing call: I finish the requirements widget.
            "default_parameters": forms.Textarea(  # Widget: I provide a multiline input for JSON parameters.
                attrs={  # Dictionary: I configure its HTML attributes.
                    "class": "form-control",  # CSS class: I apply Bootstrap styling.
                    "rows": 5,  # Integer attribute: I request five visible rows.
                    "placeholder": (  # String attribute: I begin an example JSON object.
                        '{"lookback": 20, '  # Python string: I begin the example parameter object.
                        '"threshold": 30}'  # Adjacent string: I complete the example object.
                    ),  # Closing parenthesis: I finish the placeholder.
                }  # Closing brace: I finish the attributes.
            ),  # Closing call: I finish the parameters widget.
            "output_type": forms.TextInput(  # Widget: I render the expected-output description as a text input.
                attrs={  # Dictionary: I configure its HTML attributes.
                    "class": "form-control",  # CSS class: I apply Bootstrap styling.
                    "placeholder": (  # String attribute: I begin an output example.
                        "Example: Buy/sell signals, "  # String: I begin the example.
                        "PnL and performance metrics"  # Adjacent string: I finish the example.
                    ),  # Closing parenthesis: I finish the placeholder.
                }  # Closing brace: I finish the attributes.
            ),  # Closing call: I finish the output widget.
        }  # Closing brace: I finish the widget dictionary.

        # ----------------------------------------------------
        # 4.3 FIELD HELP TEXT
        # ----------------------------------------------------
        help_texts = {  # Dictionary: I provide guidance for each library field.
            "name": (  # Dictionary entry: I define guidance for the model name.
                "Use a clear academic or commonly recognised "  # String: I begin the guidance.
                "name for the strategy/model."  # Adjacent string: I finish the guidance.
            ),  # Closing parenthesis: I finish the name help text.
            "code": (  # Dictionary entry: I define guidance for the internal code.
                "Unique internal code used by MarketPulse. "  # String: I describe the identifier's purpose.
                "Use lowercase letters, numbers, underscores "  # Adjacent string: I describe the expected characters.
                "or hyphens."  # Adjacent string: I finish the guidance.
            ),  # Closing parenthesis: I finish the code help text.
            "category": (  # Dictionary entry: I define category guidance.
                "Select the quantitative model family that "  # String: I begin the guidance.
                "best describes this item."  # Adjacent string: I finish the guidance.
            ),  # Closing parenthesis: I finish the category help text.
            "description": (  # Dictionary entry: I define description guidance.
                "Describe how the strategy or model works."  # String: I explain the expected content.
            ),  # Closing parenthesis: I finish the description help text.
            "purpose": (  # Dictionary entry: I define purpose guidance.
                "Explain what research or financial problem "  # String: I begin the guidance.
                "the model is designed to address."  # Adjacent string: I finish the guidance.
            ),  # Closing parenthesis: I finish the purpose help text.
            "data_requirements": (  # Dictionary entry: I explain the required JSON structure.
                "Enter a JSON list. Example: "  # String: I identify the expected structure.
                '["close_price", "volume"]'  # Adjacent string: I provide the original JSON-list example.
            ),  # Closing parenthesis: I finish the requirements help text.
            "default_parameters": (  # Dictionary entry: I explain the parameter structure.
                "Enter a JSON object. Example: "  # String: I identify the expected structure.
                '{"lookback": 20, "threshold": 30}'  # Adjacent string: I provide the original JSON-object example.
            ),  # Closing parenthesis: I finish the parameters help text.
            "output_type": (  # Dictionary entry: I explain the output description.
                "Describe what MarketPulse should eventually "  # String: I begin the guidance.
                "produce when the model is executed."  # Adjacent string: I finish the guidance.
            ),  # Closing parenthesis: I finish the output help text.
        }  # Closing brace: I finish the help-text dictionary.

    # --------------------------------------------------------
    # 4.4 STANDARDISE THE MODEL CODE
    # --------------------------------------------------------
    def clean_code(self):  # Field-specific cleaning method: Django calls this after the code field's validation.
        """Remove surrounding whitespace and lowercase the code."""
        code = (  # Variable assignment: I prepare the standardised identifier.
            self.cleaned_data["code"]  # Dictionary indexing: I read the cleaned code field.
            .strip()  # String method: I remove surrounding whitespace.
            .lower()  # Method chaining: I convert letters to lowercase.
        )  # Closing parenthesis: I finish the expression.
        return code  # Return statement: I supply the code's final cleaned value.

    # --------------------------------------------------------
    # 4.5 VALIDATE THE DATA-REQUIREMENTS STRUCTURE
    # --------------------------------------------------------
    def clean_data_requirements(self):  # Field-specific method: I check the parsed JSON requirements value.
        """Require a JSON list, or return an empty list for None."""
        data_requirements = self.cleaned_data.get("data_requirements")  # Dictionary lookup: I retrieve the parsed value.
        if data_requirements is None:  # Identity comparison: I check specifically for a missing value.
            return []  # Early return and list literal: I replace None with an empty list.
        if not isinstance(data_requirements, list):  # Type check and logical NOT: I reject values that are not lists.
            raise forms.ValidationError(  # Exception raising: I attach a validation error to this field.
                (  # Grouping parentheses: I group the error text.
                    "Data requirements must be a JSON list. "  # String: I explain the required type.
                    'Example: ["close_price", "volume"]'  # Adjacent string: I provide the original example.
                )  # Closing parenthesis: I finish grouping the message.
            )  # Closing call: I finish constructing the error.
        return data_requirements  # Return statement: I keep the accepted list unchanged.

    # --------------------------------------------------------
    # 4.6 VALIDATE THE DEFAULT-PARAMETERS STRUCTURE
    # --------------------------------------------------------
    def clean_default_parameters(self):  # Field-specific method: I check the parsed JSON parameters value.
        """Require a JSON object, or return an empty dictionary for None."""
        default_parameters = self.cleaned_data.get("default_parameters")  # Dictionary lookup: I retrieve the parsed value.
        if default_parameters is None:  # Identity comparison: I check specifically for a missing value.
            return {}  # Early return and dictionary literal: I replace None with an empty dictionary.
        if not isinstance(default_parameters, dict):  # Type check and logical NOT: I reject values that are not dictionaries.
            raise forms.ValidationError(  # Exception raising: I attach a validation error to this field.
                (  # Grouping parentheses: I group the error text.
                    "Default parameters must be a JSON object. "  # String: I explain the required type.
                    'Example: {"lookback": 20}'  # Adjacent string: I provide the original example.
                )  # Closing parenthesis: I finish grouping the message.
            )  # Closing call: I finish constructing the error.
        return default_parameters  # Return statement: I keep the accepted dictionary unchanged.