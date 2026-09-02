"""
============================================================
MARKETPULSE - RISK MANAGEMENT FORMS
============================================================

Framework mapping:

Alpaca Asset Universe
        ↓
MarketPulse Django API
        ↓
RiskPlannerForm
        ↓
risk_management/views.py
        ↓
Alpaca latest market snapshot
        +
Historical MarketData
        ↓
risk_management/calculators.py
        ↓
Trade & Portfolio Risk Results


PURPOSE:

This form collects the information required by the
MarketPulse Trade & Portfolio Risk Planner.

The Risk workflow is designed around:

1. Search the Alpaca asset universe
2. Select a valid market symbol
3. Retrieve the latest Alpaca market information
4. Define simulated trading capital
5. Define maximum acceptable risk
6. Define trade direction
7. Use a live/latest or custom entry price
8. Select a stop-loss methodology
9. Optionally define a profit target
10. Calculate a risk-constrained position

IMPORTANT:

This form does NOT communicate directly with Alpaca.

The browser will call MarketPulse Django API endpoints.

Those endpoints communicate with the Alpaca service layer.

This separation means the Alpaca API key and secret remain
securely on the Django server and are never exposed to the
browser.

============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

from django import forms


# ============================================================
# 2. TRADE & PORTFOLIO RISK PLANNER FORM
# ============================================================

class RiskPlannerForm(forms.Form):
    """
    ============================================================
    TRADE & PORTFOLIO RISK PLANNER
    ============================================================

    This form is responsible for:

    - collecting user inputs
    - validating those inputs
    - providing clear field labels
    - providing explanatory help text
    - applying Bootstrap form styling
    - normalising the selected stock symbol

    The form does NOT perform the final financial calculations.

    The actual calculations remain in:

        risk_management/calculators.py

    Alpaca communication remains in:

        data_management/services/alpaca.py

    ============================================================
    """


    # ========================================================
    # 2.1 ALPACA ASSET / SYMBOL SEARCH
    # ========================================================

    # Previously this field was a ChoiceField populated from:
    #
    # core.MarketData
    #
    # This meant that if MarketPulse only contained:
    #
    # AAPL
    # MSFT
    #
    # then those were the only two assets available on the
    # Risk page.
    #
    # The field is now a CharField because the frontend will
    # provide an autocomplete search connected to Alpaca's
    # active US-equity asset universe.
    #
    # Example workflow:
    #
    # User types:
    #
    # Microsoft
    #
    #        ↓
    #
    # MarketPulse API searches Alpaca
    #
    #        ↓
    #
    # MSFT - Microsoft Corporation - NASDAQ
    #
    #        ↓
    #
    # User selects MSFT
    #
    #        ↓
    #
    # The final value submitted by this form is:
    #
    # MSFT
    symbol = forms.CharField(
        label="Asset / Symbol",
        required=True,
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_symbol",
                "placeholder": (
                    "Search symbol or company, "
                    "for example AAPL or Microsoft"
                ),
                "autocomplete": "off",
                "spellcheck": "false",
            }
        ),
        help_text=(
            "Search Alpaca's active US-equity universe by "
            "ticker symbol or company name, then select an "
            "asset from the search results."
        ),
    )


    # ========================================================
    # 2.2 MARKET CURRENCY
    # ========================================================

    # Alpaca US-equity market prices are represented in USD.
    #
    # The previous version allowed:
    #
    # USD
    # EUR
    # GBP
    # CHF
    #
    # but MarketPulse did NOT actually perform an FX
    # conversion.
    #
    # This could produce a misleading result such as:
    #
    # AAPL market price = 230 USD
    #
    # while the interface simply labelled that value:
    #
    # 230 CHF
    #
    # That would be incorrect.
    #
    # Therefore the Risk Planner currently uses USD only.
    #
    # Proper multi-currency portfolio conversion can be added
    # later using an FX-rate service.
    currency = forms.ChoiceField(
        label="Market Currency",
        choices=[
            (
                "USD",
                "USD - US Dollar",
            ),
        ],
        initial="USD",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_currency",
            }
        ),
        help_text=(
            "Alpaca US-equity market prices are currently "
            "processed in US dollars by MarketPulse."
        ),
    )


    # ========================================================
    # 2.3 TRADING CAPITAL / PORTFOLIO VALUE
    # ========================================================

    # This is the total hypothetical amount available to the
    # simulated trading account.
    #
    # Example:
    #
    # Trading Capital = 10,000
    #
    # This DOES NOT mean:
    #
    # Buy 10,000 worth of AAPL.
    #
    # MarketPulse uses this value together with the selected
    # risk percentage and stop distance to determine a
    # risk-constrained position size.
    trading_capital = forms.DecimalField(
        label="Trading Capital / Portfolio Value",
        min_value=1,
        max_digits=14,
        decimal_places=2,
        initial=10000,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_trading_capital",
                "step": "0.01",
                "min": "1",
                "placeholder": "Example: 10000",
            }
        ),
        help_text=(
            "Total simulated capital available for trading. "
            "This is not automatically the amount invested "
            "in the selected asset."
        ),
    )


    # ========================================================
    # 2.4 MAXIMUM RISK PER TRADE
    # ========================================================

    # Example:
    #
    # Trading capital = 10,000
    #
    # Risk percentage = 1
    #
    # Maximum planned risk:
    #
    # 10,000 × 1%
    #
    # =
    #
    # 100
    #
    # Therefore entering:
    #
    # 1
    #
    # means:
    #
    # 1%
    #
    # and NOT:
    #
    # 1 USD.
    risk_percentage = forms.DecimalField(
        label="Maximum Risk per Trade (%)",
        min_value=0.01,
        max_value=100,
        max_digits=6,
        decimal_places=2,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_risk_percentage",
                "step": "0.1",
                "min": "0.01",
                "max": "100",
                "placeholder": "Example: 1",
            }
        ),
        help_text=(
            "Percentage of trading capital that may be lost "
            "if the planned stop-loss is reached. "
            "For example, entering 1 means 1%."
        ),
    )


    # ========================================================
    # 2.5 TRADE DIRECTION
    # ========================================================

    # Long:
    #
    # The hypothetical trade benefits if the market price
    # rises.
    #
    # Short:
    #
    # The hypothetical trade benefits if the market price
    # falls.
    direction = forms.ChoiceField(
        label="Trade Direction",
        choices=[
            (
                "long",
                "Long - price expected to rise",
            ),
            (
                "short",
                "Short - price expected to fall",
            ),
        ],
        initial="long",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_direction",
            }
        ),
        help_text=(
            "Long positions normally place the stop below "
            "entry. Short positions normally place the stop "
            "above entry."
        ),
    )


    # ========================================================
    # 2.6 PLANNED ENTRY PRICE
    # ========================================================

    # Entry price means:
    #
    # Price of ONE share/unit.
    #
    # Example:
    #
    # MSFT entry price = 500
    #
    # This does NOT mean:
    #
    # The user is investing only 500.
    #
    # If MarketPulse calculates:
    #
    # Quantity = 10
    #
    # then:
    #
    # Position Value
    #
    # =
    #
    # 10 × 500
    #
    # =
    #
    # 5,000
    #
    #
    # The field is optional.
    #
    # When blank, the view should attempt:
    #
    # 1. Alpaca latest trade price
    #
    # and if unavailable:
    #
    # 2. Most recently stored historical MarketData close
    #
    # and if neither exists:
    #
    # 3. Ask the user for a manual price.
    entry_price = forms.DecimalField(
        label="Planned Entry Price",
        required=False,
        min_value=0.0001,
        max_digits=14,
        decimal_places=4,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_entry_price",
                "step": "0.0001",
                "min": "0.0001",
                "placeholder": (
                    "Leave blank to use the latest "
                    "Alpaca market price"
                ),
            }
        ),
        help_text=(
            "The assumed price of one share or unit when the "
            "hypothetical trade begins. Leave blank to use "
            "Alpaca's latest available market price."
        ),
    )


    # ========================================================
    # 2.7 STOP-LOSS METHOD
    # ========================================================

    # MarketPulse supports three approaches.
    #
    # --------------------------------------------------------
    # CUSTOM PERCENTAGE
    # --------------------------------------------------------
    #
    # Example:
    #
    # Entry = 100
    # Stop distance = 5%
    #
    # Long stop:
    #
    # 95
    #
    #
    # --------------------------------------------------------
    # ATR BASED
    # --------------------------------------------------------
    #
    # Uses Average True Range calculated from historical:
    #
    # High
    # Low
    # Close
    #
    #
    # --------------------------------------------------------
    # FIXED STOP PRICE
    # --------------------------------------------------------
    #
    # User specifies the exact stop level.
    stop_method = forms.ChoiceField(
        label="Stop-Loss Method",
        choices=[
            (
                "percentage",
                "Custom Percentage",
            ),
            (
                "atr",
                "ATR-Based",
            ),
            (
                "fixed",
                "Fixed Stop Price",
            ),
        ],
        initial="percentage",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_stop_method",
            }
        ),
        help_text=(
            "Choose whether the stop-loss is calculated "
            "using a percentage, historical ATR, or an exact "
            "price."
        ),
    )


    # ========================================================
    # 2.8 PERCENTAGE STOP-LOSS DISTANCE
    # ========================================================

    # Example:
    #
    # Long trade:
    #
    # Entry = 100
    #
    # Stop distance = 5%
    #
    # Monetary distance:
    #
    # 100 × 5%
    #
    # =
    #
    # 5
    #
    # Stop:
    #
    # 100 - 5
    #
    # =
    #
    # 95
    stop_loss_percentage = forms.DecimalField(
        label="Stop-Loss Distance (%)",
        required=False,
        min_value=0.01,
        max_value=100,
        max_digits=6,
        decimal_places=2,
        initial=5,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_stop_loss_percentage",
                "step": "0.1",
                "min": "0.01",
                "max": "100",
                "placeholder": "Example: 5",
            }
        ),
        help_text=(
            "Example: entering 5 positions the stop "
            "approximately 5% away from the entry price."
        ),
    )


    # ========================================================
    # 2.9 ATR MULTIPLIER
    # ========================================================

    # ATR:
    #
    # Average True Range
    #
    # MarketPulse calculates this from historical OHLC data.
    #
    # Example:
    #
    # 14-day ATR = 3
    #
    # Multiplier = 2
    #
    # Stop distance:
    #
    # 3 × 2
    #
    # =
    #
    # 6
    #
    # This means more volatile assets can use a stop distance
    # that reflects recent historical price movement.
    atr_multiplier = forms.DecimalField(
        label="ATR Multiplier",
        required=False,
        min_value=0.1,
        max_value=20,
        max_digits=6,
        decimal_places=2,
        initial=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_atr_multiplier",
                "step": "0.1",
                "min": "0.1",
                "max": "20",
                "placeholder": "Example: 2",
            }
        ),
        help_text=(
            "ATR means Average True Range. "
            "For example, entering 2 uses a stop distance "
            "approximately equal to 2 × the 14-day ATR."
        ),
    )


    # ========================================================
    # 2.10 FIXED STOP PRICE
    # ========================================================

    # This field is used only when:
    #
    # Stop-Loss Method
    #
    # =
    #
    # Fixed Stop Price
    #
    #
    # Example:
    #
    # Long position
    #
    # Entry = 100
    #
    # Fixed Stop = 95
    #
    #
    # Risk per share:
    #
    # 100 - 95
    #
    # =
    #
    # 5
    stop_price = forms.DecimalField(
        label="Fixed Stop Price",
        required=False,
        min_value=0.0001,
        max_digits=14,
        decimal_places=4,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_stop_price",
                "step": "0.0001",
                "min": "0.0001",
                "placeholder": "Example: 95.00",
            }
        ),
        help_text=(
            "Enter the exact planned stop price when using "
            "the Fixed Stop Price method."
        ),
    )


    # ========================================================
    # 2.11 PROFIT TARGET
    # ========================================================

    # Profit Target is OPTIONAL.
    #
    # MarketPulse can calculate position size without it.
    #
    # If supplied, MarketPulse can additionally calculate:
    #
    # - potential reward per unit
    # - total potential reward
    # - reward-to-risk ratio
    #
    #
    # Example:
    #
    # Long entry = 100
    #
    # Stop = 95
    #
    # Target = 110
    #
    #
    # Risk per unit:
    #
    # 5
    #
    # Reward per unit:
    #
    # 10
    #
    # Reward / Risk:
    #
    # 10 / 5
    #
    # =
    #
    # 2 : 1
    target_price = forms.DecimalField(
        label="Profit Target (Optional)",
        required=False,
        min_value=0.0001,
        max_digits=14,
        decimal_places=4,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "id_target_price",
                "step": "0.0001",
                "min": "0.0001",
                "placeholder": "Example: 110.00",
            }
        ),
        help_text=(
            "Optional favourable exit price. If entered, "
            "MarketPulse calculates potential reward and the "
            "reward-to-risk ratio."
        ),
    )


    # ========================================================
    # 3. NORMALISE ALPACA SYMBOL
    # ========================================================

    def clean_symbol(self):
        """
        --------------------------------------------------------
        NORMALISE THE SELECTED MARKET SYMBOL
        --------------------------------------------------------

        The autocomplete interface will normally submit a
        ticker such as:

            aapl

        or:

            MsFt

        This method converts the submitted value into:

            AAPL

            MSFT

        Validation that the symbol genuinely exists at Alpaca
        belongs in the Alpaca service/view layer rather than
        inside this form.

        Keeping external API calls out of Django form
        validation makes the form more predictable and easier
        to test.
        --------------------------------------------------------
        """


        symbol = (
            self.cleaned_data[
                "symbol"
            ]
            .strip()
            .upper()
        )


        if not symbol:

            raise forms.ValidationError(
                "Select an asset from the Alpaca search results."
            )


        return symbol


    # ========================================================
    # 4. COMPLETE FORM VALIDATION
    # ========================================================

    def clean(self):
        """
        --------------------------------------------------------
        VALIDATE THE SELECTED RISK SETTINGS
        --------------------------------------------------------

        Only the field relevant to the chosen stop-loss method
        is required.

        Percentage:
            requires stop_loss_percentage

        ATR:
            requires atr_multiplier

        Fixed:
            requires stop_price

        Direction-specific stop and target relationships are
        also checked when an explicit entry price is supplied.

        If the entry price is blank, the final validation will
        occur after the view retrieves the latest Alpaca price.
        --------------------------------------------------------
        """


        cleaned_data = (
            super().clean()
        )


        # ----------------------------------------------------
        # Read values
        # ----------------------------------------------------

        stop_method = (
            cleaned_data.get(
                "stop_method"
            )
        )


        direction = (
            cleaned_data.get(
                "direction"
            )
        )


        entry_price = (
            cleaned_data.get(
                "entry_price"
            )
        )


        stop_price = (
            cleaned_data.get(
                "stop_price"
            )
        )


        target_price = (
            cleaned_data.get(
                "target_price"
            )
        )


        # ====================================================
        # 4.1 PERCENTAGE STOP VALIDATION
        # ====================================================

        if (
            stop_method == "percentage"
            and
            cleaned_data.get(
                "stop_loss_percentage"
            ) is None
        ):

            self.add_error(
                "stop_loss_percentage",
                (
                    "Enter a stop-loss percentage when "
                    "using the Custom Percentage method."
                ),
            )


        # ====================================================
        # 4.2 ATR STOP VALIDATION
        # ====================================================

        if (
            stop_method == "atr"
            and
            cleaned_data.get(
                "atr_multiplier"
            ) is None
        ):

            self.add_error(
                "atr_multiplier",
                (
                    "Enter an ATR multiplier when "
                    "using the ATR-Based method."
                ),
            )


        # ====================================================
        # 4.3 FIXED STOP VALIDATION
        # ====================================================

        if (
            stop_method == "fixed"
            and
            stop_price is None
        ):

            self.add_error(
                "stop_price",
                (
                    "Enter a fixed stop price when "
                    "using the Fixed Stop Price method."
                ),
            )


        # ====================================================
        # 4.4 FIXED STOP DIRECTION VALIDATION
        # ====================================================

        # This validation can happen here when the user has
        # manually entered the planned entry price.
        #
        # If entry_price is blank, risk_management/views.py
        # will first retrieve Alpaca's latest price and the
        # calculator will then perform the final validation.
        if (
            stop_method == "fixed"
            and
            entry_price is not None
            and
            stop_price is not None
        ):


            # ------------------------------------------------
            # LONG:
            # stop must be below entry
            # ------------------------------------------------

            if (
                direction == "long"
                and
                stop_price >= entry_price
            ):

                self.add_error(
                    "stop_price",
                    (
                        "For a long position, the fixed "
                        "stop price must be below the "
                        "entry price."
                    ),
                )


            # ------------------------------------------------
            # SHORT:
            # stop must be above entry
            # ------------------------------------------------

            if (
                direction == "short"
                and
                stop_price <= entry_price
            ):

                self.add_error(
                    "stop_price",
                    (
                        "For a short position, the fixed "
                        "stop price must be above the "
                        "entry price."
                    ),
                )


        # ====================================================
        # 4.5 TARGET PRICE VALIDATION
        # ====================================================

        # If a target exists and an explicit entry price was
        # entered, MarketPulse can validate the relationship
        # immediately.
        #
        # Long:
        #
        # target > entry
        #
        # Short:
        #
        # target < entry
        if (
            entry_price is not None
            and
            target_price is not None
        ):


            # ------------------------------------------------
            # LONG TARGET
            # ------------------------------------------------

            if (
                direction == "long"
                and
                target_price <= entry_price
            ):

                self.add_error(
                    "target_price",
                    (
                        "For a long position, the profit "
                        "target must be above the entry price."
                    ),
                )


            # ------------------------------------------------
            # SHORT TARGET
            # ------------------------------------------------

            if (
                direction == "short"
                and
                target_price >= entry_price
            ):

                self.add_error(
                    "target_price",
                    (
                        "For a short position, the profit "
                        "target must be below the entry price."
                    ),
                )


        return cleaned_data