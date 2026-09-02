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
- Data analysis
- Future strategy/model execution

============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

# Django messages are used to show success and error
# notifications after actions such as creating a strategy,
# adding a library model or running a backtest.
from django.contrib import messages


# login_required prevents unauthenticated users from accessing
# the Strategy Builder and strategy research functionality.
from django.contrib.auth.decorators import login_required


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
from core.models import (
    Backtest,
    Strategy,
)


# ============================================================
# 3. STRATEGY BUILDER FORM IMPORTS
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
# 4. STRATEGY BUILDER MODEL IMPORTS
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
# 5. BACKTESTING ENGINE IMPORT
# ============================================================

# run_backtest() contains the historical simulation logic
# used by MarketPulse custom strategies.
from .backtesting import run_backtest


# ============================================================
# 6. STRATEGY & MODEL RESEARCH WORKSPACE
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
    37 quantitative models
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


    This page combines two related but different concepts:

    1. STRATEGY / MODEL LIBRARY

       Models supplied by MarketPulse such as:

       - GBM
       - Heston
       - ARIMA
       - GARCH
       - Random Forest
       - Fama-French
       - Markowitz
       - Black-Scholes
       - Monte Carlo

    2. MY STRATEGIES

       Trading strategies created by the logged-in user.

    ============================================================
    """


    # ========================================================
    # 6.1 LOAD THE COMPLETE ACTIVE MODEL LIBRARY
    # ========================================================

    # Retrieve every active model stored in
    # StrategyLibraryItem.
    #
    # Ordering keeps models arranged consistently by:
    #
    # category
    #     ↓
    # display_order
    #     ↓
    # name
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
    # 6.2 BUILD CATEGORY SUMMARY CARDS
    # ========================================================

    # The Strategy page displays one summary card for each
    # quantitative model category.
    #
    # Example:
    #
    # Stochastic Models
    # 6 models
    #
    # Time-Series Models
    # 5 models
    category_cards = []


    for (
        category_code,
        category_label,
    ) in StrategyLibraryItem.CATEGORY_CHOICES:

        # ----------------------------------------------------
        # Count models belonging to this category
        # ----------------------------------------------------

        category_count = (
            library_items
            .filter(
                category=category_code
            )
            .count()
        )


        # ----------------------------------------------------
        # Store information required by template
        # ----------------------------------------------------

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
    # 6.3 LIBRARY SUMMARY STATISTICS
    # ========================================================

    # Total number of active library models.
    total_library_models = (
        library_items.count()
    )


    # Number of models whose numerical runner has already
    # been implemented and tested.
    ready_models = (
        library_items
        .filter(
            implementation_status="ready"
        )
        .count()
    )


    # Models whose implementation exists but is still being
    # tested or evaluated.
    experimental_models = (
        library_items
        .filter(
            implementation_status="experimental"
        )
        .count()
    )


    # Models available for research and comparison but whose
    # actual numerical engine has not yet been implemented.
    catalogued_models = (
        library_items
        .filter(
            implementation_status="catalogued"
        )
        .count()
    )


    # ========================================================
    # 6.4 MODEL COMPARISON
    # ========================================================

    # Comparison checkboxes generate a URL similar to:
    #
    # /strategy/?compare=gbm&compare=arima
    #
    # getlist() is required because multiple GET parameters
    # have the same name.
    requested_compare_codes = (
        request.GET.getlist(
            "compare"
        )
    )


    # --------------------------------------------------------
    # Remove duplicate model codes
    # --------------------------------------------------------

    # dict.fromkeys() removes duplicate codes while preserving
    # the order in which the user selected them.
    requested_compare_codes = list(
        dict.fromkeys(
            requested_compare_codes
        )
    )


    comparison_message = ""


    # ========================================================
    # 6.5 LIMIT COMPARISON TO FOUR MODELS
    # ========================================================

    # Comparing too many models creates a very wide and
    # difficult-to-read table.
    #
    # MarketPulse therefore compares a maximum of four.
    if len(requested_compare_codes) > 4:

        requested_compare_codes = (
            requested_compare_codes[:4]
        )


        comparison_message = (
            "MarketPulse compares a maximum of four "
            "models at the same time."
        )


    # ========================================================
    # 6.6 RETRIEVE SELECTED COMPARISON MODELS
    # ========================================================

    compare_queryset = (
        StrategyLibraryItem.objects
        .filter(
            code__in=requested_compare_codes,
            is_active=True,
        )
    )


    # --------------------------------------------------------
    # Create lookup dictionary
    # --------------------------------------------------------

    compare_lookup = {

        item.code:
            item

        for item in compare_queryset
    }


    # --------------------------------------------------------
    # Preserve user's original comparison order
    # --------------------------------------------------------

    compare_items = [

        compare_lookup[code]

        for code in requested_compare_codes

        if code in compare_lookup
    ]


    # --------------------------------------------------------
    # Require at least two models
    # --------------------------------------------------------

    if (
        requested_compare_codes
        and len(compare_items) < 2
    ):

        comparison_message = (
            "Select at least two models to compare."
        )


    # ========================================================
    # 6.7 LOAD USER-CREATED STRATEGIES
    # ========================================================

    # A user should only see their own strategies.
    #
    # prefetch_related("rules") reduces unnecessary database
    # queries if strategy rules are later displayed.
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
    # 6.8 PREPARE STRATEGY PERFORMANCE SUMMARY
    # ========================================================

    # Each custom strategy can have several historical
    # backtests.
    #
    # The Strategy page shows:
    #
    # - Number of backtests
    # - Latest total return
    # - Latest Sharpe ratio
    # - Latest maximum drawdown
    # - Latest win rate
    my_strategy_rows = []


    for strategy in my_strategies:

        # ----------------------------------------------------
        # Find latest backtest
        # ----------------------------------------------------

        latest_backtest = (
            strategy.backtests
            .order_by(
                "-created_at"
            )
            .first()
        )


        # ----------------------------------------------------
        # Count all backtests
        # ----------------------------------------------------

        backtest_count = (
            strategy.backtests
            .count()
        )


        # ----------------------------------------------------
        # Add prepared row to template data
        # ----------------------------------------------------

        my_strategy_rows.append(
            {
                "strategy":
                    strategy,

                "latest_backtest":
                    latest_backtest,

                "backtest_count":
                    backtest_count,
            }
        )


    # ========================================================
    # 6.9 BUILD TEMPLATE CONTEXT
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
        # Compatibility
        # ----------------------------------------------------

        # The original MarketPulse list.html template used:
        #
        # strategies
        #
        # We continue providing the variable so older template
        # code does not fail during development.
        "strategies":
            my_strategies,


        # ----------------------------------------------------
        # Page information
        # ----------------------------------------------------

        "page_title":
            "Strategy & Model Research",
    }


    # ========================================================
    # 6.10 DISPLAY STRATEGY RESEARCH PAGE
    # ========================================================

    return render(
        request,
        "strategy_builder/list.html",
        context,
    )


# ============================================================
# 7. CREATE CUSTOM STRATEGY
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
    # 7.1 BUILD STRATEGY FORM
    # ========================================================

    form = StrategyCreateForm(
        request.POST or None
    )


    # ========================================================
    # 7.2 PROCESS SUBMITTED FORM
    # ========================================================

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        # StrategyCreateForm's save() method receives the
        # logged-in user so the new strategy is correctly
        # associated with its owner.
        strategy = form.save(
            request.user
        )


        # ----------------------------------------------------
        # Success message
        # ----------------------------------------------------

        messages.success(
            request,
            "Strategy created successfully."
        )


        # ----------------------------------------------------
        # Continue directly to backtesting
        # ----------------------------------------------------

        return redirect(
            "strategy_builder:backtest",
            strategy_id=strategy.pk,
        )


    # ========================================================
    # 7.3 DISPLAY STRATEGY CREATION FORM
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
# 8. ADD STRATEGY / MODEL TO LIBRARY
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

    This prevents MarketPulse from presenting an unavailable
    calculation engine as functional.
    ============================================================
    """


    # ========================================================
    # 8.1 PROCESS POST REQUEST
    # ========================================================

    if request.method == "POST":

        form = StrategyLibraryItemForm(
            request.POST
        )


        # ----------------------------------------------------
        # Validate submitted information
        # ----------------------------------------------------

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
            # Make model visible in library
            # ------------------------------------------------

            library_item.is_active = True


            # ------------------------------------------------
            # Place custom models after built-in seeded models
            # ------------------------------------------------

            library_item.display_order = 999


            # ------------------------------------------------
            # Save model
            # ------------------------------------------------

            library_item.save()


            # ------------------------------------------------
            # Success message
            # ------------------------------------------------

            messages.success(
                request,
                (
                    f"{library_item.name} was added "
                    f"to the MarketPulse Strategy & "
                    f"Model Library."
                ),
            )


            # ------------------------------------------------
            # Return to Strategy Research page
            # ------------------------------------------------

            return redirect(
                "strategy_builder:list"
            )


    # ========================================================
    # 8.2 GET REQUEST
    # ========================================================

    else:

        form = StrategyLibraryItemForm()


    # ========================================================
    # 8.3 DISPLAY ADD MODEL FORM
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
# 9. BACKTEST STRATEGY
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
    # 9.1 RETRIEVE USER'S STRATEGY
    # ========================================================

    # Both primary key and user are checked.
    #
    # This prevents one logged-in user from backtesting a
    # strategy owned by someone else.
    strategy = get_object_or_404(
        Strategy,
        pk=strategy_id,
        user=request.user,
    )


    # ========================================================
    # 9.2 BUILD BACKTEST FORM
    # ========================================================

    form = BacktestForm(
        request.POST or None
    )


    # ========================================================
    # 9.3 PROCESS BACKTEST REQUEST
    # ========================================================

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        try:

            # ------------------------------------------------
            # Run historical backtest
            # ------------------------------------------------

            backtest = run_backtest(
                strategy,
                **form.cleaned_data,
            )


            # ------------------------------------------------
            # Redirect to results
            # ------------------------------------------------

            return redirect(
                "strategy_builder:results",
                backtest_id=backtest.pk,
            )


        except Exception as error:

            # ------------------------------------------------
            # Display backtesting error without crashing page
            # ------------------------------------------------

            messages.error(
                request,
                str(error),
            )


    # ========================================================
    # 9.4 DISPLAY BACKTEST FORM
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
# 10. BACKTEST RESULTS
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
    # 10.1 RETRIEVE BACKTEST
    # ========================================================

    # Ensure the requested backtest belongs to a strategy
    # owned by the currently logged-in user.
    backtest = get_object_or_404(
        Backtest,
        pk=backtest_id,
        strategy__user=request.user,
    )


    # ========================================================
    # 10.2 RETRIEVE SIMULATED TRADES
    # ========================================================

    trades = (
        backtest.trades
        .all()
        .order_by(
            "entry_date"
        )
    )


    # ========================================================
    # 10.3 BUILD RESULTS CONTEXT
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
    # 10.4 DISPLAY RESULTS
    # ========================================================

    return render(
        request,
        "strategy_builder/backtest_results.html",
        context,
    )