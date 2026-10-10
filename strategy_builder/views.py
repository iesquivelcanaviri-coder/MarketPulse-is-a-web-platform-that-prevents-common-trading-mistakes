"""
============================================================
MARKETPULSE - STRATEGY BUILDER VIEWS
============================================================

Framework mapping:
Django URLs → these views → forms / models / analytics
→ template context → HTML response.

Strategy & Model Library:
StrategyLibraryItem → strategy_list()
→ strategy_builder/list.html
→ Browse / Filter / Compare.

Custom Strategy:
StrategyCreateForm
    ↓
strategy_list()
    ↓
core.Strategy
    ↓
Strategy Rules
    ↓
My Strategies section
    ↓
Backtesting.

Portfolio Risk Calculator:
RiskPlannerForm
    ↓
strategy_list()
    ↓
Selected user Strategy
    +
Alpaca current price / stored MarketData
    ↓
risk_management.calculators
    ↓
Portfolio risk result
    ↓
Displayed inside My Strategies without leaving /strategy/.

Historical Backtesting:
BacktestForm
    ↓
run_backtest()
    ↓
core.Backtest
    ↓
BacktestTrade
    ↓
backtest_results().

Strategy Robustness:
The analytical backend is retained for compatibility.

User Strategy
    ↓
Historical MarketData
    ↓
detect_overfitting()
    ↓
OverfittingTest.

The separate visible Strategy Robustness section is no longer
required on the Strategies workspace.

Stress Testing:
The analytical backend is retained for compatibility.

User Strategy
    ↓
Historical MarketData
    ↓
run_stress_test()
    ↓
StressTest.

The separate visible Stress Testing section is no longer
required on the Strategies workspace.

Library Creation:
StrategyLibraryItemForm
    ↓
StrategyLibraryItem
    ↓
Strategy & Model Library.

Student understanding:
Views coordinate HTTP requests and responses.
Forms validate submitted user data.
Models provide database access through Django's ORM.
Imported analytical functions perform calculations.
Templates display the context supplied by views.

Programming concepts:
Imports, functions, decorators, parameters, return values,
variables, strings, numbers, Booleans, lists, tuples,
dictionaries, loops, conditions, comprehensions, slicing,
unpacking, method chaining and exception handling.

Important workflow changes:
Creating a strategy now happens inside /strategy/.
The Portfolio Risk Calculator is also prepared and processed
inside /strategy/ so the user does not need to open /risk/calculator/.

The old /strategy/create/ URL remains available only as a
compatibility redirect back to the My Strategies section.

analysis_tools remains an internal analytics layer.
Market Condition remains part of the Data workflow.

These notes describe this view's calls. Details inside imported
forms and calculation engines belong to their own source files.
============================================================
"""


# ============================================================
# 1. DJANGO IMPORTS — REUSING FRAMEWORK FUNCTIONS
# ============================================================

from django.contrib import messages  # Import: I use Django's temporary user-notification system.

from django.contrib.auth.decorators import login_required  # Import: I require authentication before selected views run.

from django.db.models import Max, Min  # Import: I use database aggregation functions for historical date ranges.

from django.shortcuts import get_object_or_404, redirect, render  # Import: I use Django helpers for retrieval, redirection and template rendering.

from django.urls import reverse  # Import: I convert named Django URL routes into actual URL strings.


# ============================================================
# 2. CORE MODELS — DATABASE ACCESS
# ============================================================

from core.models import Backtest, MarketData, Strategy  # Model imports: I access shared backtests, market data and strategies.


# ============================================================
# 3. INTERNAL ANALYTICS — CALCULATIONS AND STORED RESULTS
# ============================================================

from analysis_tools.analyzers import detect_overfitting, run_stress_test  # Function imports: I reuse the project's analytical calculation functions.

from analysis_tools.models import OverfittingTest, StressTest  # Model imports: I retrieve stored analytical results.


# ============================================================
# 4. LOCAL FORMS — SUBMITTED DATA
# ============================================================

from .forms import BacktestForm, StrategyCreateForm, StrategyLibraryItemForm  # Relative imports: I load forms belonging to strategy_builder.


# ============================================================
# 5. LOCAL LIBRARY MODEL
# ============================================================

from .models import StrategyLibraryItem  # Relative model import: I access strategy and model catalogue metadata.


# ============================================================
# 6. BACKTESTING ENGINE
# ============================================================

from .backtesting import run_backtest  # Relative import: I use the project's historical backtesting function.


# ============================================================
# 6.1 RISK PLANNER — REUSE THE EXISTING RISK FEATURE
# ============================================================

from risk_management.forms import RiskPlannerForm  # Cross-app import: I reuse the existing validated Trade & Portfolio Risk Planner form.

from risk_management.calculators import (  # Cross-app imports: I reuse the existing numerical risk engine rather than duplicating its formulas.
    calculate_trade_risk_plan,  # Function import: I calculate position size, stop, planned loss and potential reward.
    get_market_risk_context,  # Function import: I retrieve ATR, volatility, drawdown and stored-price context for an asset.
)  # Closing parenthesis: I finish the risk-calculator imports.

from data_management.services.alpaca import (  # Service imports: I reuse the server-side Alpaca integration already used by Risk.
    AlpacaServiceError,  # Exception import: I handle an expected Alpaca service failure without breaking the page.
    get_stock_snapshot,  # Function import: I request the latest available price when the user leaves entry price blank.
)  # Closing parenthesis: I finish the Alpaca-service imports.


# ============================================================
# 7. HELPERS — SMALL REUSABLE FUNCTIONS
# ============================================================

def _strategy_workspace_url(anchor=None):  # Function definition: I create a reusable helper with an optional anchor argument.
    """Return the Strategies URL, optionally followed by a section anchor."""

    url = reverse("strategy_builder:list")  # Function call: I resolve the named Strategies workspace URL.

    if anchor:  # Conditional: I check whether a browser section anchor was supplied.
        return f"{url}#{anchor}"  # Formatted string: I append the section fragment to the workspace URL.

    return url  # Return statement: I provide the plain Strategies URL when no anchor is needed.


def _get_available_historical_symbols():  # Function definition: I create a helper that takes no explicit arguments.
    """Return distinct symbols stored in core.MarketData."""

    return list(  # Return and conversion: I evaluate the QuerySet and return an ordinary Python list.
        MarketData.objects  # ORM manager: I begin a query against stored historical market data.
        .order_by("symbol")  # Method chaining: I sort records alphabetically by symbol.
        .values_list("symbol", flat=True)  # Query projection: I retrieve only symbol values rather than complete objects.
        .distinct()  # Query method: I remove duplicate ticker symbols.
    )  # Closing parenthesis: I finish the list conversion.


