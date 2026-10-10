"""
============================================================
MARKETPULSE - STRATEGY BUILDER VIEWS
============================================================

Framework mapping:
Django URLs → these views → forms / models / analytics
→ template context → HTML response.

Strategy & Model Library:
StrategyLibraryItem → strategy_list()
→ strategy_builder/list.html → Browse / Filter / Compare.

Custom Strategy:
StrategyCreateForm → core.Strategy → strategy_create()
→ Backtesting.

Historical Backtesting:
BacktestForm → run_backtest() → core.Backtest
→ BacktestTrade → backtest_results().

Strategy Robustness:
Strategies page → User Strategy → Historical MarketData
→ detect_overfitting() → OverfittingTest
→ Result displayed inside /strategy/.

Stress Testing:
Strategies page → User Strategy → Historical MarketData
→ run_stress_test() → StressTest
→ Result displayed inside /strategy/.

Library Creation:
StrategyLibraryItemForm → StrategyLibraryItem
→ Strategy & Model Library.

Student understanding:
Views coordinate requests and return responses.
Forms validate submitted data.
Models provide database access through Django's ORM.
Imported analytics functions perform the calculations.
Templates display the supplied context.

Programming concepts:
Imports, functions, decorators, parameters, return values,
variables, strings, numbers, Booleans, lists, tuples,
dictionaries, loops, conditions, comprehensions, slicing,
unpacking, method chaining and exception handling.

analysis_tools remains an internal analytics layer.
Robustness and stress forms are handled on the Strategies page.
Market Condition remains part of the Data workflow.

These notes describe this view's calls. Details inside imported
forms and calculation engines belong to their own source files.
============================================================
"""

# ============================================================
# 1. DJANGO IMPORTS — REUSING FRAMEWORK FUNCTIONS
# ============================================================
from django.contrib import messages  # I import user-notification helpers.
from django.contrib.auth.decorators import login_required  # I import the decorator that requires authentication.
from django.db.models import Max, Min  # I import database aggregation functions for date ranges.
from django.shortcuts import get_object_or_404, redirect, render  # I import retrieval and response helpers.
from django.urls import reverse  # I import named-route URL resolution.

# ============================================================
# 2. CORE MODELS — DATABASE ACCESS
# ============================================================
from core.models import Backtest, MarketData, Strategy  # I import model classes used by these views.

# ============================================================
# 3. INTERNAL ANALYTICS — CALCULATIONS AND STORED RESULTS
# ============================================================
from analysis_tools.analyzers import detect_overfitting, run_stress_test  # I delegate analysis to the internal engine.
from analysis_tools.models import OverfittingTest, StressTest  # I import models used to retrieve analysis results.

# ============================================================
# 4. LOCAL FORMS — SUBMITTED DATA
# ============================================================
from .forms import BacktestForm, StrategyCreateForm, StrategyLibraryItemForm  # The leading dot imports from this package.

# ============================================================
# 5. LOCAL LIBRARY MODEL
# ============================================================
from .models import StrategyLibraryItem  # I import the strategy-library metadata model.

# ============================================================
# 6. BACKTESTING ENGINE
# ============================================================
from .backtesting import run_backtest  # I import the function that performs historical simulation.

# ============================================================
# 7. HELPERS — SMALL REUSABLE FUNCTIONS
# ============================================================
def _strategy_workspace_url(anchor=None):  # I define a helper with an optional parameter defaulting to None.
    """Return the Strategies URL, optionally followed by a section anchor."""
    url = reverse("strategy_builder:list")  # I resolve the named route instead of hard-coding its path.
    if anchor:  # I check whether a truthy anchor was supplied.
        return f"{url}#{anchor}"  # An f-string inserts values; the fragment identifies a browser section.
    return url  # I return the plain URL when there is no anchor.


