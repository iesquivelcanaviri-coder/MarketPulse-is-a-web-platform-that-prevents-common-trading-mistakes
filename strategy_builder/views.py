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
User Strategy
        ↓
Historical MarketData
        ↓
analysis_tools.detect_overfitting()
        ↓
OverfittingTest
        ↓
Strategy Robustness Results


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
- Future strategy/model execution

IMPORTANT ARCHITECTURE:

The old public "Analysis" section is being removed.

analysis_tools remains inside the project as an INTERNAL
analytics engine.

The user now accesses:

Strategy Robustness
    through the Strategies tab

Market Condition
    through the Data tab

Stress Testing
    through the Risk tab

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

# Django messages are used to show success and error
# notifications after actions such as creating a strategy,
# adding a library model, running a backtest or checking
# strategy robustness.
from django.contrib import messages


# login_required prevents unauthenticated users from accessing
# the Strategy Builder and strategy research functionality.
from django.contrib.auth.decorators import login_required


# Min and Max allow MarketPulse to identify the first and
# latest historical dates available for a selected symbol.
#
# This is more reliable than assuming that every imported
# dataset contains exactly the last one or two calendar years.
from django.db.models import (
    Max,
    Min,
)


# get_object_or_404 safely retrieves a database object and
# automatically returns a 404 page if the object does not exist.
#
# redirect sends the user to another named Django URL.
#
# render combines a Django template with context data.
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)


# ============================================================
# 2. CORE MODEL IMPORTS
# ============================================================

# Strategy stores strategies created by MarketPulse users.
#
# Backtest stores the historical results of running one of
# those strategies against market data.
#
# MarketData stores historical OHLCV observations imported
# through the Data section.
from core.models import (
    Backtest,
    MarketData,
    Strategy,
)


# ============================================================
# 3. INTERNAL ANALYTICS ENGINE IMPORTS
# ============================================================

# analysis_tools is no longer intended to have its own
# user-facing navigation tab.
#
# Instead it acts as an internal analytics layer.
#
# detect_overfitting() is used here because Strategy
# Robustness belongs naturally inside the Strategies section.
from analysis_tools.analyzers import (
    detect_overfitting,
)


# OverfittingTest stores the results produced by the
# robustness / overfitting analysis.
from analysis_tools.models import (
    OverfittingTest,
)


# ============================================================
# 4. STRATEGY BUILDER FORM IMPORTS
# ============================================================

# StrategyCreateForm:
#     Creates a custom user strategy.
#
# BacktestForm:
#     Collects the settings required to run a backtest.
#
# StrategyLibraryItemForm:
#     Allows additional models or strategies to be added to
#     the MarketPulse Strategy & Model Library.
from .forms import (
    BacktestForm,
    StrategyCreateForm,
    StrategyLibraryItemForm,
)


# ============================================================
# 5. STRATEGY BUILDER MODEL IMPORTS
# ============================================================

# StrategyLibraryItem stores the metadata for the built-in
# quantitative models such as:
#
# - GBM
# - ARIMA
# - GARCH
# - Random Forest
# - Fama-French
# - Markowitz
# - Black-Scholes
# - Monte Carlo
from .models import StrategyLibraryItem


# ============================================================
# 6. BACKTESTING ENGINE IMPORT
# ============================================================

# run_backtest() contains the historical simulation logic
# used by MarketPulse custom strategies.
from .backtesting import run_backtest


# ============================================================
# 7. STRATEGY & MODEL RESEARCH WORKSPACE
# ============================================================