def _robustness_interpretation(test):  # Function definition: I receive one robustness-result object.
    """Return a user-facing label and explanation as a two-item tuple."""

    if not test:  # Conditional and truthiness: I handle an absent result.
        return (None, None)  # Tuple return: I provide two empty values when no test exists.

    score = float(test.overfitting_score)  # Type conversion: I convert the stored score into a Python float.

    if test.is_overfitted and score >= 0.50:  # Boolean logic: I require both overfitting and the higher score threshold.
        return (  # Return statement: I provide the high-risk interpretation.
            "High Overfitting Risk",  # String: I provide the readable label.
            (
                "Performance weakened substantially when "  # Adjacent string: I begin the explanation.
                "MarketPulse moved from the in-sample period "  # String continuation: I identify the historical comparison.
                "to the out-of-sample period. The historical "  # String continuation: I describe the performance change.
                "result may depend too heavily on the data "  # String continuation: I explain the possible problem.
                "used during strategy development."  # String: I finish the explanation.
            ),  # Closing parenthesis: I finish the explanation expression.
        )  # Closing parenthesis: I finish the tuple.

    if test.is_overfitted:  # Conditional: I handle overfitting below the previous score threshold.
        return (  # Return statement: I provide the moderate-risk interpretation.
            "Moderate Overfitting Risk",  # String: I provide the readable label.
            (
                "The strategy showed a meaningful reduction "  # Adjacent string: I begin the explanation.
                "in performance on the out-of-sample period. "  # String continuation: I identify where performance weakened.
                "Additional testing across other data periods "  # String continuation: I describe useful additional research.
                "and market conditions would be useful."  # String: I finish the explanation.
            ),  # Closing parenthesis: I finish the explanation.
        )  # Closing parenthesis: I finish the tuple.

    return (  # Return statement: I handle the remaining non-overfitted result.
        "Low Overfitting Risk",  # String: I provide the readable label.
        (
            "The simplified robustness check did not identify "  # Adjacent string: I begin the explanation.
            "a large deterioration between the in-sample and "  # String continuation: I describe the comparison.
            "out-of-sample periods. This does not guarantee "  # String continuation: I state an important limitation.
            "future performance."  # String: I finish the explanation.
        ),  # Closing parenthesis: I finish the explanation.
    )  # Closing parenthesis: I finish the tuple.


# ============================================================
# 8. STRATEGIES WORKSPACE — MAIN REQUEST HANDLER
# ============================================================