def _get_available_historical_symbols():  # I define a helper with no explicit parameters.
    """Return distinct symbols stored in core.MarketData."""
    return list(  # I evaluate the query and convert its results into a Python list.
        MarketData.objects  # I access the model's query manager.
        .order_by("symbol")  # I order the records by symbol.
        .values_list("symbol", flat=True)  # I request symbol values rather than complete model objects.
        .distinct()  # I remove duplicate symbol values.
    )  # I finish the returned list conversion.


def _robustness_interpretation(test):  # I receive an analysis result as a parameter.
    """Return a user-facing label and explanation as a two-item tuple."""
    if not test:  # I handle an absent or false result.
        return (None, None)  # I return a tuple containing two empty values.
    score = float(test.overfitting_score)  # I convert the stored score into a floating-point number.
    if test.is_overfitted and score >= 0.50:  # Boolean AND requires the flag and score threshold to match.
        return (  # I return the high-risk label and explanation.
            "High Overfitting Risk",  # I supply the label string.
            (
                "Performance weakened substantially when "  # Adjacent string literals join automatically.
                "MarketPulse moved from the in-sample period "  # I continue the explanation.
                "to the out-of-sample period. The historical "  # I describe the comparison.
                "result may depend too heavily on the data "  # I explain the possible limitation.
                "used during strategy development."  # I complete the explanation.
            ),  # I close the explanation string.
        )  # I close the returned tuple.
    if test.is_overfitted:  # I handle flagged results below the previous threshold.
        return (  # I return the moderate-risk interpretation.
            "Moderate Overfitting Risk",  # I supply its label.
            (
                "The strategy showed a meaningful reduction "  # I begin the explanation.
                "in performance on the out-of-sample period. "  # I describe the observed reduction.
                "Additional testing across other data periods "  # I suggest broader evaluation.
                "and market conditions would be useful."  # I complete the explanation.
            ),  # I close the explanation string.
        )  # I close the tuple.
    return (  # I return the remaining interpretation.
        "Low Overfitting Risk",  # I supply the unflagged-result label.
        (
            "The simplified robustness check did not identify "  # I describe this check's finding.
            "a large deterioration between the in-sample and "  # I identify the comparison.
            "out-of-sample periods. This does not guarantee "  # I state the interpretation's limit.
            "future performance."  # I complete the explanation.
        ),  # I close the explanation string.
    )  # I close the tuple.