@login_required
def strategy_list(request):
    """
    ============================================================
    STRATEGY & MODEL RESEARCH WORKSPACE
    ============================================================

    URL:

        /strategy/

    Framework mapping:

    StrategyLibraryItem
            ↓
    Quantitative model library
            ↓
    Search / filter / compare
            ↓
    Data tab / Future Model Runner


    User
        ↓
    core.Strategy
        ↓
    Backtest
        ↓
    Historical performance summary
        ↓
    Strategy Robustness
        ↓
    Overfitting Analysis


    This page combines:

    1. STRATEGY / MODEL LIBRARY

    2. USER-CREATED STRATEGIES

    3. BACKTEST PERFORMANCE

    4. STRATEGY ROBUSTNESS

    ============================================================
    """


    # ========================================================
    # 7.1 LOAD THE COMPLETE ACTIVE MODEL LIBRARY
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
    # 7.2 BUILD CATEGORY SUMMARY CARDS
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
    # 7.3 LIBRARY SUMMARY STATISTICS
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
    # 7.4 MODEL COMPARISON
    # ========================================================

    requested_compare_codes = (
        request.GET.getlist(
            "compare"
        )
    )


    # Remove duplicate selections while keeping the order
    # chosen by the user.
    requested_compare_codes = list(
        dict.fromkeys(
            requested_compare_codes
        )
    )


    comparison_message = ""


    # ========================================================
    # 7.5 LIMIT COMPARISON TO FOUR MODELS
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
    # 7.6 RETRIEVE SELECTED COMPARISON MODELS
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
    # 7.7 LOAD USER-CREATED STRATEGIES
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
    # 7.8 PREPARE STRATEGY PERFORMANCE + ROBUSTNESS SUMMARY
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

        # OverfittingTest currently stores strategy_name rather
        # than a ForeignKey to Strategy.
        #
        # Therefore MarketPulse matches by:
        #
        # user
        # +
        # strategy name
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
        # Convert technical result to clear user-facing label
        # ----------------------------------------------------

        robustness_label = None


        if latest_robustness_test:

            score = float(
                latest_robustness_test.overfitting_score
            )


            if latest_robustness_test.is_overfitted:

                if score >= 0.50:

                    robustness_label = (
                        "High Overfitting Risk"
                    )

                else:

                    robustness_label = (
                        "Moderate Overfitting Risk"
                    )

            else:

                robustness_label = (
                    "Low Overfitting Risk"
                )


        # ----------------------------------------------------
        # Add prepared row to template
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
            }
        )


    # ========================================================
    # 7.9 USER ROBUSTNESS SUMMARY
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


    # ========================================================
    # 7.10 BUILD TEMPLATE CONTEXT
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
        # Strategy robustness
        # ----------------------------------------------------

        "robustness_test_count":
            robustness_test_count,

        "latest_user_robustness_test":
            latest_user_robustness_test,


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
    # 7.11 DISPLAY STRATEGY RESEARCH PAGE
    # ========================================================

    return render(
        request,
        "strategy_builder/list.html",
        context,
    )


# ============================================================
# 8. STRATEGY ROBUSTNESS / OVERFITTING ANALYSIS
# ============================================================