@login_required  # Decorator: Django requires a signed-in user before this view executes.
def strategy_list(request):  # Function definition: Django passes the current HTTP request object.
    """
    Render the combined Strategies workspace.

    GET:
    - prepares the model library;
    - prepares comparison data;
    - prepares the user's saved strategies;
    - prepares an empty inline strategy-creation form;
    - prepares the existing RiskPlannerForm for same-page use.

    POST:
    - creates a new strategy inside the same Strategies page;
    - calculates portfolio/trade risk inside the same Strategies page;
    - retains compatibility with robustness processing;
    - retains compatibility with stress-test processing.
    """

    # ========================================================
    # 8.1 ACTIVE MODEL LIBRARY
    # ========================================================

    library_items = (  # Variable assignment: I store a QuerySet of active library entries.
        StrategyLibraryItem.objects  # ORM manager: I access strategy-library records.
        .filter(is_active=True)  # Query filter: I include only entries currently marked active.
        .order_by("category", "display_order", "name")  # Query ordering: I organise models consistently for display.
    )  # Closing parenthesis: I finish the QuerySet expression.


    # ========================================================
    # 8.2 CATEGORY SUMMARY CARDS
    # ========================================================

    category_cards = []  # List creation: I start an empty collection for category summaries.

    for category_code, category_label in StrategyLibraryItem.CATEGORY_CHOICES:  # Loop and tuple unpacking: I process every configured category.
        category_count = library_items.filter(category=category_code).count()  # ORM filtering: I count active models belonging to this category.

        category_cards.append({  # List method: I add one dictionary containing category display data.
            "code": category_code,  # Dictionary entry: I store the machine-readable category code.
            "label": category_label,  # Dictionary entry: I store the human-readable category name.
            "count": category_count,  # Dictionary entry: I store how many models belong to this category.
        })  # Closing parenthesis: I finish appending the dictionary.


    # ========================================================
    # 8.3 LIBRARY COUNTS
    # ========================================================

    total_library_models = library_items.count()  # ORM count: I calculate the number of active library models.

    ready_models = library_items.filter(
        implementation_status="ready"
    ).count()  # ORM filtering and count: I calculate how many models are ready to run.

    experimental_models = library_items.filter(
        implementation_status="experimental"
    ).count()  # ORM filtering and count: I calculate how many models are experimental.

    catalogued_models = library_items.filter(
        implementation_status="catalogued"
    ).count()  # ORM filtering and count: I calculate how many models currently contain catalogue metadata only.


    # ========================================================
    # 8.4 COMPARISON INPUT
    # ========================================================

    requested_compare_codes = request.GET.getlist(
        "compare"
    )  # Request access: I retrieve every repeated compare query-string value.

    requested_compare_codes = list(
        dict.fromkeys(requested_compare_codes)
    )  # Dictionary keys and list conversion: I remove duplicates while preserving requested order.

    comparison_message = ""  # String assignment: I begin with no model-comparison feedback.


    # ========================================================
    # 8.5 SERVER-SIDE COMPARISON LIMIT
    # ========================================================

    if len(requested_compare_codes) > 4:  # Conditional: I enforce a maximum of four models even if browser controls are bypassed.
        requested_compare_codes = requested_compare_codes[:4]  # List slicing: I retain only the first four submitted model codes.

        comparison_message = (  # String assignment: I prepare user feedback explaining the limit.
            "MarketPulse compares a maximum of four "  # Adjacent string: I begin the feedback.
            "models at the same time."  # String: I finish the feedback.
        )  # Closing parenthesis: I finish the message expression.


    # ========================================================
    # 8.6 RETRIEVE VALID COMPARISON ITEMS
    # ========================================================

    compare_queryset = StrategyLibraryItem.objects.filter(  # ORM query: I retrieve valid active library records.
        code__in=requested_compare_codes,  # Field lookup: I match any requested model code.
        is_active=True,  # Boolean filter: I exclude inactive catalogue entries.
    )  # Closing parenthesis: I finish the query.

    compare_lookup = {
        item.code: item
        for item in compare_queryset
    }  # Dictionary comprehension: I map each valid model code to its model object.

    compare_items = [
        compare_lookup[code]
        for code in requested_compare_codes
        if code in compare_lookup
    ]  # List comprehension: I keep valid models in the same order requested by the browser.

    if requested_compare_codes and len(compare_items) < 2:  # Boolean condition: I detect a comparison request containing fewer than two valid models.
        comparison_message = "Select at least two models to compare."  # String assignment: I replace the feedback with the minimum-selection message.


    # ========================================================
    # 8.7 USER-OWNED STRATEGIES
    # ========================================================

    my_strategies = (  # Variable assignment: I prepare the current user's strategy QuerySet.
        Strategy.objects  # ORM manager: I access Strategy database records.
        .filter(user=request.user)  # Ownership filter: I show only strategies belonging to the signed-in user.
        .prefetch_related("rules")  # Query optimisation: I retrieve related rules efficiently for later display.
        .order_by("-created_at")  # Ordering: I place the newest strategies first.
    )  # Closing parenthesis: I finish the QuerySet expression.


    # ========================================================
    # 8.8 STORED HISTORICAL SYMBOLS
    # ========================================================

    available_symbols = _get_available_historical_symbols()  # Function call: I retrieve the unique symbols stored in MarketData.


    # ========================================================
    # 8.9 IDENTIFY THE SUBMITTED SAME-PAGE ACTION
    # ========================================================

    action = (
        request.POST.get("action", "")
        if request.method == "POST"
        else ""
    )  # Conditional expression: I read the hidden action field only for submitted POST requests.


    # ========================================================
    # 8.10 INLINE STRATEGY CREATION FORM
    # ========================================================

    strategy_form = StrategyCreateForm(
        request.POST if action == "create_strategy" else None
    )  # Form creation: I bind submitted data only when the inline strategy form caused the POST request.


    # ========================================================
    # 8.10.1 INLINE PORTFOLIO RISK CALCULATOR FORM
    # ========================================================

    risk_form = RiskPlannerForm(  # Cross-app form creation: I reuse the existing Risk form on this Strategies page.
        request.POST if action == "calculate_risk" else None,  # Conditional binding: I bind POST data only when the Risk calculator submitted the request.
        initial={  # Dictionary: I preserve the same sensible starting values used by the standalone Risk page.
            "symbol": available_symbols[0] if available_symbols else "",  # Conditional expression: I initialise the symbol from stored historical data when available.
            "trading_capital": 10000,  # Integer: I initialise the simulated portfolio value.
            "risk_percentage": 1,  # Integer: I initialise maximum risk at one percent.
            "currency": "USD",  # String: I initialise the current supported market currency.
            "direction": "long",  # String: I initialise the trade direction.
            "stop_method": "percentage",  # String: I initialise the stop method.
            "stop_loss_percentage": 5,  # Integer: I initialise the percentage stop distance.
            "atr_multiplier": 2,  # Integer: I initialise the ATR multiplier.
        },  # Closing brace: I finish the initial-value dictionary.
        prefix="risk",  # Prefix: I keep Risk input names and HTML IDs separate from StrategyCreateForm fields on the same page.
    )  # Closing parenthesis: I finish building the same-page Risk form.

    risk_result = None  # Initial state: no portfolio-risk result exists until the user submits the Risk calculator.
    selected_risk_strategy = None  # Initial state: no strategy is selected for Risk on an ordinary GET request.
    selected_risk_strategy_id = (  # Variable assignment: I preserve the selected strategy for the Risk dropdown.
        request.POST.get("risk_strategy")  # Request lookup: I first read the Risk calculator's submitted strategy ID.
        or request.GET.get("risk_strategy")  # Logical OR: I optionally allow a strategy to be preselected through the query string.
        or ""  # Empty string: I provide a safe fallback when no strategy is selected.
    )  # Closing parenthesis: I finish the selected-ID expression.
    risk_market_context = None  # Initial state: historical context is loaded only when the Risk calculation needs it.


    # ========================================================
    # 8.11 PRESERVE ANALYTICS FORM SELECTIONS
    # ========================================================

    selected_validation_strategy = (  # Variable assignment: I preserve a submitted or query-string strategy identifier.
        request.POST.get("strategy")  # Request data: I first look for the strategy in POST data.
        or request.GET.get("strategy")  # Logical OR: I next look for a strategy in the query string.
        or ""  # Empty string: I provide a safe fallback when no strategy was supplied.
    )  # Closing parenthesis: I finish the selection expression.

    selected_validation_symbol = (  # Variable assignment: I prepare the selected historical symbol.
        request.POST.get("symbol")  # Request data: I first inspect submitted POST data.
        or request.GET.get("symbol")  # Logical OR: I then inspect the query string.
        or ""  # Empty string: I provide a safe fallback.
    ).strip().upper()  # String methods: I remove surrounding whitespace and normalise the ticker to uppercase.

    selected_stress_scenario = (
        request.POST.get("scenario")
        or "crash"
    )  # Logical OR: I retain a submitted stress scenario or use crash as the compatibility default.


    # ========================================================
    # 8.12 DISPATCH SAME-PAGE POST ACTIONS
    # ========================================================

    if request.method == "POST":  # Conditional: I process submitted forms only for POST requests.

        # ----------------------------------------------------
        # 8.12.1 CREATE STRATEGY INSIDE MY STRATEGIES
        # ----------------------------------------------------

        if action == "create_strategy":  # Equality comparison: I identify the inline strategy-creation submission.

            if strategy_form.is_valid():  # Form validation: I continue only when every field and cross-field rule is valid.
                strategy = strategy_form.save(
                    request.user
                )  # Custom form method: I create the Strategy and its associated strategy rules for this user.

                messages.success(  # Django messages: I prepare temporary confirmation feedback.
                    request,  # Request argument: I attach the message to this user's request.
                    f"{strategy.name} was created successfully.",  # Formatted string: I include the new strategy's readable name.
                )  # Closing parenthesis: I finish the success message.

                return redirect(
                    _strategy_workspace_url("myStrategiesSection")
                )  # Redirect: I return to My Strategies instead of opening another page.

            messages.error(
                request,
                "Please correct the strategy form errors below.",
            )  # Error feedback: I tell the user why the inline form remains open.


        # ----------------------------------------------------
        # 8.12.2 PORTFOLIO RISK — CALCULATE ON THIS SAME PAGE
        # ----------------------------------------------------

        elif action == "calculate_risk":  # Equality comparison: I identify the inline Portfolio Risk Calculator submission.

            if not selected_risk_strategy_id:  # Truthiness condition: I require the user to choose one of their saved strategies.
                messages.error(
                    request,
                    "Select one of your strategies first.",
                )  # Error feedback: I explain the missing strategy selection.

            else:  # Else branch: I continue when a strategy ID was submitted.
                selected_risk_strategy = get_object_or_404(  # Secure retrieval: I load only a strategy owned by the signed-in user.
                    Strategy,  # Model argument: I query the shared Strategy model.
                    pk=selected_risk_strategy_id,  # Primary-key lookup: I match the strategy chosen in the Risk dropdown.
                    user=request.user,  # Ownership filter: I prevent another user's strategy from being used.
                )  # Closing parenthesis: I finish secure strategy retrieval.

                if risk_form.is_valid():  # Form validation: I continue only when all existing RiskPlannerForm rules pass.
                    cleaned = risk_form.cleaned_data  # Attribute access: I retrieve validated and converted Risk input values.
                    selected_risk_symbol = (  # Variable assignment: I prepare the submitted ticker for services and database queries.
                        cleaned["symbol"]  # Dictionary indexing: I read the validated symbol.
                        .strip()  # String method: I remove surrounding whitespace.
                        .upper()  # Method chaining: I normalise the ticker to uppercase.
                    )  # Closing parenthesis: I finish symbol normalisation.

                    risk_market_context = get_market_risk_context(
                        selected_risk_symbol
                    )  # Function call: I reuse the existing historical Risk helper for ATR, volatility, drawdown and stored-close context.

                    # ----------------------------------------
                    # 8.12.2.1 ENTRY PRICE — MANUAL FIRST
                    # ----------------------------------------

                    entry_price = cleaned.get(
                        "entry_price"
                    )  # Dictionary lookup: I use the user's manually supplied entry price when available.

                    # ----------------------------------------
                    # 8.12.2.2 ALPACA PRICE FALLBACK
                    # ----------------------------------------

                    if entry_price is None:  # Identity comparison: I contact Alpaca only when the user left entry price blank.
                        try:  # Exception handling: I protect the Strategies page from an expected Alpaca service failure.
                            alpaca_snapshot = get_stock_snapshot(
                                selected_risk_symbol
                            )  # Service call: I request the server-side Alpaca snapshot for the selected ticker.
                            entry_price = alpaca_snapshot.get(
                                "latest_price"
                            )  # Dictionary lookup: I read the latest available price from the service result.
                        except AlpacaServiceError:  # Exception branch: I handle the project's known Alpaca service error.
                            entry_price = None  # Assignment: I leave the price unavailable so the stored-close fallback can run.

                    # ----------------------------------------
                    # 8.12.2.3 STORED HISTORICAL CLOSE FALLBACK
                    # ----------------------------------------

                    if entry_price is None and risk_market_context:  # Boolean AND: I use stored history only if the current price is still unavailable.
                        entry_price = risk_market_context.get(
                            "latest_close"
                        )  # Dictionary lookup: I retrieve the latest stored historical closing price.

                    if entry_price is None:  # Identity comparison: I detect failure of all three price sources.
                        risk_form.add_error(  # Form method: I attach a useful validation-style message to the existing entry-price field.
                            "entry_price",  # String: I identify the field that needs user input.
                            (
                                "MarketPulse could not obtain a current "
                                "Alpaca price or a stored historical price. "
                                "Enter an entry price manually."
                            ),  # String expression: I explain the fallback failure and next step.
                        )  # Closing parenthesis: I finish adding the field error.

                    else:  # Else branch: I have a usable entry price and can calculate the risk plan.
                        try:  # Exception handling: I convert calculation problems into form feedback instead of breaking the page.
                            risk_result = calculate_trade_risk_plan(  # Function call: I reuse the established Risk engine without duplicating formulas here.
                                trading_capital=cleaned["trading_capital"],  # Keyword argument: I supply validated simulated portfolio capital.
                                risk_percentage=cleaned["risk_percentage"],  # Keyword argument: I supply the maximum accepted loss percentage.
                                entry_price=entry_price,  # Keyword argument: I supply manual, Alpaca or stored entry price.
                                direction=cleaned["direction"],  # Keyword argument: I supply long or short direction.
                                stop_method=cleaned["stop_method"],  # Keyword argument: I supply percentage, ATR or fixed stop mode.
                                stop_loss_percentage=cleaned.get(
                                    "stop_loss_percentage"
                                ),  # Optional keyword argument: I supply the percentage stop distance when relevant.
                                fixed_stop_price=cleaned.get(
                                    "stop_price"
                                ),  # Optional keyword argument: I supply the exact stop price when relevant.
                                atr=(
                                    risk_market_context.get("atr_14")
                                    if risk_market_context
                                    else None
                                ),  # Conditional expression: I supply historical ATR when stored market context exists.
                                atr_multiplier=cleaned.get(
                                    "atr_multiplier"
                                ),  # Optional keyword argument: I supply the chosen ATR multiplier.
                                target_price=cleaned.get(
                                    "target_price"
                                ),  # Optional keyword argument: I supply a favourable target for potential-reward calculation.
                            )  # Closing parenthesis: I finish the existing Risk calculation.

                            # --------------------------------
                            # 8.12.2.4 ADD DISPLAY CONTEXT
                            # --------------------------------

                            risk_result["strategy_name"] = (
                                selected_risk_strategy.name
                            )  # Dictionary assignment: I identify the strategy used for this portfolio-risk simulation.
                            risk_result["strategy_id"] = (
                                selected_risk_strategy.pk
                            )  # Dictionary assignment: I retain its primary key for template links or data attributes.
                            risk_result["symbol"] = selected_risk_symbol  # Dictionary assignment: I include the normalised asset ticker.
                            risk_result["currency"] = cleaned.get(
                                "currency",
                                "USD",
                            )  # Dictionary lookup with default: I include the selected market currency.
                            risk_result["trading_capital"] = float(
                                cleaned["trading_capital"]
                            )  # Type conversion: I expose capital as a simple numeric display value.
                            risk_result["risk_percentage"] = float(
                                cleaned["risk_percentage"]
                            )  # Type conversion: I expose the requested maximum-risk percentage.

                            # --------------------------------
                            # 8.12.2.5 LATEST MATCHING BACKTEST
                            # --------------------------------

                            latest_risk_backtest = (
                                selected_risk_strategy.backtests  # Related manager: I start from backtests belonging to the selected strategy.
                                .filter(symbol=selected_risk_symbol)  # Query filter: I use only backtests for the same asset as this Risk calculation.
                                .order_by("-created_at")  # Ordering: I place the newest matching backtest first.
                                .first()  # Query evaluation: I retrieve one saved backtest or None.
                            )  # Closing parenthesis: I finish the latest-backtest query.

                            risk_result["latest_backtest"] = (
                                latest_risk_backtest
                            )  # Dictionary assignment: I make the matching historical performance object available to the template.
                            risk_result["historical_win_rate_pct"] = None  # Initial value: no historical percentage exists without a matching backtest.
                            risk_result["historical_loss_rate_pct"] = None  # Initial value: no complementary loss percentage exists yet.
                            risk_result["historical_expectancy"] = None  # Initial value: expectancy also requires historical win rate and a target reward.
                            risk_result["backtest_total_return_pct"] = None  # Initial value: converted historical total return is unavailable without a backtest.
                            risk_result["backtest_max_drawdown_pct"] = None  # Initial value: converted historical drawdown is unavailable without a backtest.

                            if latest_risk_backtest:  # Truthiness condition: I add historical portfolio-manager metrics when a matching backtest exists.
                                historical_win_rate = float(
                                    latest_risk_backtest.win_rate
                                )  # Type conversion: the backtesting engine stores win rate as a fraction between zero and one.
                                historical_loss_rate = (
                                    1 - historical_win_rate
                                )  # Arithmetic: I derive the complementary historical losing-trade fraction.

                                risk_result["historical_win_rate_pct"] = round(
                                    historical_win_rate * 100,
                                    2,
                                )  # Percentage conversion: I prepare the historical win rate for readable display.
                                risk_result["historical_loss_rate_pct"] = round(
                                    historical_loss_rate * 100,
                                    2,
                                )  # Percentage conversion: I prepare the historical loss rate for readable display.
                                risk_result["backtest_total_return_pct"] = round(
                                    float(latest_risk_backtest.total_return) * 100,
                                    2,
                                )  # Percentage conversion: I prepare the saved fractional backtest return for portfolio-manager display.
                                risk_result["backtest_max_drawdown_pct"] = round(
                                    float(latest_risk_backtest.max_drawdown) * 100,
                                    2,
                                )  # Percentage conversion: I prepare the saved fractional maximum drawdown for readable display.

                                if risk_result.get("potential_reward") is not None:  # Condition: expectancy needs a user-supplied target and therefore a potential reward.
                                    expected_value = (  # Variable assignment: I calculate a simple historical expectancy from the saved win rate.
                                        historical_win_rate
                                        * risk_result["potential_reward"]
                                        - historical_loss_rate
                                        * risk_result["planned_loss"]
                                    )  # Arithmetic: historical win chance × target reward minus historical loss chance × planned stop loss.
                                    risk_result["historical_expectancy"] = round(
                                        expected_value,
                                        2,
                                    )  # Dictionary assignment: I store the rounded simulated expectancy for display.

                        except ValueError as error:  # Exception handling: I catch validation-style failures raised by the existing Risk engine.
                            risk_form.add_error(
                                None,
                                str(error),
                            )  # Form-wide error: I show the existing calculator's message inside the inline form.


        # ----------------------------------------------------
        # 8.12.3 ROBUSTNESS — BACKEND RETAINED FOR COMPATIBILITY
        # ----------------------------------------------------

        elif action == "robustness":  # Equality comparison: I retain processing for older or external robustness submissions.

            if not selected_validation_strategy:  # Conditional: I require a selected strategy.
                messages.error(
                    request,
                    "Select a strategy to test.",
                )  # Error feedback: I explain that a strategy must be supplied.

            elif not selected_validation_symbol:  # Alternative condition: I require a historical asset.
                messages.error(
                    request,
                    "Select a historical asset to test.",
                )  # Error feedback: I explain that a stored-data symbol must be supplied.

            else:  # Else branch: I continue when both required selections exist.
                strategy = get_object_or_404(  # Secure retrieval: I load the requested strategy or return HTTP 404.
                    Strategy,  # Model argument: I query Strategy.
                    pk=selected_validation_strategy,  # Primary-key filter: I match the submitted strategy ID.
                    user=request.user,  # Ownership filter: I prevent access to another user's strategy.
                )  # Closing parenthesis: I finish the retrieval.

                market_queryset = (  # Variable assignment: I prepare historical observations for the selected symbol.
                    MarketData.objects  # ORM manager: I access stored MarketData.
                    .filter(symbol=selected_validation_symbol)  # Query filter: I include only the selected ticker.
                    .order_by("date")  # Ordering: I arrange observations chronologically.
                )  # Closing parenthesis: I finish the query.

                observation_count = market_queryset.count()  # ORM count: I determine how much historical data is available.

                if observation_count < 60:  # Validation condition: I enforce the existing minimum-data requirement.
                    messages.error(  # Error message: I explain the insufficient-data problem.
                        request,  # Request argument: I attach the message to this request.
                        (
                            f"{selected_validation_symbol} currently "  # Formatted string: I identify the selected symbol.
                            f"has {observation_count} historical "  # Formatted string: I include the available observation count.
                            f"observations. MarketPulse requires at "  # String continuation: I introduce the minimum.
                            f"least 60 observations for this "  # String continuation: I specify the minimum number.
                            f"Strategy Robustness check."  # String: I identify the affected analysis.
                        ),  # Closing parenthesis: I finish the message.
                    )  # Closing parenthesis: I finish creating the error notification.

                else:  # Else branch: I continue when enough observations exist.
                    date_range = market_queryset.aggregate(  # ORM aggregation: I calculate the available historical date boundaries.
                        first_date=Min("date"),  # Aggregation: I retrieve the earliest stored date.
                        last_date=Max("date"),  # Aggregation: I retrieve the latest stored date.
                    )  # Closing parenthesis: I finish aggregation.

                    first_date = date_range["first_date"]  # Dictionary indexing: I extract the earliest date.
                    last_date = date_range["last_date"]  # Dictionary indexing: I extract the latest date.

                    if (
                        first_date is None
                        or last_date is None
                        or first_date >= last_date
                    ):  # Boolean OR: I reject missing dates or an invalid historical period.

                        messages.error(  # Error feedback: I explain that the period cannot be used.
                            request,  # Request argument: I attach the feedback.
                            (
                                "MarketPulse could not determine "  # String: I begin the explanation.
                                "a valid historical period for "  # Adjacent string: I continue the explanation.
                                f"{selected_validation_symbol}."  # Formatted string: I identify the selected ticker.
                            ),  # Closing parenthesis: I finish the message.
                        )  # Closing parenthesis: I finish error creation.

                    else:  # Else branch: I continue with a valid historical date range.
                        test_periods = [
                            (first_date, last_date)
                        ]  # List containing tuple: I supply the analytical engine with the available period.

                        try:  # Exception handling: I protect the request from analytical calculation failures.

                            tests = detect_overfitting(  # Function call: I delegate robustness analysis to the existing engine.
                                strategy,  # Argument: I supply the owned Strategy object.
                                selected_validation_symbol,  # Argument: I supply the selected historical ticker.
                                test_periods,  # Argument: I supply the historical testing period.
                            )  # Closing parenthesis: I finish the analytical call.

                            if tests:  # Truthiness condition: I treat a returned result as successful completion.
                                messages.success(  # Success feedback: I tell the user the compatibility calculation completed.
                                    request,  # Request argument: I attach the feedback.
                                    (
                                        "Strategy Robustness check "  # String: I begin the success message.
                                        f"completed for "  # Formatted-string continuation: I prepare the strategy name.
                                        f"{strategy.name} on "  # Formatted string: I include the strategy.
                                        f"{selected_validation_symbol}."  # Formatted string: I include the historical ticker.
                                    ),  # Closing parenthesis: I finish the message.
                                )  # Closing parenthesis: I finish success feedback.

                                return redirect(
                                    _strategy_workspace_url("myStrategiesSection")
                                )  # Redirect: The removed robustness section is replaced by the existing My Strategies anchor.

                            messages.error(  # Error feedback: I handle an empty or false analytical response.
                                request,  # Request argument: I attach the message.
                                (
                                    "MarketPulse could not produce "  # String: I begin the explanation.
                                    "a Strategy Robustness result."  # String: I finish the explanation.
                                ),  # Closing parenthesis: I finish the message.
                            )  # Closing parenthesis: I finish error feedback.

                        except Exception as error:  # Exception handling: I catch errors raised by the analytical engine.
                            messages.error(  # Error feedback: I convert the failure into user-visible feedback.
                                request,  # Request argument: I attach the message.
                                (
                                    "Strategy Robustness analysis "  # String: I begin the explanation.
                                    "could not be completed: "  # String continuation: I introduce the exception.
                                    f"{error}"  # Formatted string: I include the exception's text.
                                ),  # Closing parenthesis: I finish the message.
                            )  # Closing parenthesis: I finish error feedback.


        # ----------------------------------------------------
        # 8.12.4 STRESS TESTING — BACKEND RETAINED FOR COMPATIBILITY
        # ----------------------------------------------------

        elif action == "stress_test":  # Equality comparison: I retain support for older stress-test submissions.

            if not selected_validation_strategy:  # Conditional: I require a strategy identifier.
                messages.error(
                    request,
                    "Select a strategy first.",
                )  # Error feedback: I explain the missing strategy.

            elif not selected_validation_symbol:  # Alternative condition: I require a historical symbol.
                messages.error(
                    request,
                    "Select an asset first.",
                )  # Error feedback: I explain the missing historical asset.

            else:  # Else branch: I continue when both selections exist.
                strategy = get_object_or_404(  # Secure retrieval: I retrieve the selected strategy or return HTTP 404.
                    Strategy,  # Model argument: I query Strategy.
                    pk=selected_validation_strategy,  # Primary-key filter: I match the submitted ID.
                    user=request.user,  # Ownership filter: I restrict the strategy to the signed-in user.
                )  # Closing parenthesis: I finish strategy retrieval.

                scenarios = {  # Nested dictionary: I retain the project's configured stress-test parameter presets.

                    "crash": {  # Dictionary key: I define the crash scenario.
                        "crash_start": 0.70,  # Float: I store the configured start position.
                        "crash_magnitude": 0.20,  # Float: I store the configured crash magnitude.
                    },  # Closing brace: I finish the crash parameters.

                    "volatility_spike": {  # Dictionary key: I define the volatility-spike scenario.
                        "spike_start": 0.50,  # Float: I store the configured spike start.
                        "spike_duration": 0.10,  # Float: I store the configured spike duration.
                        "spike_magnitude": 3.0,  # Float: I store the configured volatility multiplier.
                    },  # Closing brace: I finish volatility-spike parameters.

                    "liquidity_crisis": {  # Dictionary key: I define the liquidity-crisis scenario.
                        "crisis_start": 0.60,  # Float: I store the configured crisis start.
                        "crisis_duration": 0.20,  # Float: I store the configured crisis duration.
                        "volume_reduction": 0.70,  # Float: I store the configured reduction in market volume.
                    },  # Closing brace: I finish liquidity-crisis parameters.

                    "regime_change": {  # Dictionary key: I define the market-regime-change scenario.
                        "change_point": 0.50,  # Float: I store the configured change point.
                        "new_trend": -0.01,  # Signed float: I store the configured new negative trend.
                    },  # Closing brace: I finish regime-change parameters.

                }  # Closing brace: I finish the scenario dictionary.

                parameters = scenarios.get(
                    selected_stress_scenario
                )  # Dictionary lookup: I retrieve the chosen preset or None for an unknown scenario.

                if parameters is None:  # Identity condition: I reject scenario names that are not in the preset dictionary.
                    messages.error(
                        request,
                        "Choose a valid stress scenario.",
                    )  # Error feedback: I explain the invalid selection.

                else:  # Else branch: I continue with an allowed scenario.
                    try:  # Exception handling: I protect the page from calculation failures.

                        stress_result = run_stress_test(  # Function call: I delegate the calculation to the existing stress-test engine.
                            strategy,  # Argument: I supply the user's strategy.
                            selected_validation_symbol,  # Argument: I supply the historical market symbol.
                            selected_stress_scenario,  # Argument: I supply the selected scenario code.
                            parameters,  # Argument: I supply the scenario's parameter dictionary.
                        )  # Closing parenthesis: I finish the stress-test call.

                        if stress_result:  # Truthiness condition: I detect successful analytical output.
                            messages.success(  # Success feedback: I tell the user the compatibility calculation completed.
                                request,  # Request argument: I attach the feedback.
                                (
                                    "Stress test completed "  # String: I begin the success message.
                                    f"for {strategy.name} on "  # Formatted string: I include the strategy name.
                                    f"{selected_validation_symbol}."  # Formatted string: I include the historical asset.
                                ),  # Closing parenthesis: I finish the message.
                            )  # Closing parenthesis: I finish success feedback.

                            return redirect(
                                _strategy_workspace_url("myStrategiesSection")
                            )  # Redirect: I return to the remaining My Strategies section because the stress panel is being removed.

                        messages.error(  # Error feedback: I handle a false or empty analytical result.
                            request,  # Request argument: I attach the feedback.
                            (
                                "MarketPulse could not complete "  # String: I begin the explanation.
                                "the stress test. Make sure the "  # String continuation: I suggest a likely requirement.
                                "selected asset has sufficient "  # String continuation: I identify historical data availability.
                                "historical data."  # String: I finish the guidance.
                            ),  # Closing parenthesis: I finish the message.
                        )  # Closing parenthesis: I finish error feedback.

                    except Exception as error:  # Exception handling: I catch calculation failures.
                        messages.error(  # Error feedback: I expose a readable error message.
                            request,  # Request argument: I attach the feedback.
                            (
                                "Stress testing could not be "  # String: I begin the explanation.
                                f"completed: {error}"  # Formatted string: I append the exception text.
                            ),  # Closing parenthesis: I finish the message.
                        )  # Closing parenthesis: I finish error feedback.


    # ========================================================
    # 8.13 PREPARE EACH STRATEGY'S SUMMARY
    # ========================================================

    my_strategy_rows = []  # List creation: I prepare presentation data for the My Strategies section.

    for strategy in my_strategies:  # Loop: I process every strategy belonging to the current user.

        latest_backtest = (
            strategy.backtests
            .order_by("-created_at")
            .first()
        )  # Related query: I retrieve the most recent backtest for this strategy or None.

        backtest_count = (
            strategy.backtests.count()
        )  # Related-manager count: I calculate the number of saved backtests for this strategy.

        latest_robustness_test = (  # Variable assignment: I retain compatibility with stored robustness results.
            OverfittingTest.objects  # ORM manager: I access stored overfitting tests.
            .filter(
                user=request.user,
                strategy_name=strategy.name,
            )  # Query filter: I match the current user and the existing strategy-name field.
            .order_by("-created_at")  # Ordering: I place the newest result first.
            .first()  # Query evaluation: I retrieve one result or None.
        )  # Closing parenthesis: I finish the query.

        robustness_label, robustness_explanation = _robustness_interpretation(
            latest_robustness_test
        )  # Tuple unpacking: I convert the stored test into readable interpretation values.

        my_strategy_rows.append({  # List method: I add one display dictionary for this strategy.
            "strategy": strategy,  # Dictionary entry: I provide the Strategy model object.
            "latest_backtest": latest_backtest,  # Dictionary entry: I provide its newest saved backtest.
            "backtest_count": backtest_count,  # Dictionary entry: I provide the number of backtests.
            "latest_robustness_test": latest_robustness_test,  # Dictionary entry: I retain stored robustness information for compatibility.
            "robustness_label": robustness_label,  # Dictionary entry: I provide the readable robustness label.
            "robustness_explanation": robustness_explanation,  # Dictionary entry: I provide the readable explanation.
        })  # Closing parenthesis: I finish appending this strategy summary.


    # ========================================================
    # 8.14 USER-LEVEL ROBUSTNESS SUMMARY — COMPATIBILITY DATA
    # ========================================================

    robustness_test_count = OverfittingTest.objects.filter(
        user=request.user
    ).count()  # ORM query: I count stored robustness tests belonging to this user.

    latest_user_robustness_test = (  # Variable assignment: I retrieve the user's newest stored robustness test.
        OverfittingTest.objects  # ORM manager: I access OverfittingTest records.
        .filter(user=request.user)  # Ownership filter: I restrict results to the current user.
        .order_by("-created_at")  # Ordering: I place newest results first.
        .first()  # Query evaluation: I retrieve one object or None.
    )  # Closing parenthesis: I finish the query.

    (
        latest_user_robustness_label,
        latest_user_robustness_explanation,
    ) = _robustness_interpretation(
        latest_user_robustness_test
    )  # Tuple unpacking: I create readable compatibility values for the newest robustness result.


    # ========================================================
    # 8.15 USER-LEVEL STRESS SUMMARY — COMPATIBILITY DATA
    # ========================================================

    stress_test_count = StressTest.objects.filter(
        user=request.user
    ).count()  # ORM query: I count stored stress tests belonging to this user.

    latest_strategy_stress_test = (  # Variable assignment: I retrieve the user's newest stored stress-test result.
        StressTest.objects  # ORM manager: I access StressTest records.
        .filter(user=request.user)  # Ownership filter: I restrict results to this user.
        .order_by("-created_at")  # Ordering: I put newest results first.
        .first()  # Query evaluation: I retrieve one object or None.
    )  # Closing parenthesis: I finish the query.


    # ========================================================
    # 8.16 TEMPLATE CONTEXT — DICTIONARY OF DISPLAY DATA
    # ========================================================

    context = {  # Dictionary creation: I map template variable names to Python values.

        "library_items": library_items,  # Context value: I supply the active model catalogue.

        "category_cards": category_cards,  # Context value: I supply model-category summary information.

        "total_library_models": total_library_models,  # Context value: I supply the total active model count.

        "ready_models": ready_models,  # Context value: I supply the ready-to-run count.

        "experimental_models": experimental_models,  # Context value: I supply the experimental-model count.

        "catalogued_models": catalogued_models,  # Context value: I supply the catalogue-only count.

        "compare_items": compare_items,  # Context value: I supply valid models selected for comparison.

        "compare_codes": requested_compare_codes,  # Context value: I preserve comparison checkbox selections.

        "comparison_message": comparison_message,  # Context value: I supply server-side comparison feedback.

        "my_strategy_rows": my_strategy_rows,  # Context value: I supply enriched user-strategy summaries.

        "my_strategy_count": my_strategies.count(),  # Context value: I supply the user's total saved-strategy count.

        "strategy_form": strategy_form,  # Context value: I send the inline StrategyCreateForm to list.html.

        "show_strategy_form": (
            action == "create_strategy"
        ),  # Boolean context value: I keep the inline form open after a submitted creation request, especially when validation fails.

        "risk_form": risk_form,  # Context value: I supply the reused RiskPlannerForm for the inline Portfolio Risk Calculator.

        "risk_result": risk_result,  # Context value: I supply the calculated portfolio-risk result or None before calculation.

        "selected_risk_strategy": selected_risk_strategy,  # Context value: I supply the owned strategy chosen for this Risk calculation.

        "selected_risk_strategy_id": selected_risk_strategy_id,  # Context value: I preserve the Risk strategy dropdown selection.

        "risk_market_context": risk_market_context,  # Context value: I supply stored ATR/volatility/drawdown context for the Risk result.

        "show_risk_calculator": (
            action == "calculate_risk"
        ),  # Boolean context value: I keep the same-page Risk disclosure open after a calculation submission or validation failure.

        "available_symbols": available_symbols,  # Context value: I supply distinct historical symbols.

        "symbols": available_symbols,  # Compatibility value: I retain the older template variable name.

        "selected_validation_strategy": selected_validation_strategy,  # Compatibility value: I retain the selected strategy identifier.

        "selected_validation_symbol": selected_validation_symbol,  # Compatibility value: I retain the selected historical ticker.

        "selected_stress_scenario": selected_stress_scenario,  # Compatibility value: I retain the chosen stress scenario.

        "robustness_test_count": robustness_test_count,  # Compatibility value: I supply the user's stored robustness-test count.

        "latest_user_robustness_test": latest_user_robustness_test,  # Compatibility value: I supply the newest user-level robustness result.

        "latest_user_robustness_label": latest_user_robustness_label,  # Compatibility value: I supply its readable interpretation label.

        "latest_user_robustness_explanation": latest_user_robustness_explanation,  # Compatibility value: I supply its readable explanation.

        "stress_test_count": stress_test_count,  # Compatibility value: I supply the user's stored stress-test count.

        "latest_strategy_stress_test": latest_strategy_stress_test,  # Compatibility value: I supply the newest user-level stress result.

        "strategies": my_strategies,  # Context value: I retain the plain strategy collection for template compatibility.

        "page_title": "Strategy & Model Research",  # Context value: I supply the readable page title.

    }  # Closing brace: I finish the context dictionary.


    # ========================================================
    # 8.17 HTML RESPONSE
    # ========================================================

    return render(
        request,
        "strategy_builder/list.html",
        context,
    )  # Template response: Django renders the combined Strategies workspace using the prepared context.