# ============================================================
# 8. STRATEGIES WORKSPACE — MAIN REQUEST HANDLER
# ============================================================
@login_required  # A decorator checks authentication before this view executes.
def strategy_list(request):  # Django supplies the HTTP request object.
    """
    Render the combined Strategies workspace.
    GET prepares library, comparison and saved-strategy data.
    POST also processes robustness or stress-test submissions.
    """

    # 8.1 ACTIVE MODEL LIBRARY
    library_items = (  # I store a QuerySet representing matching library records.
        StrategyLibraryItem.objects  # I access the library model manager.
        .filter(is_active=True)  # I include only active items.
        .order_by("category", "display_order", "name")  # I define the display ordering.
    )  # I close the chained query.

    # 8.2 CATEGORY SUMMARY CARDS
    category_cards = []  # I initialise an empty list of category dictionaries.
    for category_code, category_label in StrategyLibraryItem.CATEGORY_CHOICES:  # Tuple unpacking gives each choice a code and label.
        category_count = library_items.filter(category=category_code).count()  # I count active items in this category.
        category_cards.append({  # I append a dictionary representing one category.
            "code": category_code,  # I store its machine-readable code.
            "label": category_label,  # I store its readable label.
            "count": category_count,  # I store its model count.
        })  # I finish appending the category.

    # 8.3 LIBRARY COUNTS
    total_library_models = library_items.count()  # I count all active library records.
    ready_models = library_items.filter(implementation_status="ready").count()  # I count ready records.
    experimental_models = library_items.filter(implementation_status="experimental").count()  # I count experimental records.
    catalogued_models = library_items.filter(implementation_status="catalogued").count()  # I count catalogued records.

    # 8.4 COMPARISON INPUT
    requested_compare_codes = request.GET.getlist("compare")  # I retrieve repeated compare query parameters as a list.
    requested_compare_codes = list(dict.fromkeys(requested_compare_codes))  # Dictionary keys remove duplicates while retaining insertion order.
    comparison_message = ""  # I initialise an empty feedback string.

    # 8.5 SERVER-SIDE COMPARISON LIMIT
    if len(requested_compare_codes) > 4:  # I check the list length independently of browser controls.
        requested_compare_codes = requested_compare_codes[:4]  # Slicing retains only the first four codes.
        comparison_message = (  # I prepare feedback about the limit.
            "MarketPulse compares a maximum of four "  # I begin the message.
            "models at the same time."  # I complete the message.
        )  # I close the string expression.

    # 8.6 RETRIEVE VALID COMPARISON ITEMS
    compare_queryset = StrategyLibraryItem.objects.filter(  # I query active records matching submitted codes.
        code__in=requested_compare_codes,  # The __in lookup matches any code in the list.
        is_active=True,  # I exclude inactive records.
    )  # I close the query.
    compare_lookup = {item.code: item for item in compare_queryset}  # A dictionary comprehension indexes objects by code.
    compare_items = [compare_lookup[code] for code in requested_compare_codes if code in compare_lookup]  # A list comprehension preserves requested order and skips unknown codes.
    if requested_compare_codes and len(compare_items) < 2:  # I require at least two valid items when comparison was requested.
        comparison_message = "Select at least two models to compare."  # I replace feedback with the minimum-selection message.

    # 8.7 USER-OWNED STRATEGIES
    my_strategies = (  # I prepare the user's strategy QuerySet.
        Strategy.objects  # I access the Strategy manager.
        .filter(user=request.user)  # I restrict this list to the current user.
        .prefetch_related("rules")  # I preload related rules to reduce later repeated queries.
        .order_by("-created_at")  # The minus sign requests newest-first ordering.
    )  # I close the query.

    # 8.8 STORED HISTORICAL SYMBOLS
    available_symbols = _get_available_historical_symbols()  # I call the reusable helper for stored-data choices.

    # 8.9 PRESERVE FORM SELECTIONS
    selected_validation_strategy = (  # I choose the submitted or query-string strategy value.
        request.POST.get("strategy")  # I first check form data.
        or request.GET.get("strategy")  # Logical OR falls back to query-string data.
        or ""  # I use an empty string when neither supplies a truthy value.
    )  # I close the selection expression.
    selected_validation_symbol = (  # I choose and normalise the asset symbol.
        request.POST.get("symbol")  # I first check submitted form data.
        or request.GET.get("symbol")  # I then check the query string.
        or ""  # I provide an empty fallback.
    ).strip().upper()  # Method chaining removes outer whitespace and uppercases the symbol.
    selected_stress_scenario = request.POST.get("scenario") or "crash"  # I use the posted scenario or default to crash.

    # 8.10 DISPATCH POST ACTIONS
    if request.method == "POST":  # I process calculation actions only for a POST request.
        action = request.POST.get("action", "")  # I read the hidden action field with an empty default.

        # 8.10.1 ROBUSTNESS
        if action == "robustness":  # Equality selects the robustness branch.
            if not selected_validation_strategy:  # I require a strategy selection.
                messages.error(request, "Select a strategy to test.")  # I queue user-facing error feedback.
            elif not selected_validation_symbol:  # I next require a historical symbol.
                messages.error(request, "Select a historical asset to test.")  # I queue missing-symbol feedback.
            else:  # I continue when both selections are present.
                strategy = get_object_or_404(  # I retrieve a matching strategy or raise Http404.
                    Strategy,  # I identify the model.
                    pk=selected_validation_strategy,  # I match the requested primary key.
                    user=request.user,  # I also enforce ownership in this lookup.
                )  # I close retrieval.
                market_queryset = (  # I prepare the selected asset's historical data.
                    MarketData.objects  # I access the market-data manager.
                    .filter(symbol=selected_validation_symbol)  # I match the normalised symbol.
                    .order_by("date")  # I order observations chronologically.
                )  # I close the query.
                observation_count = market_queryset.count()  # I count stored observations.
                if observation_count < 60:  # I enforce this view's minimum robustness-data requirement.
                    messages.error(  # I queue a detailed data-shortage message.
                        request,  # I attach feedback to this request.
                        (
                            f"{selected_validation_symbol} currently "  # An f-string inserts the selected symbol.
                            f"has {observation_count} historical "  # I insert the observed count.
                            f"observations. MarketPulse requires at "  # I continue the explanation.
                            f"least 60 observations for this "  # I state the minimum.
                            f"Strategy Robustness check."  # I complete the message.
                        ),  # I close the combined string.
                    )  # I finish queuing feedback.
                else:  # I continue with sufficient observations.
                    date_range = market_queryset.aggregate(  # Aggregation returns one dictionary of summary values.
                        first_date=Min("date"),  # I calculate the earliest stored date.
                        last_date=Max("date"),  # I calculate the latest stored date.
                    )  # I close aggregation.
                    first_date = date_range["first_date"]  # Dictionary indexing extracts the first date.
                    last_date = date_range["last_date"]  # I extract the last date.
                    if first_date is None or last_date is None or first_date >= last_date:  # Identity checks and OR detect an absent or invalid range.
                        messages.error(  # I queue invalid-period feedback.
                            request,  # I attach it to this request.
                            (
                                "MarketPulse could not determine "  # I explain the problem.
                                "a valid historical period for "  # I continue the message.
                                f"{selected_validation_symbol}."  # I identify the selected symbol.
                            ),  # I close the combined string.
                        )  # I finish feedback.
                    else:  # I continue with a valid historical range.
                        test_periods = [(first_date, last_date)]  # I build a list containing a start/end tuple for the engine.
                        try:  # I begin calculation operations that may raise exceptions.
                            tests = detect_overfitting(  # I delegate robustness calculation to the imported function.
                                strategy,  # I pass the owned strategy object.
                                selected_validation_symbol,  # I pass the selected symbol.
                                test_periods,  # I pass the available test period.
                            )  # I store the returned results.
                            if tests:  # I treat a truthy result as successful.
                                messages.success(  # I queue success feedback.
                                    request,  # I attach it to the request.
                                    (
                                        "Strategy Robustness check "  # I begin the success message.
                                        f"completed for "  # I continue it.
                                        f"{strategy.name} on "  # I insert the strategy name.
                                        f"{selected_validation_symbol}."  # I insert the asset symbol.
                                    ),  # I close the combined string.
                                )  # I finish success feedback.
                                return redirect(_strategy_workspace_url("strategyRobustnessSection"))  # I return a redirect to the workspace section after POST.
                            messages.error(  # I handle a false or empty calculation result.
                                request,  # I attach feedback to this request.
                                (
                                    "MarketPulse could not produce "  # I explain the missing result.
                                    "a Strategy Robustness result."  # I complete the message.
                                ),  # I close the string.
                            )  # I finish feedback.
                        except Exception as error:  # I catch exceptions raised within this try block.
                            messages.error(  # I queue calculation-failure feedback.
                                request,  # I attach it to this request.
                                (
                                    "Strategy Robustness analysis "  # I begin the explanation.
                                    "could not be completed: "  # I introduce the error detail.
                                    f"{error}"  # I insert the exception's string representation.
                                ),  # I close the combined string.
                            )  # I finish feedback.

        # 8.10.2 STRESS TESTING
        elif action == "stress_test":  # I dispatch the alternative supported action.
            if not selected_validation_strategy:  # I require a strategy.
                messages.error(request, "Select a strategy first.")  # I queue missing-strategy feedback.
            elif not selected_validation_symbol:  # I require an asset symbol.
                messages.error(request, "Select an asset first.")  # I queue missing-asset feedback.
            else:  # I continue when both selections exist.
                strategy = get_object_or_404(  # I retrieve the selected strategy.
                    Strategy,  # I identify its model.
                    pk=selected_validation_strategy,  # I match its primary key.
                    user=request.user,  # I restrict the lookup to the current owner.
                )  # I close retrieval.
                scenarios = {  # I define a nested dictionary of engine parameter presets.
                    "crash": {  # I define the severe-decline preset.
                        "crash_start": 0.70,  # I pass the engine's configured start parameter.
                        "crash_magnitude": 0.20,  # I pass the configured shock magnitude.
                    },  # I close the crash parameters.
                    "volatility_spike": {  # I define the volatility preset.
                        "spike_start": 0.50,  # I pass its start parameter.
                        "spike_duration": 0.10,  # I pass its duration parameter.
                        "spike_magnitude": 3.0,  # I pass its magnitude parameter.
                    },  # I close the spike parameters.
                    "liquidity_crisis": {  # I define the liquidity preset.
                        "crisis_start": 0.60,  # I pass its start parameter.
                        "crisis_duration": 0.20,  # I pass its duration parameter.
                        "volume_reduction": 0.70,  # I pass its volume-reduction parameter.
                    },  # I close the liquidity parameters.
                    "regime_change": {  # I define the market-condition-change preset.
                        "change_point": 0.50,  # I pass its change-point parameter.
                        "new_trend": -0.01,  # I pass a negative floating-point trend parameter.
                    },  # I close the regime-change parameters.
                }  # I close the scenario dictionary; the engine defines the precise parameter semantics.
                parameters = scenarios.get(selected_stress_scenario)  # Dictionary get returns the preset or None for an unknown key.
                if parameters is None:  # I validate the requested scenario against these presets.
                    messages.error(request, "Choose a valid stress scenario.")  # I queue invalid-scenario feedback.
                else:  # I continue with an allowed preset.
                    try:  # I begin calculation error handling.
                        stress_result = run_stress_test(  # I delegate the numerical test to the engine.
                            strategy,  # I pass the owned strategy.
                            selected_validation_symbol,  # I pass the historical asset.
                            selected_stress_scenario,  # I pass the scenario code.
                            parameters,  # I pass the preset dictionary.
                        )  # I store the returned result.
                        if stress_result:  # I check for a truthy result.
                            messages.success(  # I queue completion feedback.
                                request,  # I attach it to the request.
                                (
                                    "Stress test completed "  # I begin the message.
                                    f"for {strategy.name} on "  # I insert the strategy name.
                                    f"{selected_validation_symbol}."  # I insert the asset symbol.
                                ),  # I close the string.
                            )  # I finish feedback.
                            return redirect(_strategy_workspace_url("stressTestingSection"))  # I redirect to the same workspace's stress section.
                        messages.error(  # I handle a false calculation result.
                            request,  # I attach feedback to the request.
                            (
                                "MarketPulse could not complete "  # I begin the explanation.
                                "the stress test. Make sure the "  # I continue it.
                                "selected asset has sufficient "  # I identify a data requirement.
                                "historical data."  # I complete the guidance.
                            ),  # I close the string.
                        )  # I finish feedback.
                    except Exception as error:  # I catch calculation exceptions.
                        messages.error(  # I queue failure feedback.
                            request,  # I attach it to the request.
                            (
                                "Stress testing could not be "  # I begin the explanation.
                                f"completed: {error}"  # I insert the exception detail.
                            ),  # I close the combined string.
                        )  # I finish feedback.

    # 8.11 PREPARE EACH STRATEGY'S SUMMARY
    my_strategy_rows = []  # I initialise the list used by the template.
    for strategy in my_strategies:  # I iterate over the current user's strategies.
        latest_backtest = strategy.backtests.order_by("-created_at").first()  # I retrieve the newest related backtest or None.
        backtest_count = strategy.backtests.count()  # I count related backtests.
        latest_robustness_test = (  # I prepare the latest name-matched robustness result.
            OverfittingTest.objects  # I access the result manager.
            .filter(user=request.user, strategy_name=strategy.name)  # I match by user and strategy name, not a Strategy foreign key.
            .order_by("-created_at")  # I sort newest first.
            .first()  # I retrieve one result or None.
        )  # I close the query.
        robustness_label, robustness_explanation = _robustness_interpretation(latest_robustness_test)  # Tuple unpacking separates the two returned values.
        my_strategy_rows.append({  # I append a presentation dictionary.
            "strategy": strategy,  # I include the strategy object.
            "latest_backtest": latest_backtest,  # I include the latest backtest.
            "backtest_count": backtest_count,  # I include its count.
            "latest_robustness_test": latest_robustness_test,  # I include the matched robustness result.
            "robustness_label": robustness_label,  # I include the readable label.
            "robustness_explanation": robustness_explanation,  # I include its explanation.
        })  # I finish appending the row.

    # 8.12 USER-LEVEL ROBUSTNESS SUMMARY
    robustness_test_count = OverfittingTest.objects.filter(user=request.user).count()  # I count the user's robustness results.
    latest_user_robustness_test = (  # I retrieve the user's newest robustness result across strategies.
        OverfittingTest.objects  # I access the manager.
        .filter(user=request.user)  # I restrict results to this user.
        .order_by("-created_at")  # I sort newest first.
        .first()  # I retrieve one object or None.
    )  # I close the query.
    latest_user_robustness_label, latest_user_robustness_explanation = _robustness_interpretation(latest_user_robustness_test)  # I unpack its readable interpretation.

    # 8.13 USER-LEVEL STRESS SUMMARY
    stress_test_count = StressTest.objects.filter(user=request.user).count()  # I count the user's stress results.
    latest_strategy_stress_test = (  # Despite its name, this query retrieves the latest result for the user across strategies.
        StressTest.objects  # I access the stress-result manager.
        .filter(user=request.user)  # I restrict results to this user.
        .order_by("-created_at")  # I sort newest first.
        .first()  # I retrieve one object or None.
    )  # I close the query.

    # 8.14 TEMPLATE CONTEXT — DICTIONARY OF DISPLAY DATA
    context = {  # I map template variable names to Python values.
        "library_items": library_items,  # I supply the active model library.
        "category_cards": category_cards,  # I supply category summaries.
        "total_library_models": total_library_models,  # I supply the total count.
        "ready_models": ready_models,  # I supply the ready count.
        "experimental_models": experimental_models,  # I supply the experimental count.
        "catalogued_models": catalogued_models,  # I supply the catalogued count.
        "compare_items": compare_items,  # I supply valid comparison objects.
        "compare_codes": requested_compare_codes,  # I supply selected codes for checkbox state.
        "comparison_message": comparison_message,  # I supply comparison feedback.
        "my_strategy_rows": my_strategy_rows,  # I supply enriched strategy summaries.
        "my_strategy_count": my_strategies.count(),  # I supply the user's strategy count.
        "available_symbols": available_symbols,  # I supply historical asset choices.
        "symbols": available_symbols,  # I retain the older compatibility variable name.
        "selected_validation_strategy": selected_validation_strategy,  # I supply the selected strategy value.
        "selected_validation_symbol": selected_validation_symbol,  # I supply the normalised symbol.
        "selected_stress_scenario": selected_stress_scenario,  # I supply the chosen scenario.
        "robustness_test_count": robustness_test_count,  # I supply the user's robustness count.
        "latest_user_robustness_test": latest_user_robustness_test,  # I supply the latest user-level result.
        "latest_user_robustness_label": latest_user_robustness_label,  # I supply its readable label.
        "latest_user_robustness_explanation": latest_user_robustness_explanation,  # I supply its explanation.
        "stress_test_count": stress_test_count,  # I supply the user's stress count.
        "latest_strategy_stress_test": latest_strategy_stress_test,  # I supply the latest user-level stress result.
        "strategies": my_strategies,  # I retain the strategy collection used by forms and older templates.
        "page_title": "Strategy & Model Research",  # I supply page information.
    }  # I close the context dictionary.

    # 8.15 HTML RESPONSE
    return render(request, "strategy_builder/list.html", context)  # Django renders the template and returns an HTTP response.

