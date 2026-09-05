"""
============================================================
MARKETPULSE - RISK MANAGEMENT VIEWS
============================================================

User-facing Risk functionality:

1. Trade & Portfolio Risk Planner
2. Stress Testing

Market Condition analysis does NOT belong here.
It belongs in data_management/views.py.

Architecture:

Alpaca
    ↓
Latest market information
    ↓

MarketData PostgreSQL
    ↓
Historical ATR / volatility / drawdown
    ↓

Risk Planner
    ↓
Position sizing / Stop-loss / Reward-to-risk

Strategy + Historical Data
    ↓
Stress Test
============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)


# ============================================================
# 2. MARKETPULSE CORE MODELS
# ============================================================

from core.models import (
    MarketData,
    Strategy,
)


# ============================================================
# 3. RISK FORM
# ============================================================

from .forms import RiskPlannerForm


# ============================================================
# 4. RISK CALCULATORS
# ============================================================

from .calculators import (
    calculate_trade_risk_plan,
    get_market_risk_context,
)


# ============================================================
# 5. ALPACA MARKET DATA SERVICE
# ============================================================

from data_management.services.alpaca import (
    AlpacaServiceError,
    get_stock_snapshot,
)


# ============================================================
# 6. ANALYTICS ENGINE
# ============================================================

from analysis_tools.analyzers import (
    run_stress_test,
)


from analysis_tools.models import (
    StressTest,
)


# ============================================================
# 7. TRADE & PORTFOLIO RISK CALCULATOR
# ============================================================

@login_required
def calculator(request):
    """
    ============================================================
    TRADE & PORTFOLIO RISK PLANNER
    ============================================================

    This is the main Risk page.

    It combines:

    - Alpaca latest market prices
    - Stored historical MarketData
    - Position sizing
    - Stop-loss calculations
    - ATR
    - Reward-to-risk
    - Maximum planned loss

    Entry-price priority:

    1. User-entered price
    2. Alpaca latest trade
    3. Latest stored historical close

    ============================================================
    """


    # ========================================================
    # 7.1 SYMBOLS WITH HISTORICAL DATA
    # ========================================================

    available_symbols = list(

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


    # ========================================================
    # 7.2 CURRENT SYMBOL
    # ========================================================

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


    selected_symbol = (
        selected_symbol
        .strip()
        .upper()
    )


    # ========================================================
    # 7.3 RISK FORM
    # ========================================================

    form = RiskPlannerForm(

        request.POST or None,

        initial={

            "symbol":
                selected_symbol,

            "trading_capital":
                10000,

            "risk_percentage":
                1,

            "currency":
                "USD",

            "direction":
                "long",

            "stop_method":
                "percentage",

            "stop_loss_percentage":
                5,

            "atr_multiplier":
                2,

        },

    )


    # ========================================================
    # 7.4 HISTORICAL MARKET CONTEXT
    # ========================================================

    market_context_map = {}


    for symbol in available_symbols:


        historical_context = (
            get_market_risk_context(
                symbol
            )
        )


        if historical_context:


            market_context_map[
                symbol
            ] = historical_context


    # ========================================================
    # 7.5 SELECTED HISTORICAL CONTEXT
    # ========================================================

    market_context = (

        market_context_map.get(
            selected_symbol
        )

    )


    # ========================================================
    # 7.6 RESULT
    # ========================================================

    result = None


    # ========================================================
    # 7.7 PROCESS FORM
    # ========================================================

    if (
        request.method == "POST"
        and
        form.is_valid()
    ):


        cleaned = (
            form.cleaned_data
        )


        selected_symbol = (

            cleaned[
                "symbol"
            ]
            .strip()
            .upper()

        )


        market_context = (

            market_context_map.get(
                selected_symbol
            )

        )


        # ====================================================
        # 7.8 ENTRY PRICE
        # ====================================================

        entry_price = (

            cleaned.get(
                "entry_price"
            )

        )


        # ----------------------------------------------------
        # Try Alpaca when no manual entry price was supplied.
        # ----------------------------------------------------

        if entry_price is None:


            try:


                alpaca_snapshot = (
                    get_stock_snapshot(
                        selected_symbol
                    )
                )


                entry_price = (
                    alpaca_snapshot.get(
                        "latest_price"
                    )
                )


            except AlpacaServiceError:


                entry_price = None


        # ----------------------------------------------------
        # Historical close is fallback.
        # ----------------------------------------------------

        if (
            entry_price is None
            and
            market_context
        ):


            entry_price = (

                market_context.get(
                    "latest_close"
                )

            )


        # ----------------------------------------------------
        # Still no usable entry price.
        # ----------------------------------------------------

        if entry_price is None:


            form.add_error(

                "entry_price",

                (
                    "MarketPulse could not obtain a current "
                    "Alpaca price or a stored historical price. "
                    "Enter an entry price manually."
                ),

            )


        else:


            # =================================================
            # 7.9 CALCULATE RISK PLAN
            # =================================================

            try:


                result = (

                    calculate_trade_risk_plan(

                        trading_capital=
                            cleaned[
                                "trading_capital"
                            ],

                        risk_percentage=
                            cleaned[
                                "risk_percentage"
                            ],

                        entry_price=
                            entry_price,

                        direction=
                            cleaned[
                                "direction"
                            ],

                        stop_method=
                            cleaned[
                                "stop_method"
                            ],

                        stop_loss_percentage=
                            cleaned.get(
                                "stop_loss_percentage"
                            ),

                        fixed_stop_price=
                            cleaned.get(
                                "stop_price"
                            ),

                        atr=
                            (
                                market_context.get(
                                    "atr_14"
                                )

                                if market_context

                                else None
                            ),

                        atr_multiplier=
                            cleaned.get(
                                "atr_multiplier"
                            ),

                        target_price=
                            cleaned.get(
                                "target_price"
                            ),

                    )

                )


                # =============================================
                # 7.10 ADD DISPLAY INFORMATION
                # =============================================

                result[
                    "symbol"
                ] = selected_symbol


                result[
                    "currency"
                ] = cleaned.get(
                    "currency",
                    "USD",
                )


                result[
                    "direction"
                ] = cleaned[
                    "direction"
                ]


                result[
                    "risk_percentage"
                ] = float(

                    cleaned[
                        "risk_percentage"
                    ]

                )


                result[
                    "trading_capital"
                ] = float(

                    cleaned[
                        "trading_capital"
                    ]

                )


                result[
                    "target_price"
                ] = (

                    float(
                        cleaned[
                            "target_price"
                        ]
                    )

                    if cleaned.get(
                        "target_price"
                    )

                    else None

                )


            except ValueError as error:


                form.add_error(
                    None,
                    str(error),
                )


    # ========================================================
    # 7.11 TEMPLATE CONTEXT
    # ========================================================

    context = {

        "form":
            form,

        "result":
            result,

        "market_context":
            market_context,

        "market_context_map":
            market_context_map,

        "selected_symbol":
            selected_symbol,

        "available_symbols":
            available_symbols,

    }


    # ========================================================
    # 7.12 RENDER PAGE
    # ========================================================

    return render(

        request,

        "risk_management/calculator.html",

        context,

    )


# ============================================================
# 8. STRESS TEST
# ============================================================

@login_required
def stress_test(request):
    """
    ============================================================
    STRESS TEST
    ============================================================

    User question:

        "What happens if market conditions become much worse?"

    Technical implementation:

        analysis_tools.analyzers.run_stress_test()

    The complex parameters remain in the backend.

    Users select understandable scenarios instead:

    - Severe market decline
    - Volatility spike
    - Liquidity shock
    - Market condition change
    ============================================================
    """


    # ========================================================
    # 8.1 USER STRATEGIES
    # ========================================================

    strategies = (

        Strategy.objects
        .filter(
            user=request.user
        )
        .order_by(
            "name"
        )

    )


    # ========================================================
    # 8.2 AVAILABLE HISTORICAL SYMBOLS
    # ========================================================

    symbols = list(

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


    # ========================================================
    # 8.3 PROCESS STRESS TEST
    # ========================================================

    if request.method == "POST":


        strategy_id = (
            request.POST.get(
                "strategy"
            )
        )


        symbol = (

            request.POST.get(
                "symbol",
                "",
            )
            .strip()
            .upper()

        )


        scenario = (

            request.POST.get(
                "scenario",
                "crash",
            )

        )


        # ----------------------------------------------------
        # Validate strategy selection.
        # ----------------------------------------------------

        if not strategy_id:


            messages.error(
                request,
                "Select a strategy first.",
            )


        elif not symbol:


            messages.error(
                request,
                "Select an asset first.",
            )


        else:


            strategy = get_object_or_404(

                Strategy,

                id=strategy_id,

                user=request.user,

            )


            # =================================================
            # 8.4 USER-FRIENDLY SCENARIO PRESETS
            # =================================================

            scenarios = {


                # ---------------------------------------------
                # Severe market decline
                # ---------------------------------------------

                "crash": {

                    "crash_start":
                        0.70,

                    "crash_magnitude":
                        0.20,

                },


                # ---------------------------------------------
                # Volatility spike
                # ---------------------------------------------

                "volatility_spike": {

                    "spike_start":
                        0.50,

                    "spike_duration":
                        0.10,

                    "spike_magnitude":
                        3.0,

                },


                # ---------------------------------------------
                # Liquidity shock
                # ---------------------------------------------

                "liquidity_crisis": {

                    "crisis_start":
                        0.60,

                    "crisis_duration":
                        0.20,

                    "volume_reduction":
                        0.70,

                },


                # ---------------------------------------------
                # Market condition / regime change
                # ---------------------------------------------

                "regime_change": {

                    "change_point":
                        0.50,

                    "new_trend":
                        -0.01,

                },

            }


            parameters = (

                scenarios.get(
                    scenario
                )

            )


            if parameters is None:


                messages.error(
                    request,
                    "Choose a valid stress scenario.",
                )


            else:


                # =============================================
                # 8.5 RUN INTERNAL ANALYTICS ENGINE
                # =============================================

                stress_result = (

                    run_stress_test(

                        strategy,

                        symbol,

                        scenario,

                        parameters,

                    )

                )


                if stress_result:


                    messages.success(
                        request,
                        "Stress test completed successfully.",
                    )


                    return redirect(
                        "risk_management:stress_test_results"
                    )


                else:


                    messages.error(

                        request,

                        (
                            "MarketPulse could not complete the "
                            "stress test. Make sure the selected "
                            "asset has sufficient historical data."
                        ),

                    )


    # ========================================================
    # 8.6 RENDER STRESS TEST
    # ========================================================

    return render(

        request,

        "risk_management/stress_test.html",

        {

            "strategies":
                strategies,

            "symbols":
                symbols,

        },

    )


# ============================================================
# 9. STRESS TEST RESULTS
# ============================================================

@login_required
def stress_test_results(request):
    """
    Display recent stress-test results for the logged-in user.
    """


    tests = (

        StressTest.objects
        .filter(
            user=request.user
        )
        .order_by(
            "-created_at"
        )[:20]

    )


    return render(

        request,

        "risk_management/stress_test_results.html",

        {

            "tests":
                tests,

        },

    )