# ============================================================
# 9. LEGACY ROBUSTNESS ROUTE — REDIRECT COMPATIBILITY
# ============================================================

@login_required  # Decorator: I require authentication before handling this older route.
def strategy_robustness(request):  # Function definition: I retain the route so existing links do not fail.
    """
    Redirect old robustness URLs to My Strategies.

    The separate visible Strategy Robustness section is being
    removed from the Strategies workspace.
    """

    return redirect(
        _strategy_workspace_url("myStrategiesSection")
    )  # Redirect: I send old robustness links to the remaining My Strategies section.


# ============================================================
# 10. LEGACY ROBUSTNESS RESULTS ROUTE
# ============================================================

@login_required  # Decorator: I require authentication before handling the older results route.
def strategy_robustness_results(request):  # Function definition: I keep the previous named route available.
    """
    Redirect old robustness-result links to My Strategies.

    This prevents existing URLs from pointing to a section that
    has now been removed from list.html.
    """

    return redirect(
        _strategy_workspace_url("myStrategiesSection")
    )  # Redirect: I return to the active My Strategies area.


# ============================================================
# 11. LEGACY CREATE-STRATEGY ROUTE
# ============================================================

@login_required  # Decorator: I require a signed-in user.
def strategy_create(request):  # Function definition: I retain /strategy/create/ for backwards compatibility.
    """
    Redirect old strategy-creation links to My Strategies.

    Strategy creation is now performed by StrategyCreateForm
    inside strategy_list(), so this view no longer renders
    strategy_builder/create.html.
    """

    return redirect(
        _strategy_workspace_url("myStrategiesSection")
    )  # Redirect: I return to the inline strategy-creation area on the main Strategies page.