# ============================================================
# 9. LEGACY ROBUSTNESS ROUTE — REDIRECT COMPATIBILITY
# ============================================================
@login_required  # I require authentication.
def strategy_robustness(request):  # I keep the previous route usable.
    """Redirect legacy robustness links to the combined Strategies page."""
    strategy_id = request.GET.get("strategy") or ""  # I read an optional strategy query parameter.
    base_url = reverse("strategy_builder:list")  # I resolve the main workspace URL.
    if strategy_id:  # I check whether a strategy was supplied.
        return redirect(  # I redirect while retaining the selection in the query string.
            (
                f"{base_url}"  # I insert the resolved route.
                f"?strategy={strategy_id}"  # I append the supplied strategy value.
                "#strategyRobustnessSection"  # I append the browser section fragment.
            )  # I close the combined string.
        )  # I return the redirect response.
    return redirect(  # I handle links without a strategy selection.
        (
            f"{base_url}"  # I insert the workspace URL.
            "#strategyRobustnessSection"  # I select the robustness section.
        )  # I close the combined string.
    )  # I return the redirect.

# ============================================================
# 10. LEGACY ROBUSTNESS RESULTS ROUTE
# ============================================================
@login_required  # I require authentication.
def strategy_robustness_results(request):  # I handle the older results route.
    """Redirect old robustness-results links to the Strategies workspace."""
    return redirect(_strategy_workspace_url("strategyRobustnessSection"))  # I return a section redirect rather than rendering a separate page.

