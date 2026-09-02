"""
============================================================
STRATEGY BUILDER - FORMS
============================================================

Framework mapping:

StrategyCreateForm
        ↓
core.Strategy
        ↓
StrategyRule
        ↓
Creates two IF / THEN moving-average rules


BacktestForm
        ↓
strategy_builder/backtesting.py
        ↓
Historical strategy simulation


StrategyLibraryItemForm
        ↓
StrategyLibraryItem
        ↓
Strategy & Model Library
        ↓
Strategies tab
        +
Data tab model selector


PURPOSE:

This file contains the forms used by the MarketPulse
Strategy Builder and Strategy Research functionality.

============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

from django import forms

from core.models import Strategy

from .models import (
    StrategyLibraryItem,
    StrategyRule,
)


# ============================================================
# 2. STRATEGY CREATE FORM
# ============================================================

class StrategyCreateForm(forms.Form):
    """
    ============================================================
    CUSTOM STRATEGY CREATION FORM
    ============================================================

    Framework mapping:

    User
        ↓
    StrategyCreateForm
        ↓
    core.Strategy
        ↓
    Two StrategyRule records

    The current custom strategy builder creates a moving-average
    crossover strategy consisting of:

    BUY:
        Fast moving average crosses above slow moving average.

    SELL:
        Fast moving average crosses below slow moving average.

    ============================================================
    """


    # ========================================================
    # 2.1 BASIC STRATEGY INFORMATION
    # ========================================================

    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Example: Apple 10/30 MA Strategy",
            }
        ),
    )


    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder":
                    "Describe the purpose of this strategy.",
            }
        ),
    )


    # ========================================================
    # 2.2 MARKET SYMBOL
    # ========================================================

    symbol = forms.CharField(
        max_length=20,
        initial="AAPL",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "AAPL",
            }
        ),
        help_text=(
            "Enter the market ticker used by the strategy, "
            "for example AAPL, MSFT or SPY."
        ),
    )


    # ========================================================
    # 2.3 MOVING-AVERAGE PARAMETERS
    # ========================================================

    fast_period = forms.IntegerField(
        min_value=2,
        initial=10,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
            }
        ),
        help_text=(
            "Number of observations used by the faster "
            "moving average."
        ),
    )


    slow_period = forms.IntegerField(
        min_value=3,
        initial=30,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
            }
        ),
        help_text=(
            "Number of observations used by the slower "
            "moving average."
        ),
    )


    # ========================================================
    # 2.4 RISK MANAGEMENT PARAMETERS
    # ========================================================

    risk_per_trade = forms.DecimalField(
        min_value=0.001,
        max_value=0.10,
        initial=0.01,
        decimal_places=3,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.001",
            }
        ),
        help_text=(
            "Fraction of capital risked per trade. "
            "0.01 means 1%."
        ),
    )


    stop_loss_pct = forms.DecimalField(
        min_value=0.005,
        max_value=0.50,
        initial=0.05,
        decimal_places=3,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.001",
            }
        ),
        help_text=(
            "Stop-loss percentage expressed as a decimal. "
            "0.05 means 5%."
        ),
    )


    # ========================================================
    # 2.5 EXECUTION COST PARAMETERS
    # ========================================================

    commission_pct = forms.DecimalField(
        min_value=0,
        max_value=0.05,
        initial=0.001,
        decimal_places=4,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.0001",
            }
        ),
        help_text=(
            "Simulated transaction commission. "
            "0.001 means 0.1%."
        ),
    )


    slippage_pct = forms.DecimalField(
        min_value=0,
        max_value=0.05,
        initial=0.0005,
        decimal_places=4,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.0001",
            }
        ),
        help_text=(
            "Simulated slippage applied to backtest execution."
        ),
    )


    max_volume_pct = forms.DecimalField(
        min_value=0.0001,
        max_value=0.10,
        initial=0.02,
        decimal_places=4,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.0001",
            }
        ),
        help_text=(
            "Maximum proportion of observed market volume that "
            "the simulation may attempt to trade."
        ),
    )


    # ========================================================
    # 2.6 DAILY LOSS LIMIT
    # ========================================================

    max_daily_loss_pct = forms.DecimalField(
        min_value=0.001,
        max_value=0.20,
        initial=0.03,
        decimal_places=3,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.001",
            }
        ),
        help_text=(
            "Backtest discipline limit. "
            "0.03 means a maximum daily loss of 3%."
        ),
    )


    # ========================================================
    # 2.7 FORM VALIDATION
    # ========================================================

    def clean(self):
        """
        Validate relationships between strategy parameters.
        """

        cleaned_data = super().clean()


        fast_period = cleaned_data.get(
            "fast_period"
        )


        slow_period = cleaned_data.get(
            "slow_period"
        )


        # ----------------------------------------------------
        # Fast moving average must be shorter than slow MA
        # ----------------------------------------------------

        if (
            fast_period
            and slow_period
            and fast_period >= slow_period
        ):

            raise forms.ValidationError(
                (
                    "Fast period must be smaller than "
                    "slow period."
                )
            )


        return cleaned_data


    # ========================================================
    # 2.8 SAVE STRATEGY
    # ========================================================

    def save(self, user):
        """
        Create the Strategy and its two moving-average
        crossover StrategyRule records.
        """


        # ----------------------------------------------------
        # Standardise market symbol
        # ----------------------------------------------------

        symbol = (
            self.cleaned_data["symbol"]
            .strip()
            .upper()
        )


        # ----------------------------------------------------
        # Build strategy risk/execution configuration
        # ----------------------------------------------------

        configuration_fields = [

            "risk_per_trade",
            "stop_loss_pct",
            "commission_pct",
            "slippage_pct",
            "max_volume_pct",
            "max_daily_loss_pct",

        ]


        rule_config = {

            field_name:
                float(
                    self.cleaned_data[
                        field_name
                    ]
                )

            for field_name in configuration_fields

        }


        # ----------------------------------------------------
        # Create Strategy
        # ----------------------------------------------------

        strategy = Strategy.objects.create(

            user=user,

            name=self.cleaned_data[
                "name"
            ],

            description=self.cleaned_data[
                "description"
            ],

            rule_config=rule_config,

        )


        # ----------------------------------------------------
        # Shared moving-average parameters
        # ----------------------------------------------------

        moving_average_parameters = {

            "fast_period":
                self.cleaned_data[
                    "fast_period"
                ],

            "slow_period":
                self.cleaned_data[
                    "slow_period"
                ],

        }


        # ----------------------------------------------------
        # BUY RULE
        # ----------------------------------------------------

        StrategyRule.objects.create(

            strategy=strategy,

            name=(
                "IF fast MA crosses above "
                "slow MA THEN buy"
            ),

            symbol=symbol,

            condition_type="ma_cross_up",

            action="buy",

            parameters=(
                moving_average_parameters
            ),

        )


        # ----------------------------------------------------
        # SELL RULE
        # ----------------------------------------------------

        StrategyRule.objects.create(

            strategy=strategy,

            name=(
                "IF fast MA crosses below "
                "slow MA THEN sell"
            ),

            symbol=symbol,

            condition_type="ma_cross_down",

            action="sell",

            parameters=(
                moving_average_parameters
            ),

        )


        return strategy


# ============================================================
# 3. BACKTEST FORM
# ============================================================

class BacktestForm(forms.Form):
    """
    ============================================================
    HISTORICAL BACKTEST FORM
    ============================================================

    Framework mapping:

    Historical MarketData
        +
    Strategy
        +
    BacktestForm
        ↓
    strategy_builder/backtesting.py
        ↓
    Backtest
        ↓
    BacktestTrade
        ↓
    Performance Metrics

    ============================================================
    """


    # ========================================================
    # 3.1 BACKTEST START DATE
    # ========================================================

    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )


    # ========================================================
    # 3.2 BACKTEST END DATE
    # ========================================================

    end_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )


    # ========================================================
    # 3.3 INITIAL CAPITAL
    # ========================================================

    initial_capital = forms.DecimalField(
        min_value=100,
        initial=10000,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "100",
            }
        ),
        help_text=(
            "Starting simulated capital for the historical backtest."
        ),
    )


    # ========================================================
    # 3.4 BACKTEST VALIDATION
    # ========================================================

    def clean(self):
        """
        Ensure the requested historical period is valid.
        """

        cleaned_data = super().clean()


        start_date = cleaned_data.get(
            "start_date"
        )


        end_date = cleaned_data.get(
            "end_date"
        )


        if (
            start_date
            and end_date
            and start_date >= end_date
        ):

            raise forms.ValidationError(
                (
                    "End date must be after "
                    "start date."
                )
            )


        return cleaned_data


# ============================================================
# 4. STRATEGY / MODEL LIBRARY FORM
# ============================================================

class StrategyLibraryItemForm(forms.ModelForm):
    """
    ============================================================
    ADD STRATEGY OR MODEL TO MARKETPULSE
    ============================================================

    Framework mapping:

    Strategies tab
        ↓
    Add Library Model
        ↓
    StrategyLibraryItemForm
        ↓
    StrategyLibraryItem
        ↓
    PostgreSQL
        ↓
    Strategy & Model Library
        ↓
    Data tab selector


    PURPOSE:

    This form allows additional quantitative strategies,
    financial models and analytical methods to be added to
    the MarketPulse Strategy & Model Library.

    For example:

    - RSI Mean Reversion
    - MACD Crossover
    - Donchian Breakout
    - Prophet Forecasting
    - CAPM
    - Another academic model added later


    IMPORTANT:

    Adding an item to the library does not automatically mean
    that MarketPulse has implemented its mathematical engine.

    New items should initially remain:

        Catalogued

    until their numerical implementation has genuinely been
    developed and tested.

    ============================================================
    """


    # ========================================================
    # 4.1 MODELFORM CONFIGURATION
    # ========================================================

    class Meta:

        model = StrategyLibraryItem


        # ----------------------------------------------------
        # Fields editable by normal form
        # ----------------------------------------------------

        fields = [

            "name",
            "code",
            "category",
            "description",
            "purpose",
            "data_requirements",
            "default_parameters",
            "output_type",

        ]


        # ====================================================
        # 4.2 FIELD WIDGETS
        # ====================================================

        widgets = {


            # ------------------------------------------------
            # Model Name
            # ------------------------------------------------

            "name": forms.TextInput(
                attrs={
                    "class":
                        "form-control",

                    "placeholder":
                        "Example: RSI Mean Reversion",
                }
            ),


            # ------------------------------------------------
            # Internal Model Code
            # ------------------------------------------------

            "code": forms.TextInput(
                attrs={
                    "class":
                        "form-control",

                    "placeholder":
                        "Example: rsi_mean_reversion",
                }
            ),


            # ------------------------------------------------
            # Category
            # ------------------------------------------------

            "category": forms.Select(
                attrs={
                    "class":
                        "form-select",
                }
            ),


            # ------------------------------------------------
            # Description
            # ------------------------------------------------

            "description": forms.Textarea(
                attrs={
                    "class":
                        "form-control",

                    "rows":
                        4,

                    "placeholder":
                        (
                            "Explain how the strategy or "
                            "model works."
                        ),
                }
            ),


            # ------------------------------------------------
            # Purpose
            # ------------------------------------------------

            "purpose": forms.Textarea(
                attrs={
                    "class":
                        "form-control",

                    "rows":
                        3,

                    "placeholder":
                        (
                            "Explain why someone might use "
                            "this model."
                        ),
                }
            ),


            # ------------------------------------------------
            # Data Requirements
            # ------------------------------------------------

            "data_requirements": forms.Textarea(
                attrs={
                    "class":
                        "form-control",

                    "rows":
                        3,

                    "placeholder":
                        (
                            '["close_price", '
                            '"volume"]'
                        ),
                }
            ),


            # ------------------------------------------------
            # Default Parameters
            # ------------------------------------------------

            "default_parameters": forms.Textarea(
                attrs={
                    "class":
                        "form-control",

                    "rows":
                        5,

                    "placeholder":
                        (
                            '{"lookback": 20, '
                            '"threshold": 30}'
                        ),
                }
            ),


            # ------------------------------------------------
            # Expected Output
            # ------------------------------------------------

            "output_type": forms.TextInput(
                attrs={
                    "class":
                        "form-control",

                    "placeholder":
                        (
                            "Example: Buy/sell signals, "
                            "PnL and performance metrics"
                        ),
                }
            ),

        }


        # ====================================================
        # 4.3 HELP TEXT
        # ====================================================

        help_texts = {


            "name":
                (
                    "Use a clear academic or commonly recognised "
                    "name for the strategy/model."
                ),


            "code":
                (
                    "Unique internal code used by MarketPulse. "
                    "Use lowercase letters, numbers, underscores "
                    "or hyphens."
                ),


            "category":
                (
                    "Select the quantitative model family that "
                    "best describes this item."
                ),


            "description":
                (
                    "Describe how the strategy or model works."
                ),


            "purpose":
                (
                    "Explain what research or financial problem "
                    "the model is designed to address."
                ),


            "data_requirements":
                (
                    "Enter a JSON list. Example: "
                    '["close_price", "volume"]'
                ),


            "default_parameters":
                (
                    "Enter a JSON object. Example: "
                    '{"lookback": 20, "threshold": 30}'
                ),


            "output_type":
                (
                    "Describe what MarketPulse should eventually "
                    "produce when the model is executed."
                ),

        }


    # ========================================================
    # 4.4 CLEAN MODEL CODE
    # ========================================================

    def clean_code(self):
        """
        Standardise the internal model code.

        Example:

            RSI_MEAN_REVERSION

        becomes:

            rsi_mean_reversion
        """

        code = (
            self.cleaned_data["code"]
            .strip()
            .lower()
        )


        return code


    # ========================================================
    # 4.5 VALIDATE DATA REQUIREMENTS
    # ========================================================

    def clean_data_requirements(self):
        """
        StrategyLibraryItem.data_requirements must contain
        a JSON list.

        Correct example:

        [
            "close_price",
            "volume"
        ]

        Incorrect example:

        {
            "close_price": true
        }
        """

        data_requirements = (
            self.cleaned_data.get(
                "data_requirements"
            )
        )


        if data_requirements is None:

            return []


        if not isinstance(
            data_requirements,
            list,
        ):

            raise forms.ValidationError(
                (
                    "Data requirements must be a JSON list. "
                    'Example: ["close_price", "volume"]'
                )
            )


        return data_requirements


    # ========================================================
    # 4.6 VALIDATE DEFAULT PARAMETERS
    # ========================================================

    def clean_default_parameters(self):
        """
        StrategyLibraryItem.default_parameters must contain
        a JSON object/dictionary.

        Correct:

        {
            "lookback": 20,
            "threshold": 30
        }

        Incorrect:

        [
            20,
            30
        ]
        """

        default_parameters = (
            self.cleaned_data.get(
                "default_parameters"
            )
        )


        if default_parameters is None:

            return {}


        if not isinstance(
            default_parameters,
            dict,
        ):

            raise forms.ValidationError(
                (
                    "Default parameters must be a JSON object. "
                    'Example: {"lookback": 20}'
                )
            )


        return default_parameters