# ============================================================
# 12. ADD LIBRARY METADATA — DEFERRED MODEL SAVE
# ============================================================

@login_required  # Decorator: I require authentication; this view itself does not add an is_staff permission check.
def library_item_create(request):  # Function definition: I process creation of strategy-library metadata.
    """Create an active library item whose initial implementation status is catalogued."""

    if request.method == "POST":  # Conditional: I distinguish a submitted form from an initial page request.

        form = StrategyLibraryItemForm(
            request.POST
        )  # Form binding: I populate the library form with submitted POST data.

        if form.is_valid():  # Form validation: I continue only after Django accepts the submitted values.

            library_item = form.save(
                commit=False
            )  # ModelForm save: I create the model object in memory without writing it to the database yet.

            library_item.implementation_status = (
                "catalogued"
            )  # Attribute assignment: I mark the new library entry as metadata-only initially.

            library_item.is_active = True  # Boolean assignment: I make the entry visible in the active library.

            library_item.display_order = 999  # Integer assignment: I place manually added entries later in their category.

            library_item.save()  # Model method: I persist the prepared library record to the configured database.

            messages.success(  # Django messages: I prepare confirmation feedback.
                request,  # Request argument: I attach the notification to this request.
                (
                    f"{library_item.name} was added "  # Formatted string: I include the library item's name.
                    f"to the MarketPulse Strategy & "  # Formatted string continuation: I identify the library.
                    f"Model Library."  # String: I finish the confirmation message.
                ),  # Closing parenthesis: I finish the message expression.
            )  # Closing parenthesis: I finish creating the success message.

            return redirect(
                "strategy_builder:list"
            )  # Redirect: I return to the main Strategies workspace after successful library creation.

    else:  # Else branch: I handle an initial GET request.
        form = StrategyLibraryItemForm()  # Form creation: I prepare an empty library-entry form.

    context = {  # Dictionary creation: I prepare values required by the library-add template.
        "form": form,  # Context value: I supply the form and any validation errors.
        "page_title": "Add Strategy or Model",  # Context value: I supply the readable page title.
    }  # Closing brace: I finish the context dictionary.

    return render(
        request,
        "strategy_builder/library_add.html",
        context,
    )  # Template response: I display the library-entry page.