# ============================================================
# 11. CREATE A CUSTOM STRATEGY — FORM VALIDATION
# ============================================================
@login_required  # I require a signed-in user.
def strategy_create(request):  # I handle strategy creation requests.
    """Validate a StrategyCreateForm and redirect successful creation to backtesting."""
    form = StrategyCreateForm(request.POST or None)  # I bind nonempty submitted data or create an unbound form.
    if request.method == "POST" and form.is_valid():  # Short-circuit AND validates only when the method matches.
        strategy = form.save(request.user)  # I call this form's custom save method with the current user.
        messages.success(request, "Strategy created successfully.")  # I queue success feedback.
        return redirect(  # I redirect to the new strategy's backtest route.
            "strategy_builder:backtest",  # I identify the named route.
            strategy_id=strategy.pk,  # I supply its required URL argument.
        )  # I return the redirect.
    context = {  # I prepare data for GET requests or unsuccessful validation.
        "form": form,  # I include the form, which can contain validation errors.
        "page_title": "Create Strategy",  # I include the page title.
    }  # I close the context.
    return render(request, "strategy_builder/create.html", context)  # I render the creation form.

# ============================================================
# 12. ADD LIBRARY METADATA — DEFERRED MODEL SAVE
# ============================================================
@login_required  # This view checks login; it contains no additional is_staff check.
def library_item_create(request):  # I handle library-item creation.
    """Create an active library item whose initial implementation status is catalogued."""
    if request.method == "POST":  # I distinguish submitted forms from initial page requests.
        form = StrategyLibraryItemForm(request.POST)  # I bind submitted data to the form.
        if form.is_valid():  # I validate it using the form's rules.
            library_item = form.save(commit=False)  # I obtain a model instance without saving it yet.
            library_item.implementation_status = "catalogued"  # I mark metadata as catalogued rather than numerically implemented.
            library_item.is_active = True  # I make the item eligible for the active library.
            library_item.display_order = 999  # I give it the configured later display-order value.
            library_item.save()  # I persist the model instance.
            messages.success(  # I queue creation feedback.
                request,  # I attach it to the request.
                (
                    f"{library_item.name} was added "  # I insert the new item's name.
                    f"to the MarketPulse Strategy & "  # I continue the message.
                    f"Model Library."  # I complete it.
                ),  # I close the string.
            )  # I finish feedback.
            return redirect("strategy_builder:list")  # I return to the workspace after successful creation.
    else:  # I handle a non-POST request.
        form = StrategyLibraryItemForm()  # I create an empty form.
    context = {  # I prepare initial or invalid-form display data.
        "form": form,  # I include the form and any validation errors.
        "page_title": "Add Strategy or Model",  # I include the page title.
    }  # I close the context.
    return render(request, "strategy_builder/library_add.html", context)  # I render the library-item form.

