"""
============================================================
MARKETPULSE - RISK MANAGEMENT VIEWS
============================================================

Framework mapping:

                    ALPACA
                       ↓
              Latest Market Price
                       ↓
                       │
                       │
Data tab              │
    ↓                 │
core.MarketData       │
    ↓                 │
Historical Context    │
    ↓                 │
    └────────────┬────┘
                 ↓
          RiskPlannerForm
                 ↓
       Risk Calculation Engine
                 ↓
           RiskSnapshot
                 ↓
       Risk Planner / Dashboard


PURPOSE:

The Risk module helps the user understand:

- Trading capital
- Maximum risk per trade
- Planned entry price
- Alpaca latest market price
- Stop-loss distance
- ATR-based stops
- Fixed stops
- Position sizing
- Capital allocation
- Potential loss
- Potential reward
- Reward-to-risk
- Historical volatility
- Historical drawdown

The module combines:

1. Alpaca current/latest market information
2. MarketPulse stored historical market data
3. MarketPulse quantitative risk calculations

This is an educational risk-planning tool.
It does not provide investment advice.
============================================================
"""


# ============================================================
# 1. PYTHON IMPORTS
# ============================================================

from decimal import Decimal


# ============================================================
# 2. DJANGO IMPORTS
# ============================================================

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# ============================================================
# 3. MARKETPULSE DATABASE IMPORTS
# ============================================================

# MarketData stores historical OHLCV observations imported
# through the MarketPulse Data tab.
#
# This import fixes:
#
# NameError:
# name 'MarketData' is not defined

from core.models import MarketData


# ============================================================
# 4. ALPACA SERVICE IMPORTS
# ============================================================

# The Risk view does NOT communicate with Alpaca directly
# through raw HTTP requests.
#
# Instead it uses the MarketPulse Alpaca service layer:
#
# risk_management/views.py
#         ↓
# data_management/services/alpaca.py
#         ↓
# Alpaca REST API
#
# This keeps external-provider logic separate from the
# Django page logic.

from data_management.services.alpaca import (
    AlpacaServiceError,
    get_stock_snapshot,
)


# ============================================================
# 5. RISK MANAGEMENT IMPORTS
# ============================================================

from .calculators import (
    calculate_trade_risk_plan,
    get_market_risk_context,
)

from .forms import RiskPlannerForm

from .models import RiskSnapshot


# ============================================================
# 6. TRADE & PORTFOLIO RISK PLANNER
# ============================================================