@login_required
def strategy_robustness(request):
    """
    ============================================================
    STRATEGY ROBUSTNESS
    ============================================================

    URL:

        /strategy/robustness/

    User-facing question:

        "Does this strategy still behave reasonably when
         tested on historical data it was not evaluated on?"

    Technical method:

        Overfitting Analysis


    Framework mapping:

    User Strategy
        ↓
    Historical MarketData
        ↓
    Full historical period
        ↓
    70% In-Sample
        ↓
    30% Out-of-Sample
        ↓
    detect_overfitting()
        ↓
    OverfittingTest
        ↓
    Strategy Robustness Result


    IMPORTANT:

    The technical analysis remains inside:

        analysis_tools/analyzers.py

    But the USER accesses it through:

        Strategies → Strategy Robustness

    ============================================================
    """


    # ========================================================
    # 8.1 LOAD USER STRATEGIES
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
    # 8.2 LOAD AVAILABLE HISTORICAL SYMBOLS
    # ========================================================

    # Strategy robustness requires historical observations.
    #
    # Therefore this dropdown intentionally uses MarketData,
    # not Alpaca's live asset universe.
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
    # 8.3 PRESERVE USER SELECTIONS
    # ========================================================

    selected_strategy_id = (
        request.POST.get(
            "strategy",
            "",
        )
    )


    selected_symbol = (
        request.POST.get(
            "symbol",
            "",
        )
        .strip()
        .upper()
    )


    # ========================================================
    # 8.4 PROCESS ROBUSTNESS REQUEST
    # ========================================================

    if request.method == "POST":


        # ----------------------------------------------------
        # Require a strategy
        # ----------------------------------------------------

        if not selected_strategy_id:

            messages.error(
                request,
                "Select a strategy to test.",
            )


        # ----------------------------------------------------
        # Require an asset
        # ----------------------------------------------------

        elif not selected_symbol:

            messages.error(
                request,
                "Select a historical asset to test.",
            )


        else:

            # ------------------------------------------------
            # Retrieve user's strategy securely
            # ------------------------------------------------

            strategy = get_object_or_404(
                Strategy,
                pk=selected_strategy_id,
                user=request.user,
            )


            # =================================================
            # 8.5 FIND AVAILABLE HISTORICAL DATA
            # =================================================

            market_queryset = (
                MarketData.objects
                .filter(
                    symbol=selected_symbol
                )
                .order_by(
                    "date"
                )
            )


            observation_count = (
                market_queryset.count()
            )


            # ------------------------------------------------
            # Minimum observations
            # ------------------------------------------------

            if observation_count < 60:

                messages.error(
                    request,
                    (
                        f"{selected_symbol} currently has "
                        f"{observation_count} historical "
                        f"observations. MarketPulse requires "
                        f"at least 60 observations for this "
                        f"Strategy Robustness check."
                    ),
                )


            else:

                # =============================================
                # 8.6 DETERMINE TRUE DATA RANGE
                # =============================================

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
                            f"{selected_symbol}."
                        ),
                    )


                else:

                    # =========================================
                    # 8.7 DEFINE ROBUSTNESS TEST PERIOD
                    # =========================================

                    # detect_overfitting() already performs
                    # its own internal:
                    #
                    # 70% in-sample
                    # 30% out-of-sample
                    #
                    # split.
                    #
                    # Therefore the view supplies the full
                    # historical period as one test period.
                    #
                    # This avoids arbitrary hard-coded dates
                    # and makes the feature work with whatever
                    # dataset the user has actually imported.
                    test_periods = [
                        (
                            first_date,
                            last_date,
                        )
                    ]


                    # =========================================
                    # 8.8 RUN INTERNAL ANALYTICS ENGINE
                    # =========================================

                    try:

                        tests = (
                            detect_overfitting(
                                strategy,
                                selected_symbol,
                                test_periods,
                            )
                        )


                        if tests:

                            messages.success(
                                request,
                                (
                                    "Strategy Robustness "
                                    f"check completed for "
                                    f"{strategy.name} on "
                                    f"{selected_symbol}."
                                ),
                            )


                            return redirect(
                                "strategy_builder:robustness_results"
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
                                f"could not be completed: {error}"
                            ),
                        )


    # ========================================================
    # 8.9 LATEST RESULT FOR THIS USER
    # ========================================================

    latest_test = (
        OverfittingTest.objects
        .filter(
            user=request.user
        )
        .order_by(
            "-created_at"
        )
        .first()
    )


    # ========================================================
    # 8.10 DISPLAY ROBUSTNESS PAGE
    # ========================================================

    context = {

        "strategies":
            strategies,

        "symbols":
            symbols,

        "selected_strategy_id":
            selected_strategy_id,

        "selected_symbol":
            selected_symbol,

        "latest_test":
            latest_test,

        "page_title":
            "Strategy Robustness",
    }


    return render(
        request,
        "strategy_builder/robustness.html",
        context,
    )


# ============================================================
# 9. STRATEGY ROBUSTNESS RESULTS
# ============================================================