# ============================================================
# 13. BACKTEST A STRATEGY — VALIDATED KEYWORD UNPACKING
# ============================================================
@login_required  # I require authentication.
def backtest_strategy(request, strategy_id):  # Django supplies the request and route parameter.
    """Run a historical backtest for a strategy owned by the current user."""
    strategy = get_object_or_404(  # I retrieve the strategy or raise Http404.
        Strategy,  # I identify its model.
        pk=strategy_id,  # I match the URL's strategy ID.
        user=request.user,  # I enforce ownership in the lookup.
    )  # I close retrieval.
    form = BacktestForm(request.POST or None)  # I create a bound or unbound backtest form.
    if request.method == "POST" and form.is_valid():  # I require a submitted request and valid data.
        try:  # I handle exceptions from calculation and subsequent operations.
            backtest = run_backtest(  # I call the imported simulation engine.
                strategy,  # I pass the owned strategy.
                **form.cleaned_data,  # Double-star unpacking passes validated dictionary entries as keyword arguments.
            )  # I store the returned backtest object.
            messages.success(  # I queue completion feedback.
                request,  # I attach it to the request.
                (
                    f"Backtest completed for "  # I begin the message.
                    f"{strategy.name}."  # I insert the strategy name.
                ),  # I close the string.
            )  # I finish feedback.
            return redirect(  # I navigate to the saved backtest result.
                "strategy_builder:results",  # I identify the results route.
                backtest_id=backtest.pk,  # I pass the backtest's primary key.
            )  # I return the redirect response.
        except Exception as error:  # I catch exceptions raised within the try block.
            messages.error(request, str(error))  # I convert the exception to text and queue it as feedback.
    context = {  # I prepare the initial or unsuccessful form response.
        "strategy": strategy,  # I include the selected strategy.
        "form": form,  # I include the form and validation errors.
        "page_title": f"Backtest {strategy.name}",  # I build the title with an f-string.
    }  # I close the context.
    return render(request, "strategy_builder/backtest_form.html", context)  # I display the backtest form.

