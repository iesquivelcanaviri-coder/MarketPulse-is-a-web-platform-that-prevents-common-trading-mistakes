"""
============================================================
MARKETPULSE - STRATEGY BUILDER VIEWS
============================================================

Framework mapping:

Strategy & Model Library
        ↓
StrategyLibraryItem
        ↓
strategy_list()
        ↓
templates/strategy_builder/list.html
        ↓
Browse / Filter / Compare Models


Custom Strategy Builder
        ↓
StrategyCreateForm
        ↓
core.Strategy
        ↓
strategy_create()
        ↓
Backtesting


Historical Backtesting
        ↓
BacktestForm
        ↓
run_backtest()
        ↓
core.Backtest
        ↓
BacktestTrade
        ↓
backtest_results()


Strategy Robustness
        ↓
Strategies Tab
        ↓
User Strategy
        ↓
Historical MarketData
        ↓
analysis_tools.detect_overfitting()
        ↓
OverfittingTest
        ↓
Result displayed inside /strategy/


Stress Testing
        ↓
Strategies Tab
        ↓
User Strategy
        ↓
Historical MarketData
        ↓
Predefined severe market scenario
        ↓
analysis_tools.run_stress_test()
        ↓
StressTest
        ↓
Result displayed inside /strategy/


Add New Library Model
        ↓
StrategyLibraryItemForm
        ↓
StrategyLibraryItem
        ↓
Strategy & Model Library


PURPOSE:

This views file connects the Strategy section of MarketPulse
with:

- The built-in model library
- User-created strategies
- Model comparison
- Backtesting
- Historical performance metrics
- Strategy robustness / overfitting analysis
- Stress testing
- Future strategy/model execution


IMPORTANT ARCHITECTURE:

The old public "Analysis" section is removed from the
user-facing navigation.

analysis_tools remains inside the project as an INTERNAL
analytics engine.

The user now accesses:

Strategy & Model Research
    through the Strategies tab

Historical Backtesting
    through the Strategies tab

Strategy Robustness
    directly inside the Strategies page

Stress Testing
    directly inside the Strategies page

Market Condition
    through the Data tab


IMPORTANT:

Strategy Robustness and Stress Testing DO NOT require
separate user-facing pages.

Their calculations remain separated in the backend,
but their forms and latest results are displayed inside:

    /strategy/

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.db.models import (
    Max,
    Min,
)

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.urls import reverse


# ============================================================
# 2. CORE MODEL IMPORTS
# ============================================================

from core.models import (
    Backtest,
    MarketData,
    Strategy,
)


# ============================================================
# 3. INTERNAL ANALYTICS ENGINE IMPORTS
# ============================================================

# analysis_tools remains an internal analytics layer.
#
# detect_overfitting()
#     powers Strategy Robustness.
#
# run_stress_test()
#     powers Strategy Stress Testing.
from analysis_tools.analyzers import (
    detect_overfitting,
    run_stress_test,
)


# OverfittingTest stores Strategy Robustness results.
#
# StressTest stores Strategy Stress Testing results.
from analysis_tools.models import (
    OverfittingTest,
    StressTest,
)


# ============================================================
# 4. STRATEGY BUILDER FORM IMPORTS
# ============================================================

from .forms import (
    BacktestForm,
    StrategyCreateForm,
    StrategyLibraryItemForm,
)


# ============================================================
# 5. STRATEGY BUILDER MODEL IMPORTS
# ============================================================

from .models import StrategyLibraryItem


# ============================================================
# 6. BACKTESTING ENGINE IMPORT
# ============================================================

from .backtesting import run_backtest


# ============================================================
# 7. INTERNAL VIEW HELPERS
# ============================================================

def _strategy_workspace_url(
    anchor=None,
):
    """
    Return the main Strategies workspace URL.

    Optional anchor examples:

        strategyRobustnessSection
        stressTestingSection
        myStrategiesSection
    """

    url = reverse(
        "strategy_builder:list"
    )

    if anchor:

        return (
            f"{url}#{anchor}"
        )

    return url


def _get_available_historical_symbols():
    """
    Return all symbols currently available in core.MarketData.

    Both Strategy Robustness and Stress Testing depend on
    stored historical data rather than only live Alpaca data.
    """

    return list(
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


def _robustness_interpretation(
    test,
):
    """
    Convert the technical OverfittingTest result into
    user-friendly language.

    Returns:

        label,
        explanation
    """

    if not test:

        return (
            None,
            None,
        )


    score = float(
        test.overfitting_score
    )


    if (
        test.is_overfitted
        and score >= 0.50
    ):

        return (
            "High Overfitting Risk",
            (
                "Performance weakened substantially when "
                "MarketPulse moved from the in-sample period "
                "to the out-of-sample period. The historical "
                "result may depend too heavily on the data "
                "used during strategy development."
            ),
        )


    if test.is_overfitted:

        return (
            "Moderate Overfitting Risk",
            (
                "The strategy showed a meaningful reduction "
                "in performance on the out-of-sample period. "
                "Additional testing across other data periods "
                "and market conditions would be useful."
            ),
        )


    return (
        "Low Overfitting Risk",
        (
            "The simplified robustness check did not identify "
            "a large deterioration between the in-sample and "
            "out-of-sample periods. This does not guarantee "
            "future performance."
        ),
    )


# ============================================================
# 8. STRATEGY & MODEL RESEARCH WORKSPACE
# ============================================================

@login_required
def strategy_list(request):
    """
    ============================================================
    STRATEGY & MODEL RESEARCH WORKSPACE
    ============================================================

    URL:

        /strategy/


    The Strategies page now combines:

    1. Strategy & Model Library

    2. Model Search and Filtering

    3. Model Comparison

    4. User-Created Strategies

    5. Historical Backtesting

    6. Strategy Robustness

    7. Stress Testing


    IMPORTANT:

    Strategy Robustness and Stress Testing are processed
    directly by this view.

    They no longer require users to leave the Strategies page.
    ============================================================
    """


    # ========================================================
    # 8.1 LOAD THE COMPLETE ACTIVE MODEL LIBRARY
    # ========================================================

    library_items = (
        StrategyLibraryItem.objects
        .filter(
            is_active=True
        )
        .order_by(
            "category",
            "display_order",
            "name",
        )
    )


    # ========================================================
    # 8.2 BUILD CATEGORY SUMMARY CARDS
    # ========================================================

    category_cards = []


    for (
        category_code,
        category_label,
    ) in StrategyLibraryItem.CATEGORY_CHOICES:

        category_count = (
            library_items
            .filter(
                category=category_code
            )
            .count()
        )


        category_cards.append(
            {
                "code":
                    category_code,

                "label":
                    category_label,

                "count":
                    category_count,
            }
        )


    # ========================================================
    # 8.3 LIBRARY SUMMARY STATISTICS
    # ========================================================

    total_library_models = (
        library_items.count()
    )


    ready_models = (
        library_items
        .filter(
            implementation_status="ready"
        )
        .count()
    )


    experimental_models = (
        library_items
        .filter(
            implementation_status="experimental"
        )
        .count()
    )


    catalogued_models = (
        library_items
        .filter(
            implementation_status="catalogued"
        )
        .count()
    )


    # ========================================================
    # 8.4 MODEL COMPARISON
    # ========================================================

    requested_compare_codes = (
        request.GET.getlist(
            "compare"
        )
    )


    # Remove duplicate selections while preserving order.
    requested_compare_codes = list(
        dict.fromkeys(
            requested_compare_codes
        )
    )


    comparison_message = ""


    # ========================================================
    # 8.5 LIMIT COMPARISON TO FOUR MODELS
    # ========================================================

    if len(requested_compare_codes) > 4:

        requested_compare_codes = (
            requested_compare_codes[:4]
        )


        comparison_message = (
            "MarketPulse compares a maximum of four "
            "models at the same time."
        )


    # ========================================================
    # 8.6 RETRIEVE SELECTED COMPARISON MODELS
    # ========================================================

    compare_queryset = (
        StrategyLibraryItem.objects
        .filter(
            code__in=requested_compare_codes,
            is_active=True,
        )
    )


    compare_lookup = {

        item.code:
            item

        for item in compare_queryset
    }


    compare_items = [

        compare_lookup[code]

        for code in requested_compare_codes

        if code in compare_lookup
    ]


    if (
        requested_compare_codes
        and len(compare_items) < 2
    ):

        comparison_message = (
            "Select at least two models to compare."
        )


    # ========================================================
    # 8.7 LOAD USER-CREATED STRATEGIES
    # ========================================================

    my_strategies = (
        Strategy.objects
        .filter(
            user=request.user
        )
        .prefetch_related(
            "rules"
        )
        .order_by(
            "-created_at"
        )
    )


    # ========================================================
    # 8.8 AVAILABLE HISTORICAL MARKET DATA
    # ========================================================

    available_symbols = (
        _get_available_historical_symbols()
    )


    # ========================================================
    # 8.9 PRESERVE SAME-PAGE VALIDATION SELECTIONS
    # ========================================================

    # A strategy can be supplied by:
    #
    # POST:
    #     when a form is submitted
    #
    # GET:
    #     when a "Check Robustness" or Stress Test link
    #     pre-selects a specific strategy.
    selected_validation_strategy = (
        request.POST.get(
            "strategy"
        )
        or
        request.GET.get(
            "strategy"
        )
        or
        ""
    )


    selected_validation_symbol = (
        request.POST.get(
            "symbol"
        )
        or
        request.GET.get(
            "symbol"
        )
        or
        ""
    ).strip().upper()


    selected_stress_scenario = (
        request.POST.get(
            "scenario"
        )
        or
        "crash"
    )


    # ========================================================
    # 8.10 PROCESS SAME-PAGE STRATEGY ACTION
    # ========================================================

    if request.method == "POST":

        action = (
            request.POST.get(
                "action",
                "",
            )
        )


        # ====================================================
        # 8.10.1 STRATEGY ROBUSTNESS
        # ====================================================

        if action == "robustness":


            # ------------------------------------------------
            # Require strategy
            # ------------------------------------------------

            if not selected_validation_strategy:

                messages.error(
                    request,
                    "Select a strategy to test.",
                )


            # ------------------------------------------------
            # Require historical asset
            # ------------------------------------------------

            elif not selected_validation_symbol:

                messages.error(
                    request,
                    "Select a historical asset to test.",
                )


            else:

                strategy = get_object_or_404(
                    Strategy,
                    pk=selected_validation_strategy,
                    user=request.user,
                )


                # =============================================
                # HISTORICAL DATA FOR SELECTED SYMBOL
                # =============================================

                market_queryset = (
                    MarketData.objects
                    .filter(
                        symbol=selected_validation_symbol
                    )
                    .order_by(
                        "date"
                    )
                )


                observation_count = (
                    market_queryset.count()
                )


                # =============================================
                # MINIMUM DATA REQUIREMENT
                # =============================================

                if observation_count < 60:

                    messages.error(
                        request,
                        (
                            f"{selected_validation_symbol} currently "
                            f"has {observation_count} historical "
                            f"observations. MarketPulse requires at "
                            f"least 60 observations for this "
                            f"Strategy Robustness check."
                        ),
                    )


                else:

                    # =========================================
                    # DETERMINE AVAILABLE DATE RANGE
                    # =========================================

                    date_range = (
                        market_queryset.aggregate(
                            first_date=Min(
                                "date"
                            ),
                            last_date=Max(
                                "date"
                            ),
                        )
                    )


                    first_date = (
                        date_range[
                            "first_date"
                        ]
                    )


                    last_date = (
                        date_range[
                            "last_date"
                        ]
                    )


                    if (
                        first_date is None
                        or
                        last_date is None
                        or
                        first_date >= last_date
                    ):

                        messages.error(
                            request,
                            (
                                "MarketPulse could not determine "
                                "a valid historical period for "
                                f"{selected_validation_symbol}."
                            ),
                        )


                    else:

                        # =====================================
                        # ROBUSTNESS TEST PERIOD
                        # =====================================

                        # detect_overfitting() performs its own
                        # internal in-sample/out-of-sample split.
                        test_periods = [
                            (
                                first_date,
                                last_date,
                            )
                        ]


                        # =====================================
                        # RUN INTERNAL ANALYTICS ENGINE
                        # =====================================

                        try:

                            tests = (
                                detect_overfitting(
                                    strategy,
                                    selected_validation_symbol,
                                    test_periods,
                                )
                            )


                            if tests:

                                messages.success(
                                    request,
                                    (
                                        "Strategy Robustness check "
                                        f"completed for "
                                        f"{strategy.name} on "
                                        f"{selected_validation_symbol}."
                                    ),
                                )


                                return redirect(
                                    _strategy_workspace_url(
                                        "strategyRobustnessSection"
                                    )
                                )


                            messages.error(
                                request,
                                (
                                    "MarketPulse could not produce "
                                    "a Strategy Robustness result."
                                ),
                            )


                        except Exception as error:

                            messages.error(
                                request,
                                (
                                    "Strategy Robustness analysis "
                                    "could not be completed: "
                                    f"{error}"
                                ),
                            )


        # ====================================================
        # 8.10.2 STRESS TESTING
        # ====================================================

        elif action == "stress_test":


            # ------------------------------------------------
            # Require strategy
            # ------------------------------------------------

            if not selected_validation_strategy:

                messages.error(
                    request,
                    "Select a strategy first.",
                )


            # ------------------------------------------------
            # Require asset
            # ------------------------------------------------

            elif not selected_validation_symbol:

                messages.error(
                    request,
                    "Select an asset first.",
                )


            else:

                strategy = get_object_or_404(
                    Strategy,
                    pk=selected_validation_strategy,
                    user=request.user,
                )


                # =============================================
                # USER-FRIENDLY STRESS SCENARIOS
                # =============================================

                scenarios = {


                    # -----------------------------------------
                    # Severe market decline
                    # -----------------------------------------

                    "crash": {

                        "crash_start":
                            0.70,

                        "crash_magnitude":
                            0.20,

                    },


                    # -----------------------------------------
                    # Volatility spike
                    # -----------------------------------------

                    "volatility_spike": {

                        "spike_start":
                            0.50,

                        "spike_duration":
                            0.10,

                        "spike_magnitude":
                            3.0,

                    },


                    # -----------------------------------------
                    # Liquidity shock
                    # -----------------------------------------

                    "liquidity_crisis": {

                        "crisis_start":
                            0.60,

                        "crisis_duration":
                            0.20,

                        "volume_reduction":
                            0.70,

                    },


                    # -----------------------------------------
                    # Market condition change
                    # -----------------------------------------

                    "regime_change": {

                        "change_point":
                            0.50,

                        "new_trend":
                            -0.01,

                    },

                }


                parameters = (
                    scenarios.get(
                        selected_stress_scenario
                    )
                )


                # =============================================
                # VALIDATE SCENARIO
                # =============================================

                if parameters is None:

                    messages.error(
                        request,
                        "Choose a valid stress scenario.",
                    )


                else:

                    # =========================================
                    # RUN INTERNAL STRESS TEST ENGINE
                    # =========================================

                    try:

                        stress_result = (
                            run_stress_test(
                                strategy,
                                selected_validation_symbol,
                                selected_stress_scenario,
                                parameters,
                            )
                        )


                        if stress_result:

                            messages.success(
                                request,
                                (
                                    "Stress test completed "
                                    f"for {strategy.name} on "
                                    f"{selected_validation_symbol}."
                                ),
                            )


                            return redirect(
                                _strategy_workspace_url(
                                    "stressTestingSection"
                                )
                            )


                        messages.error(
                            request,
                            (
                                "MarketPulse could not complete "
                                "the stress test. Make sure the "
                                "selected asset has sufficient "
                                "historical data."
                            ),
                        )


                    except Exception as error:

                        messages.error(
                            request,
                            (
                                "Stress testing could not be "
                                f"completed: {error}"
                            ),
                        )


    # ========================================================
    # 8.11 PREPARE STRATEGY PERFORMANCE + ROBUSTNESS SUMMARY
    # ========================================================

    my_strategy_rows = []


    for strategy in my_strategies:


        # ----------------------------------------------------
        # Latest historical backtest
        # ----------------------------------------------------

        latest_backtest = (
            strategy.backtests
            .order_by(
                "-created_at"
            )
            .first()
        )


        # ----------------------------------------------------
        # Number of historical backtests
        # ----------------------------------------------------

        backtest_count = (
            strategy.backtests
            .count()
        )


        # ----------------------------------------------------
        # Latest Strategy Robustness result
        # ----------------------------------------------------

        # Current MarketPulse OverfittingTest storage uses:
        #
        # user
        # +
        # strategy_name
        #
        # rather than requiring a Strategy foreign key here.
        latest_robustness_test = (
            OverfittingTest.objects
            .filter(
                user=request.user,
                strategy_name=strategy.name,
            )
            .order_by(
                "-created_at"
            )
            .first()
        )


        # ----------------------------------------------------
        # Convert result into user-facing label
        # ----------------------------------------------------

        (
            robustness_label,
            robustness_explanation,
        ) = _robustness_interpretation(
            latest_robustness_test
        )


        # ----------------------------------------------------
        # Add prepared row
        # ----------------------------------------------------

        my_strategy_rows.append(
            {
                "strategy":
                    strategy,

                "latest_backtest":
                    latest_backtest,

                "backtest_count":
                    backtest_count,

                "latest_robustness_test":
                    latest_robustness_test,

                "robustness_label":
                    robustness_label,

                "robustness_explanation":
                    robustness_explanation,
            }
        )


    # ========================================================
    # 8.12 USER ROBUSTNESS SUMMARY
    # ========================================================

    robustness_test_count = (
        OverfittingTest.objects
        .filter(
            user=request.user
        )
        .count()
    )


    latest_user_robustness_test = (
        OverfittingTest.objects
        .filter(
            user=request.user
        )
        .order_by(
            "-created_at"
        )
        .first()
    )


    (
        latest_user_robustness_label,
        latest_user_robustness_explanation,
    ) = _robustness_interpretation(
        latest_user_robustness_test
    )


    # ========================================================
    # 8.13 USER STRESS TEST SUMMARY
    # ========================================================

    stress_test_count = (
        StressTest.objects
        .filter(
            user=request.user
        )
        .count()
    )


    latest_strategy_stress_test = (
        StressTest.objects
        .filter(
            user=request.user
        )
        .order_by(
            "-created_at"
        )
        .first()
    )


    # ========================================================
    # 8.14 BUILD TEMPLATE CONTEXT
    # ========================================================

    context = {


        # ----------------------------------------------------
        # Strategy library
        # ----------------------------------------------------

        "library_items":
            library_items,


        # ----------------------------------------------------
        # Category cards
        # ----------------------------------------------------

        "category_cards":
            category_cards,


        # ----------------------------------------------------
        # Summary statistics
        # ----------------------------------------------------

        "total_library_models":
            total_library_models,

        "ready_models":
            ready_models,

        "experimental_models":
            experimental_models,

        "catalogued_models":
            catalogued_models,


        # ----------------------------------------------------
        # Model comparison
        # ----------------------------------------------------

        "compare_items":
            compare_items,

        "compare_codes":
            requested_compare_codes,

        "comparison_message":
            comparison_message,


        # ----------------------------------------------------
        # User strategies
        # ----------------------------------------------------

        "my_strategy_rows":
            my_strategy_rows,

        "my_strategy_count":
            my_strategies.count(),


        # ----------------------------------------------------
        # Historical assets
        # ----------------------------------------------------

        "available_symbols":
            available_symbols,

        # Compatibility name if another template still
        # expects "symbols".
        "symbols":
            available_symbols,


        # ----------------------------------------------------
        # Current validation selections
        # ----------------------------------------------------

        "selected_validation_strategy":
            selected_validation_strategy,

        "selected_validation_symbol":
            selected_validation_symbol,

        "selected_stress_scenario":
            selected_stress_scenario,


        # ----------------------------------------------------
        # Strategy robustness
        # ----------------------------------------------------

        "robustness_test_count":
            robustness_test_count,

        "latest_user_robustness_test":
            latest_user_robustness_test,

        "latest_user_robustness_label":
            latest_user_robustness_label,

        "latest_user_robustness_explanation":
            latest_user_robustness_explanation,


        # ----------------------------------------------------
        # Stress testing
        # ----------------------------------------------------

        "stress_test_count":
            stress_test_count,

        "latest_strategy_stress_test":
            latest_strategy_stress_test,


        # ----------------------------------------------------
        # Compatibility with older list.html
        # ----------------------------------------------------

        "strategies":
            my_strategies,


        # ----------------------------------------------------
        # Page information
        # ----------------------------------------------------

        "page_title":
            "Strategy & Model Research",

    }


    # ========================================================
    # 8.15 DISPLAY STRATEGIES WORKSPACE
    # ========================================================

    return render(
        request,
        "strategy_builder/list.html",
        context,
    )


# ============================================================
# 9. LEGACY STRATEGY ROBUSTNESS ROUTE
# ============================================================

@login_required
def strategy_robustness(request):
    """
    ============================================================
    LEGACY STRATEGY ROBUSTNESS ROUTE
    ============================================================

    Previous URL:

        /strategy/robustness/

    Strategy Robustness now lives directly inside:

        /strategy/#strategyRobustnessSection

    This view is retained so existing links or bookmarks
    do not cause a 404.

    It no longer renders a separate robustness template.
    ============================================================
    """


    strategy_id = (
        request.GET.get(
            "strategy"
        )
        or
        ""
    )


    base_url = reverse(
        "strategy_builder:list"
    )


    if strategy_id:

        return redirect(
            (
                f"{base_url}"
                f"?strategy={strategy_id}"
                "#strategyRobustnessSection"
            )
        )


    return redirect(
        (
            f"{base_url}"
            "#strategyRobustnessSection"
        )
    )


# ============================================================
# 10. LEGACY STRATEGY ROBUSTNESS RESULTS ROUTE
# ============================================================

@login_required
def strategy_robustness_results(request):
    """
    ============================================================
    LEGACY STRATEGY ROBUSTNESS RESULTS ROUTE
    ============================================================

    Previous URL:

        /strategy/robustness/results/

    Robustness results are now displayed directly inside
    the Strategies workspace.

    Existing links therefore redirect to the relevant
    section of /strategy/.
    ============================================================
    """

    return redirect(
        _strategy_workspace_url(
            "strategyRobustnessSection"
        )
    )


# ============================================================
# 11. CREATE CUSTOM STRATEGY
# ============================================================

@login_required
def strategy_create(request):
    """
    ============================================================
    CREATE CUSTOM STRATEGY
    ============================================================

    URL:

        /strategy/create/


    Framework mapping:

    User
        ↓
    StrategyCreateForm
        ↓
    core.Strategy
        ↓
    StrategyRule
        ↓
    Backtest


    Once successfully created, MarketPulse sends the user
    directly to the backtesting page.
    ============================================================
    """


    # ========================================================
    # 11.1 BUILD STRATEGY FORM
    # ========================================================

    form = StrategyCreateForm(
        request.POST or None
    )


    # ========================================================
    # 11.2 PROCESS SUBMITTED FORM
    # ========================================================

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        strategy = form.save(
            request.user
        )


        messages.success(
            request,
            "Strategy created successfully."
        )


        return redirect(
            "strategy_builder:backtest",
            strategy_id=strategy.pk,
        )


    # ========================================================
    # 11.3 DISPLAY STRATEGY CREATION FORM
    # ========================================================

    context = {

        "form":
            form,

        "page_title":
            "Create Strategy",

    }


    return render(
        request,
        "strategy_builder/create.html",
        context,
    )


# ============================================================
# 12. ADD STRATEGY / MODEL TO LIBRARY
# ============================================================

@login_required
def library_item_create(request):
    """
    ============================================================
    ADD STRATEGY OR MODEL TO LIBRARY
    ============================================================

    URL:

        /strategy/library/add/


    Framework mapping:

    User
        ↓
    StrategyLibraryItemForm
        ↓
    StrategyLibraryItem
        ↓
    Strategy & Model Research page


    IMPORTANT:

    New models are stored with:

        implementation_status = "catalogued"

    because adding metadata does not mean the numerical
    implementation is complete.
    ============================================================
    """


    # ========================================================
    # 12.1 PROCESS POST REQUEST
    # ========================================================

    if request.method == "POST":

        form = StrategyLibraryItemForm(
            request.POST
        )


        if form.is_valid():

            library_item = form.save(
                commit=False
            )


            # ------------------------------------------------
            # New models begin as Catalogued
            # ------------------------------------------------

            library_item.implementation_status = (
                "catalogued"
            )


            # ------------------------------------------------
            # Make model visible
            # ------------------------------------------------

            library_item.is_active = True


            # ------------------------------------------------
            # Place custom items after built-ins
            # ------------------------------------------------

            library_item.display_order = 999


            library_item.save()


            messages.success(
                request,
                (
                    f"{library_item.name} was added "
                    f"to the MarketPulse Strategy & "
                    f"Model Library."
                ),
            )


            return redirect(
                "strategy_builder:list"
            )


    # ========================================================
    # 12.2 GET REQUEST
    # ========================================================

    else:

        form = StrategyLibraryItemForm()


    # ========================================================
    # 12.3 DISPLAY ADD MODEL FORM
    # ========================================================

    context = {

        "form":
            form,

        "page_title":
            "Add Strategy or Model",

    }


    return render(
        request,
        "strategy_builder/library_add.html",
        context,
    )


# ============================================================
# 13. BACKTEST STRATEGY
# ============================================================

@login_required
def backtest_strategy(
    request,
    strategy_id,
):
    """
    ============================================================
    RUN HISTORICAL BACKTEST
    ============================================================

    URL example:

        /strategy/5/backtest/


    Framework mapping:

    core.Strategy
        ↓
    BacktestForm
        ↓
    run_backtest()
        ↓
    Historical MarketData
        ↓
    Backtest
        ↓
    BacktestTrade
        ↓
    Results page
    ============================================================
    """


    # ========================================================
    # 13.1 RETRIEVE USER'S STRATEGY
    # ========================================================

    strategy = get_object_or_404(
        Strategy,
        pk=strategy_id,
        user=request.user,
    )


    # ========================================================
    # 13.2 BUILD BACKTEST FORM
    # ========================================================

    form = BacktestForm(
        request.POST or None
    )


    # ========================================================
    # 13.3 PROCESS BACKTEST REQUEST
    # ========================================================

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        try:

            backtest = run_backtest(
                strategy,
                **form.cleaned_data,
            )


            messages.success(
                request,
                (
                    f"Backtest completed for "
                    f"{strategy.name}."
                ),
            )


            return redirect(
                "strategy_builder:results",
                backtest_id=backtest.pk,
            )


        except Exception as error:

            messages.error(
                request,
                str(error),
            )


    # ========================================================
    # 13.4 DISPLAY BACKTEST FORM
    # ========================================================

    context = {

        "strategy":
            strategy,

        "form":
            form,

        "page_title":
            f"Backtest {strategy.name}",

    }


    return render(
        request,
        "strategy_builder/backtest_form.html",
        context,
    )


# ============================================================
# 14. BACKTEST RESULTS
# ============================================================

@login_required
def backtest_results(
    request,
    backtest_id,
):
    """
    ============================================================
    DISPLAY BACKTEST RESULTS
    ============================================================

    Framework mapping:

    Backtest
        ↓
    BacktestTrade
        ↓
    Performance metrics
        ↓
    backtest_results.html


    Results may include:

    - Total return
    - Sharpe ratio
    - Maximum drawdown
    - Win rate
    - Number of trades
    - Individual simulated trades
    ============================================================
    """


    # ========================================================
    # 14.1 RETRIEVE BACKTEST
    # ========================================================

    backtest = get_object_or_404(
        Backtest,
        pk=backtest_id,
        strategy__user=request.user,
    )


    # ========================================================
    # 14.2 RETRIEVE SIMULATED TRADES
    # ========================================================

    trades = (
        backtest.trades
        .all()
        .order_by(
            "entry_date"
        )
    )


    # ========================================================
    # 14.3 BUILD RESULTS CONTEXT
    # ========================================================

    context = {

        "backtest":
            backtest,

        "trades":
            trades,

        "page_title":
            "Backtest Results",

    }


    # ========================================================
    # 14.4 DISPLAY RESULTS
    # ========================================================

    return render(
        request,
        "strategy_builder/backtest_results.html",
        context,
    )