# ============================================================
# 13. BACKTEST A STRATEGY — VALIDATED KEYWORD UNPACKING
# ============================================================

@login_required  # Decorator: I require the user to be authenticated.
def backtest_strategy(request, strategy_id):  # Function definition: Django supplies the request and integer URL parameter.
    """Run a historical backtest for a strategy owned by the current user."""

    strategy = get_object_or_404(  # Secure retrieval: I load the strategy or return HTTP 404.
        Strategy,  # Model argument: I query Strategy.
        pk=strategy_id,  # Primary-key filter: I match the ID captured from the URL.
        user=request.user,  # Ownership filter: I prevent users from backtesting another user's strategy.
    )  # Closing parenthesis: I finish retrieval.

    form = BacktestForm(
        request.POST or None
    )  # Form creation: I bind submitted data for POST or create an unbound form for GET.

    if request.method == "POST" and form.is_valid():  # Boolean AND: I require both a POST request and valid form values.

        try:  # Exception handling: I protect the page from calculation failures.

            backtest = run_backtest(  # Function call: I invoke the historical simulation engine.
                strategy,  # Positional argument: I supply the selected owned strategy.
                **form.cleaned_data,  # Dictionary unpacking: I pass validated form fields as named keyword arguments.
            )  # Closing parenthesis: I finish the backtesting call.

            messages.success(  # Django messages: I prepare completion feedback.
                request,  # Request argument: I attach the feedback to this request.
                (
                    f"Backtest completed for "  # Formatted string: I begin the confirmation.
                    f"{strategy.name}."  # Formatted string: I insert the strategy name.
                ),  # Closing parenthesis: I finish the message expression.
            )  # Closing parenthesis: I finish success feedback.

            return redirect(  # Redirect: I navigate to the persisted backtest result.
                "strategy_builder:results",  # Named URL: I identify the results route.
                backtest_id=backtest.pk,  # Keyword argument: I supply the new Backtest primary key required by that route.
            )  # Closing parenthesis: I finish the redirect.

        except Exception as error:  # Exception handling: I catch errors produced during historical simulation.
            messages.error(
                request,
                str(error),
            )  # Type conversion and feedback: I convert the exception to readable text and display it.

    context = {  # Dictionary creation: I prepare values needed by the backtest template.
        "strategy": strategy,  # Context value: I supply the selected Strategy object.
        "form": form,  # Context value: I supply the form and any validation errors.
        "page_title": f"Backtest {strategy.name}",  # Formatted string: I build a strategy-specific page title.
    }  # Closing brace: I finish the context dictionary.

    return render(
        request,
        "strategy_builder/backtest_form.html",
        context,
    )  # Template response: I display the backtest form.