@login_required
def calculator(request):
    """
    ============================================================
    TRADE & PORTFOLIO RISK PLANNER
    ============================================================

    Framework mapping:

                    User
                      ↓
              RiskPlannerForm
                      ↓
           Selected stock symbol
                      ↓
            ┌─────────┴─────────┐
            ↓                   ↓
         Alpaca             MarketData
            ↓                   ↓
      Latest price       Historical OHLCV
                                ↓
                        ATR / Volatility /
                        Drawdown / Range
            └─────────┬─────────┘
                      ↓
          calculate_trade_risk_plan()
                      ↓
                 RiskSnapshot
                      ↓
                calculator.html


    The view performs the following tasks:

    1. Finds symbols that have historical data stored in
       MarketPulse.

    2. Accepts any Alpaca-supported symbol through the
       searchable Risk Planner field.

    3. Calculates historical market-risk context when
       MarketPulse already stores history for that symbol.

    4. Determines an entry price using this priority:

       A. User-entered planned entry price

       B. Alpaca latest trade price

       C. Latest stored MarketPulse historical close

    5. Calculates:

       - Maximum risk budget
       - Stop price
       - Risk per share/unit
       - Position size
       - Position value
       - Capital allocation
       - Potential loss
       - Potential reward
       - Reward/risk ratio

    6. Saves the completed calculation as a RiskSnapshot.

    ============================================================
    """


    # ========================================================
    # 6.1 FIND SYMBOLS WITH STORED HISTORICAL DATA
    # ========================================================

    # IMPORTANT:
    #
    # These are NOT the only symbols available to the user.
    #
    # Alpaca provides the searchable asset universe through:
    #
    # /api/alpaca/assets/search/
    #
    # This list is used only to determine which symbols have
    # historical data already stored in MarketPulse.

    stored_symbols_query = (

        MarketData.objects
        .order_by(
            "symbol"
        )
        .values_list(
            "symbol",
            flat=True,
        )
        .distinct()
    )


    # --------------------------------------------------------
    # Normalise stored symbols
    # --------------------------------------------------------

    available_symbols = sorted(

        {

            str(symbol)
            .strip()
            .upper()

            for symbol in stored_symbols_query

            if symbol

        }
    )


    # ========================================================
    # 6.2 DETERMINE CURRENT SYMBOL
    # ========================================================

    # Symbol priority:
    #
    # 1. POSTed form value
    #
    # 2. URL parameter
    #
    #       /risk/calculator/?symbol=AAPL
    #
    # 3. First symbol with stored historical data
    #
    # 4. Empty value
    #
    # An empty value is acceptable because the user can search
    # Alpaca directly from the Risk page.

    selected_symbol = (

        request.POST.get(
            "symbol"
        )

        or

        request.GET.get(
            "symbol"
        )

        or

        (
            available_symbols[0]
            if available_symbols
            else ""
        )
    )


    # --------------------------------------------------------
    # Normalise selected ticker
    # --------------------------------------------------------

    selected_symbol = (

        selected_symbol
        .strip()
        .upper()

        if selected_symbol

        else ""
    )


    # ========================================================
    # 6.3 CREATE RISK PLANNER FORM
    # ========================================================

    form = RiskPlannerForm(

        request.POST or None,

        initial={

            # ------------------------------------------------
            # Symbol
            # ------------------------------------------------

            "symbol":
                selected_symbol,


            # ------------------------------------------------
            # Currency
            # ------------------------------------------------

            "currency":
                "USD",


            # ------------------------------------------------
            # Example trading capital
            # ------------------------------------------------

            "trading_capital":
                10000,


            # ------------------------------------------------
            # Example maximum risk
            #
            # 1 means 1%.
            # ------------------------------------------------

            "risk_percentage":
                1,


            # ------------------------------------------------
            # Long trade by default
            # ------------------------------------------------

            "direction":
                "long",


            # ------------------------------------------------
            # Percentage stop by default
            # ------------------------------------------------

            "stop_method":
                "percentage",


            # ------------------------------------------------
            # Example 5% stop
            # ------------------------------------------------

            "stop_loss_percentage":
                5,


            # ------------------------------------------------
            # Example ATR stop multiplier
            # ------------------------------------------------

            "atr_multiplier":
                2,
        },
    )


    # ========================================================
    # 6.4 BUILD HISTORICAL MARKET-RISK CONTEXT
    # ========================================================

    # Historical context is calculated only for symbols that
    # already exist in core.MarketData.
    #
    # Alpaca symbols that have never been historically
    # imported remain selectable and usable for current-price
    # percentage/fixed-stop calculations.
    #
    # Historical-only analytics such as ATR and drawdown will
    # remain unavailable until historical observations exist.

    market_context_map = {}


    for symbol in available_symbols:

        symbol_context = (
            get_market_risk_context(
                symbol
            )
        )


        if symbol_context:

            market_context_map[
                symbol
            ] = symbol_context


    # ========================================================
    # 6.5 CURRENT HISTORICAL SYMBOL CONTEXT
    # ========================================================

    market_context = (

        market_context_map.get(
            selected_symbol
        )
    )


    # ========================================================
    # 6.6 PREPARE RESULT
    # ========================================================

    result = None


    # ========================================================
    # 6.7 PROCESS SUBMITTED RISK PLAN
    # ========================================================

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        cleaned_data = (
            form.cleaned_data
        )


        # ====================================================
        # 6.8 SELECTED SYMBOL
        # ====================================================

        selected_symbol = (

            cleaned_data[
                "symbol"
            ]
            .strip()
            .upper()
        )


        # ----------------------------------------------------
        # Reload historical context
        # ----------------------------------------------------

        market_context = (

            market_context_map.get(
                selected_symbol
            )
        )


        # ====================================================
        # 6.9 DETERMINE ENTRY PRICE
        # ====================================================

        # MarketPulse uses the following hierarchy:
        #
        # 1. User-entered price
        #
        # 2. Alpaca latest trade price
        #
        # 3. Latest historical close stored by MarketPulse
        #
        # This allows a symbol to be used even when it has not
        # previously been imported into MarketData.

        entry_price = (
            cleaned_data.get(
                "entry_price"
            )
        )


        # ----------------------------------------------------
        # Track price provenance
        # ----------------------------------------------------

        entry_price_source = (
            "Manual entry"
        )


        alpaca_snapshot = None


        # ====================================================
        # 6.10 ALPACA LATEST PRICE FALLBACK
        # ====================================================

        if entry_price is None:

            try:

                alpaca_snapshot = (
                    get_stock_snapshot(
                        selected_symbol
                    )
                )


                alpaca_latest_price = (
                    alpaca_snapshot.get(
                        "latest_price"
                    )
                )


                if (
                    alpaca_latest_price
                    is not None
                ):

                    entry_price = (
                        alpaca_latest_price
                    )


                    entry_price_source = (
                        "Alpaca latest trade"
                    )


            except AlpacaServiceError:

                # ------------------------------------------------
                # Alpaca being temporarily unavailable should not
                # crash the Risk Planner.
                #
                # MarketPulse can still attempt to use its stored
                # historical data.
                # ------------------------------------------------

                entry_price = None


        # ====================================================
        # 6.11 STORED MARKETDATA FALLBACK
        # ====================================================

        if (
            entry_price is None
            and market_context
        ):

            entry_price = (
                market_context.get(
                    "latest_close"
                )
            )


            if entry_price is not None:

                entry_price_source = (
                    "Latest stored historical close"
                )


        # ====================================================
        # 6.12 NO ENTRY PRICE AVAILABLE
        # ====================================================

        if entry_price is None:

            form.add_error(
                "entry_price",
                (
                    "MarketPulse could not retrieve a current "
                    "Alpaca price and no stored historical close "
                    "is available. Enter a planned entry price "
                    "manually."
                ),
            )


        else:

            # =================================================
            # 6.13 CALCULATE COMPLETE RISK PLAN
            # =================================================

            try:

                result = (
                    calculate_trade_risk_plan(


                        # ====================================
                        # TRADING CAPITAL
                        # ====================================

                        trading_capital=
                            cleaned_data[
                                "trading_capital"
                            ],


                        # ====================================
                        # MAXIMUM RISK %
                        # ====================================

                        risk_percentage=
                            cleaned_data[
                                "risk_percentage"
                            ],


                        # ====================================
                        # ENTRY PRICE
                        # ====================================

                        entry_price=
                            entry_price,


                        # ====================================
                        # LONG / SHORT
                        # ====================================

                        direction=
                            cleaned_data[
                                "direction"
                            ],


                        # ====================================
                        # STOP-LOSS METHOD
                        # ====================================

                        stop_method=
                            cleaned_data[
                                "stop_method"
                            ],


                        # ====================================
                        # PERCENTAGE STOP
                        # ====================================

                        stop_loss_percentage=
                            cleaned_data.get(
                                "stop_loss_percentage"
                            ),


                        # ====================================
                        # FIXED STOP
                        # ====================================

                        fixed_stop_price=
                            cleaned_data.get(
                                "stop_price"
                            ),


                        # ====================================
                        # HISTORICAL ATR
                        # ====================================

                        atr=
                            (
                                market_context.get(
                                    "atr_14"
                                )

                                if market_context

                                else None
                            ),


                        # ====================================
                        # ATR MULTIPLIER
                        # ====================================

                        atr_multiplier=
                            cleaned_data.get(
                                "atr_multiplier"
                            ),


                        # ====================================
                        # OPTIONAL PROFIT TARGET
                        # ====================================

                        target_price=
                            cleaned_data.get(
                                "target_price"
                            ),
                    )
                )


                # =================================================
                # 6.14 ADD WEB-DISPLAY INFORMATION
                # =================================================

                # The calculation engine deliberately remains
                # generic.
                #
                # These additional fields help the web interface
                # explain where values came from.

                result[
                    "symbol"
                ] = (
                    selected_symbol
                )


                result[
                    "currency"
                ] = (
                    cleaned_data[
                        "currency"
                    ]
                )


                result[
                    "direction"
                ] = (
                    cleaned_data[
                        "direction"
                    ]
                )


                result[
                    "risk_percentage"
                ] = float(
                    cleaned_data[
                        "risk_percentage"
                    ]
                )


                result[
                    "trading_capital"
                ] = float(
                    cleaned_data[
                        "trading_capital"
                    ]
                )


                # ------------------------------------------------
                # Entry Price Source
                # ------------------------------------------------

                result[
                    "entry_price_source"
                ] = (
                    entry_price_source
                )


                # ------------------------------------------------
                # Data provenance
                # ------------------------------------------------

                result[
                    "current_market_provider"
                ] = (
                    "Alpaca"
                )


                result[
                    "historical_data_available"
                ] = bool(
                    market_context
                )


                # ------------------------------------------------
                # Optional Target Price
                # ------------------------------------------------

                result[
                    "target_price"
                ] = (

                    float(
                        cleaned_data[
                            "target_price"
                        ]
                    )

                    if cleaned_data.get(
                        "target_price"
                    )

                    else None
                )


                # ------------------------------------------------
                # Stop Method
                # ------------------------------------------------

                result[
                    "stop_method"
                ] = (
                    cleaned_data[
                        "stop_method"
                    ]
                )


                # =================================================
                # 6.15 OPTIONAL ALPACA SNAPSHOT INFORMATION
                # =================================================

                # This information is not necessary for the core
                # risk mathematics but helps make the result more
                # transparent.

                if alpaca_snapshot:

                    result[
                        "alpaca_feed"
                    ] = (
                        alpaca_snapshot.get(
                            "feed"
                        )
                    )


                    result[
                        "alpaca_latest_price"
                    ] = (
                        alpaca_snapshot.get(
                            "latest_price"
                        )
                    )


                    result[
                        "alpaca_bid_price"
                    ] = (
                        alpaca_snapshot.get(
                            "bid_price"
                        )
                    )


                    result[
                        "alpaca_ask_price"
                    ] = (
                        alpaca_snapshot.get(
                            "ask_price"
                        )
                    )


                # =================================================
                # 6.16 SAVE RISK SNAPSHOT
                # =================================================

                # RiskSnapshot already exists in MarketPulse,
                # therefore we reuse the existing database model.
                #
                # IMPORTANT:
                #
                # The UI accepts:
                #
                #     1%
                #
                # RiskSnapshot stores:
                #
                #     0.01
                #
                # therefore the percentage must be divided by 100.

                risk_percentage_decimal = (

                    Decimal(
                        str(
                            cleaned_data[
                                "risk_percentage"
                            ]
                        )
                    )

                    /

                    Decimal(
                        "100"
                    )
                )


                # =================================================
                # 6.17 HISTORICAL VOLATILITY
                # =================================================

                # get_market_risk_context() returns annualised
                # volatility as a percentage.
                #
                # Example:
                #
                #     24.50
                #
                # represents:
                #
                #     24.50%
                #
                # RiskSnapshot stores the decimal representation:
                #
                #     0.245

                volatility_decimal = (
                    Decimal(
                        "0"
                    )
                )


                if (
                    market_context
                    and
                    market_context.get(
                        "annualised_volatility_pct"
                    )
                    is not None
                ):

                    volatility_decimal = (

                        Decimal(
                            str(
                                market_context[
                                    "annualised_volatility_pct"
                                ]
                            )
                        )

                        /

                        Decimal(
                            "100"
                        )
                    )


                # =================================================
                # 6.18 SAVE HISTORICAL RISK CALCULATION
                # =================================================

                RiskSnapshot.objects.create(


                    # --------------------------------------------
                    # User
                    # --------------------------------------------

                    user=
                        request.user,


                    # --------------------------------------------
                    # Asset Symbol
                    # --------------------------------------------

                    symbol=
                        selected_symbol,


                    # --------------------------------------------
                    # Trading Capital
                    #
                    # RiskSnapshot uses the original model field:
                    # account_balance.
                    # --------------------------------------------

                    account_balance=
                        cleaned_data[
                            "trading_capital"
                        ],


                    # --------------------------------------------
                    # Risk Percentage
                    # --------------------------------------------

                    risk_percentage=
                        risk_percentage_decimal,


                    # --------------------------------------------
                    # Historical Volatility
                    # --------------------------------------------

                    volatility=
                        volatility_decimal,


                    # --------------------------------------------
                    # Position Size
                    # --------------------------------------------

                    recommended_position_size=
                        Decimal(
                            str(
                                result[
                                    "quantity"
                                ]
                            )
                        ),


                    # --------------------------------------------
                    # Stop-Loss Price
                    # --------------------------------------------

                    stop_loss_price=
                        Decimal(
                            str(
                                result[
                                    "stop_price"
                                ]
                            )
                        ),
                )


            # =================================================
            # 6.19 RISK CALCULATION VALIDATION ERROR
            # =================================================

            except ValueError as error:

                # Examples:
                #
                # - Long stop above entry
                # - Short stop below entry
                # - Invalid profit target
                # - Missing historical ATR
                # - Invalid percentage
                #
                # These errors should appear inside the form
                # rather than producing a Django 500 page.

                form.add_error(
                    None,
                    str(error),
                )


    # ========================================================
    # 6.20 TEMPLATE CONTEXT
    # ========================================================

    context = {


        # ----------------------------------------------------
        # Risk Planner Form
        # ----------------------------------------------------

        "form":
            form,


        # ----------------------------------------------------
        # Authoritative Server Calculation
        # ----------------------------------------------------

        "result":
            result,


        # ----------------------------------------------------
        # Historical context for current symbol
        # ----------------------------------------------------

        "market_context":
            market_context,


        # ----------------------------------------------------
        # Historical contexts for imported symbols
        #
        # calculator.html serialises this safely using:
        #
        # json_script
        # ----------------------------------------------------

        "market_context_map":
            market_context_map,


        # ----------------------------------------------------
        # Currently selected ticker
        # ----------------------------------------------------

        "selected_symbol":
            selected_symbol,


        # ----------------------------------------------------
        # Symbols with stored historical MarketData
        #
        # NOTE:
        #
        # This is not the Alpaca universe.
        #
        # Alpaca search is provided separately through the
        # MarketPulse API.
        # ----------------------------------------------------

        "available_symbols":
            available_symbols,


        # ----------------------------------------------------
        # Provider labels
        # ----------------------------------------------------

        "current_market_provider":
            "Alpaca",

        "historical_market_provider":
            "MarketPulse Stored Data",
    }


    # ========================================================
    # 6.21 RENDER RISK PLANNER
    # ========================================================

    return render(

        request,

        "risk_management/calculator.html",

        context,
    )


# ============================================================
# 7. RISK HISTORY DASHBOARD
# ============================================================

@login_required
def dashboard(request):
    """
    ============================================================
    RISK DASHBOARD
    ============================================================

    Displays the logged-in user's most recent RiskSnapshot
    records.

    Framework mapping:

    Trade Risk Planner
            ↓
       RiskSnapshot
            ↓
         dashboard()
            ↓
    risk_management/dashboard.html
    ============================================================
    """


    # ========================================================
    # 7.1 LATEST RISK CALCULATIONS
    # ========================================================

    snapshots = (

        RiskSnapshot.objects
        .filter(
            user=request.user
        )
        .order_by(
            "-created_at"
        )[:20]
    )


    # ========================================================
    # 7.2 USER PROFILE
    # ========================================================

    profile = getattr(
        request.user,
        "profile",
        None,
    )


    # ========================================================
    # 7.3 TEMPLATE CONTEXT
    # ========================================================

    context = {

        "snapshots":
            snapshots,

        "profile":
            profile,
    }


    # ========================================================
    # 7.4 RENDER DASHBOARD
    # ========================================================

    return render(

        request,

        "risk_management/dashboard.html",

        context,
    )