@login_required
def strategy_robustness_results(request):
    """
    ============================================================
    STRATEGY ROBUSTNESS RESULTS
    ============================================================

    URL:

        /strategy/robustness/results/

    Displays results from:

        analysis_tools.OverfittingTest

    but keeps the functionality inside the user-facing
    Strategies section.
    ============================================================
    """


    # ========================================================
    # 9.1 LOAD ONLY CURRENT USER'S TESTS
    # ========================================================

    tests = (
        OverfittingTest.objects
        .filter(
            user=request.user
        )
        .order_by(
            "-created_at"
        )
    )


    # ========================================================
    # 9.2 LATEST RESULT
    # ========================================================

    latest_test = (
        tests.first()
    )


    # ========================================================
    # 9.3 CREATE EASY-TO-UNDERSTAND INTERPRETATION
    # ========================================================

    robustness_label = None

    robustness_explanation = None


    if latest_test:

        score = float(
            latest_test.overfitting_score
        )


        # ----------------------------------------------------
        # High risk
        # ----------------------------------------------------

        if (
            latest_test.is_overfitted
            and score >= 0.50
        ):

            robustness_label = (
                "High Overfitting Risk"
            )


            robustness_explanation = (
                "Performance weakened substantially when "
                "MarketPulse moved from the in-sample period "
                "to the out-of-sample period. The historical "
                "result may depend too heavily on the data "
                "used during strategy development."
            )


        # ----------------------------------------------------
        # Moderate risk
        # ----------------------------------------------------

        elif latest_test.is_overfitted:

            robustness_label = (
                "Moderate Overfitting Risk"
            )


            robustness_explanation = (
                "The strategy showed a meaningful reduction "
                "in performance on the out-of-sample period. "
                "Additional testing across other data periods "
                "and market conditions would be useful."
            )


        # ----------------------------------------------------
        # Lower risk
        # ----------------------------------------------------

        else:

            robustness_label = (
                "Low Overfitting Risk"
            )


            robustness_explanation = (
                "The simplified robustness check did not "
                "identify a large deterioration between the "
                "in-sample and out-of-sample periods. This "
                "does not guarantee future performance."
            )


    # ========================================================
    # 9.4 DISPLAY RESULTS
    # ========================================================

    context = {

        "tests":
            tests,

        "latest_test":
            latest_test,

        "robustness_label":
            robustness_label,

        "robustness_explanation":
            robustness_explanation,

        "page_title":
            "Strategy Robustness Results",
    }


    return render(
        request,
        "strategy_builder/robustness_results.html",
        context,
    )


# ============================================================
# 10. CREATE CUSTOM STRATEGY
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

    Once the strategy is successfully created, MarketPulse
    sends the user directly to the backtesting page.
    ============================================================
    """


    # ========================================================
    # 10.1 BUILD STRATEGY FORM
    # ========================================================

    form = StrategyCreateForm(
        request.POST or None
    )


    # ========================================================
    # 10.2 PROCESS SUBMITTED FORM
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
    # 10.3 DISPLAY STRATEGY CREATION FORM
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
# 11. ADD STRATEGY / MODEL TO LIBRARY
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

    because merely adding metadata does not mean the numerical
    model has actually been implemented.
    ============================================================
    """


    # ========================================================
    # 11.1 PROCESS POST REQUEST
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
    # 11.2 GET REQUEST
    # ========================================================

    else:

        form = StrategyLibraryItemForm()


    # ========================================================
    # 11.3 DISPLAY ADD MODEL FORM
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
# 12. BACKTEST STRATEGY
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
    # 12.1 RETRIEVE USER'S STRATEGY
    # ========================================================

    strategy = get_object_or_404(
        Strategy,
        pk=strategy_id,
        user=request.user,
    )


    # ========================================================
    # 12.2 BUILD BACKTEST FORM
    # ========================================================

    form = BacktestForm(
        request.POST or None
    )


    # ========================================================
    # 12.3 PROCESS BACKTEST REQUEST
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
    # 12.4 DISPLAY BACKTEST FORM
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
# 13. BACKTEST RESULTS
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
    # 13.1 RETRIEVE BACKTEST
    # ========================================================

    backtest = get_object_or_404(
        Backtest,
        pk=backtest_id,
        strategy__user=request.user,
    )


    # ========================================================
    # 13.2 RETRIEVE SIMULATED TRADES
    # ========================================================

    trades = (
        backtest.trades
        .all()
        .order_by(
            "entry_date"
        )
    )


    # ========================================================
    # 13.3 BUILD RESULTS CONTEXT
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
    # 13.4 DISPLAY RESULTS
    # ========================================================

    return render(
        request,
        "strategy_builder/backtest_results.html",
        context,
    )