# ============================================================
# 14. BACKTEST RESULTS — RELATED RECORDS AND OWNERSHIP
# ============================================================
@login_required  # I require authentication.
def backtest_results(request, backtest_id):  # I receive the requested result ID.
    """Display an owned backtest and its related simulated trades."""
    backtest = get_object_or_404(  # I retrieve the result or raise Http404.
        Backtest,  # I identify the model.
        pk=backtest_id,  # I match the requested backtest.
        strategy__user=request.user,  # A related-field lookup restricts results through the strategy owner.
    )  # I close retrieval.
    trades = backtest.trades.all().order_by("entry_date")  # I query related trades in entry-date order.
    context = {  # I prepare results-template data.
        "backtest": backtest,  # I supply the result object and its metrics.
        "trades": trades,  # I supply the simulated trade collection.
        "page_title": "Backtest Results",  # I supply the title.
    }  # I close the dictionary.
    return render(  # I return the rendered results page.
        request,  # I pass the current request.
        "strategy_builder/backtest_results.html",  # I select the results template.
        context,  # I supply its display data.
    )  # I finish the response.

# Lecturer explanation:
# I use views to coordinate HTTP requests, form validation,
# owned database records and imported calculation engines.
# I pass prepared dictionaries to templates and redirect after
# successful submissions. The numerical algorithms live in
# the imported analytics and backtesting modules.