# ============================================================
# 14. BACKTEST RESULTS — RELATED RECORDS AND OWNERSHIP
# ============================================================

@login_required  # Decorator: I require authentication before exposing a saved backtest.
def backtest_results(request, backtest_id):  # Function definition: Django supplies the requested backtest's integer ID.
    """Display an owned backtest and its related simulated trades."""

    backtest = get_object_or_404(  # Secure retrieval: I load the requested result or return HTTP 404.
        Backtest,  # Model argument: I query Backtest.
        pk=backtest_id,  # Primary-key filter: I match the ID captured by the URL.
        strategy__user=request.user,  # Related-field lookup: I ensure the associated strategy belongs to the signed-in user.
    )  # Closing parenthesis: I finish retrieval.

    trades = (
        backtest.trades
        .all()
        .order_by("entry_date")
    )  # Related-manager query: I retrieve simulated trades in chronological entry order.

    context = {  # Dictionary creation: I prepare data required by the results template.
        "backtest": backtest,  # Context value: I supply the stored backtest and its performance metrics.
        "trades": trades,  # Context value: I supply the associated simulated trades.
        "page_title": "Backtest Results",  # Context value: I supply the readable page title.
    }  # Closing brace: I finish the context dictionary.

    return render(  # Return statement: I ask Django to build the final HTML response.
        request,  # Argument: I provide the current HTTP request.
        "strategy_builder/backtest_results.html",  # Template path: I select the backtest-results template.
        context,  # Dictionary argument: I supply all values the template can display.
    )  # Closing parenthesis: I finish the rendered response.


# ============================================================
# LECTURER EXPLANATION
# ============================================================

# I use Django views to coordinate browser requests,
# validated forms, owned database records and calculation engines.
#
# The main Strategies page now handles strategy creation itself:
#
# Browser
#     ↓
# /strategy/
#     ↓
# strategy_list()
#     ↓
# StrategyCreateForm
#     ↓
# form.is_valid()
#     ↓
# form.save(request.user)
#     ↓
# core.Strategy + related StrategyRule records
#     ↓
# PostgreSQL
#     ↓
# redirect to /strategy/#myStrategiesSection
#     ↓
# newly created strategy appears under My Strategies
#
# The old /strategy/create/ route remains available so existing
# URLs do not break, but it now redirects back to My Strategies
# rather than rendering a second strategy-creation page.
#
# The same Strategies request handler now also coordinates Risk:
#
# My Strategies
#     ↓
# Portfolio Risk Calculator
#     ↓
# RiskPlannerForm
#     ↓
# selected owned Strategy
#     +
# manual price / Alpaca price / stored historical close
#     ↓
# calculate_trade_risk_plan()
#     ↓
# position size + planned loss + potential reward
#     +
# latest matching strategy backtest
#     ↓
# historical win/loss rate + historical expectancy
#     ↓
# result displayed back inside /strategy/
#
# The numerical Risk formulas remain in risk_management/calculators.py.
# This view only coordinates the inputs, existing services and output.
#
# Backtesting remains a separate workflow because a saved strategy
# must already exist before the backtesting engine can execute.
#
# Robustness and stress-test backend functionality is retained
# for compatibility even though their separate visible sections
# are being removed from the Strategies template.
#
# Programming-language concepts demonstrated in this file include:
#
# - imports;
# - functions;
# - decorators;
# - parameters;
# - return values;
# - variables;
# - strings;
# - integers and floating-point numbers;
# - Booleans;
# - lists;
# - tuples;
# - dictionaries;
# - loops;
# - conditions;
# - comprehensions;
# - slicing;
# - method chaining;
# - keyword arguments;
# - dictionary unpacking;
# - exception handling;
# - object attributes;
# - Django ORM queries;
# - HTTP GET and POST processing;
# - server-side form validation;
# - redirects;
# - template context dictionaries.