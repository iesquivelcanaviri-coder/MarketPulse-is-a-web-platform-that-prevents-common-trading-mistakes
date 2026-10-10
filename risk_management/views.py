"""
MARKETPULSE - RISK MANAGEMENT VIEWS

Purpose:
Handle the Risk Planner, stress-test submission and stress-test results.

Framework:
Request -> authenticated view -> form/models/services -> template or redirect.

Risk Planner:
Manual entry price -> Alpaca fallback -> historical-close fallback.
Historical context and validated inputs feed the risk calculator.

Stress Testing:
User-owned strategy + symbol + scenario presets -> internal analytics engine.

Market Condition analysis belongs in data_management/views.py.
"""

# ============================================================
# 1. DJANGO IMPORTS
# ============================================================
from django.contrib import messages  # Import: I access Django's user-feedback message system.
from django.contrib.auth.decorators import login_required  # Decorator import: I require authentication for these views.
from django.shortcuts import (  # Grouped import: I access common request-handling helpers.
    get_object_or_404,  # Helper: I retrieve an object or return an HTTP 404 response.
    redirect,  # Helper: I return a redirect response.
    render,  # Helper: I render a template with context data.
)  # Closing parenthesis: I finish the grouped import.

# ============================================================
# 2. CORE MODELS
# ============================================================
from core.models import (  # Model imports: I access stored market data and strategies.
    MarketData,  # Model class: I query historical asset records.
    Strategy,  # Model class: I retrieve user-owned strategies.
)  # Closing parenthesis: I finish the model imports.

# ============================================================
# 3. RISK FORM
# ============================================================
from .forms import RiskPlannerForm  # Relative import: I use this application's risk-input form.

# ============================================================
# 4. RISK CALCULATION SERVICES
# ============================================================
from .calculators import (  # Relative import: I access separate calculation helpers.
    calculate_trade_risk_plan,  # Function import: I calculate a plan from validated inputs.
    get_market_risk_context,  # Function import: I retrieve historical risk context for a symbol.
)  # Closing parenthesis: I finish the calculator imports.

# ============================================================
# 5. ALPACA MARKET-DATA SERVICE
# ============================================================
from data_management.services.alpaca import (  # Service import: I access the project's Alpaca integration.
    AlpacaServiceError,  # Exception class: I handle the specified service failure.
    get_stock_snapshot,  # Function import: I request a stock snapshot.
)  # Closing parenthesis: I finish the service imports.

# ============================================================
# 6. INTERNAL ANALYTICS ENGINE AND RESULT MODEL
# ============================================================
from analysis_tools.analyzers import (  # Module import: I access the internal analytics engine.
    run_stress_test,  # Function import: I delegate stress-test calculations.
)  # Closing parenthesis: I finish the analyzer import.
from analysis_tools.models import (  # Model import: I access saved analytics results.
    StressTest,  # Model class: I query stress-test records.
)  # Closing parenthesis: I finish the result-model import.

# ============================================================
# 7. TRADE AND PORTFOLIO RISK PLANNER
# ============================================================
@login_required  # Decorator: Django requires a logged-in user before running this view.
def calculator(request):  # Function and parameter: I receive the browser's HTTP request.
    """Display the Risk Planner and process validated risk-plan inputs."""

    # --------------------------------------------------------
    # 7.1 SYMBOLS WITH STORED HISTORICAL DATA
    # --------------------------------------------------------
    available_symbols = list(  # Assignment and conversion: I evaluate the query into a Python list.
        MarketData.objects  # Model manager: I begin a historical-data query.
        .order_by("symbol")  # Method chaining: I sort the symbols.
        .values_list("symbol", flat=True)  # Query projection: I retrieve symbol values rather than model instances.
        .distinct()  # Query method: I remove duplicate symbols.
    )  # Closing parenthesis: I finish creating the symbol list.

    # --------------------------------------------------------
    # 7.2 SELECT AND STANDARDISE THE CURRENT SYMBOL
    # --------------------------------------------------------
    selected_symbol = (  # Assignment: I choose the first truthy symbol source.
        request.POST.get("symbol")  # Dictionary-like lookup: I first check submitted form data.
        or request.GET.get("symbol")  # Logical OR: I next check URL query parameters.
        or (available_symbols[0] if available_symbols else "")  # Conditional expression: I use the first stored symbol or an empty string.
    )  # Closing parenthesis: I finish selecting the symbol.
    selected_symbol = selected_symbol.strip().upper()  # String methods: I remove surrounding whitespace and uppercase the ticker.

    # --------------------------------------------------------
    # 7.3 BUILD THE RISK FORM
    # --------------------------------------------------------
    form = RiskPlannerForm(  # Object construction: I create the form used by the template and validation.
        request.POST or None,  # Fallback expression: I bind non-empty submitted data, otherwise pass None.
        initial={  # Dictionary: I supply initial values for an unbound form.
            "symbol": selected_symbol,  # Key-value pair: I initialise the asset symbol.
            "trading_capital": 10000,  # Integer: I initialise the capital setting.
            "risk_percentage": 1,  # Integer: I initialise the risk-percentage setting.
            "currency": "USD",  # String: I initialise the currency label.
            "direction": "long",  # String: I initialise the trade direction.
            "stop_method": "percentage",  # String: I initialise the stop calculation method.
            "stop_loss_percentage": 5,  # Integer: I initialise the stop-loss percentage.
            "atr_multiplier": 2,  # Integer: I initialise the ATR multiplier.
        },  # Closing brace: I finish the initial-value dictionary.
    )  # Closing call: I finish building the form.

    # --------------------------------------------------------
    # 7.4 BUILD THE HISTORICAL CONTEXT MAP
    # --------------------------------------------------------
    market_context_map = {}  # Dictionary assignment: I prepare a symbol-to-context lookup.
    for symbol in available_symbols:  # Iteration: I process every available historical symbol.
        historical_context = get_market_risk_context(symbol)  # Function call: I request that symbol's historical risk context.
        if historical_context:  # Truthiness condition: I store only a truthy context result.
            market_context_map[symbol] = historical_context  # Dictionary assignment: I associate the symbol with its context.

    # --------------------------------------------------------
    # 7.5 SELECT THE CONTEXT AND INITIALISE THE RESULT
    # --------------------------------------------------------
    market_context = market_context_map.get(selected_symbol)  # Dictionary lookup: I retrieve the selected asset's context, or None.
    result = None  # Initial state: I begin without a calculated risk plan.

    # --------------------------------------------------------
    # 7.6 PROCESS A VALID POST REQUEST
    # --------------------------------------------------------
    if request.method == "POST" and form.is_valid():  # Condition and method call: I calculate only for a valid submitted form.
        cleaned = form.cleaned_data  # Attribute access: I obtain validated and converted form values.
        selected_symbol = cleaned["symbol"].strip().upper()  # Dictionary indexing and string methods: I standardise the validated ticker.
        market_context = market_context_map.get(selected_symbol)  # Dictionary lookup: I refresh the context for the validated symbol.

        # ----------------------------------------------------
        # 7.7 ENTRY PRICE: MANUAL INPUT FIRST
        # ----------------------------------------------------
        entry_price = cleaned.get("entry_price")  # Dictionary lookup: I read the optional manual entry price.
        if entry_price is None:  # Identity comparison: I request Alpaca only when no manual price is available.
            try:  # Exception handling: I begin the service request.
                alpaca_snapshot = get_stock_snapshot(selected_symbol)  # Function call: I retrieve the selected asset's snapshot.
                entry_price = alpaca_snapshot.get("latest_price")  # Dictionary lookup: I read its latest-price value.
            except AlpacaServiceError:  # Exception branch: I handle this specific service error.
                entry_price = None  # Assignment: I leave the price unavailable so the historical fallback can run.

        # ----------------------------------------------------
        # 7.8 HISTORICAL-CLOSE FALLBACK
        # ----------------------------------------------------
        if entry_price is None and market_context:  # Combined condition: I use historical context only if a price is still missing.
            entry_price = market_context.get("latest_close")  # Dictionary lookup: I obtain the stored historical close.
        if entry_price is None:  # Identity comparison: I check whether all price sources were unavailable.
            form.add_error(  # Form method: I attach feedback to the entry-price field.
                "entry_price",  # Field name: I identify the input requiring attention.
                (  # Grouping parentheses: I combine the original error strings.
                    "MarketPulse could not obtain a current "  # String: I begin the error message.
                    "Alpaca price or a stored historical price. "  # Adjacent string: I explain the unavailable sources.
                    "Enter an entry price manually."  # Adjacent string: I give the next step.
                ),  # Closing parenthesis: I finish the message.
            )  # Closing call: I finish adding the field error.
        else:  # Alternative branch: I continue when an entry price is available.

            # ------------------------------------------------
            # 7.9 CALCULATE THE RISK PLAN
            # ------------------------------------------------
            try:  # Exception handling: I process calculation and display-value conversion together.
                result = calculate_trade_risk_plan(  # Function call: I delegate the numerical risk calculation.
                    trading_capital=cleaned["trading_capital"],  # Keyword argument: I supply validated capital.
                    risk_percentage=cleaned["risk_percentage"],  # Keyword argument: I supply the validated risk setting.
                    entry_price=entry_price,  # Keyword argument: I supply the selected price source's value.
                    direction=cleaned["direction"],  # Keyword argument: I supply long or short direction.
                    stop_method=cleaned["stop_method"],  # Keyword argument: I supply the stop calculation method.
                    stop_loss_percentage=cleaned.get("stop_loss_percentage"),  # Optional lookup: I supply the percentage stop setting.
                    fixed_stop_price=cleaned.get("stop_price"),  # Optional lookup: I supply the fixed stop price.
                    atr=(market_context.get("atr_14") if market_context else None),  # Conditional expression: I supply historical ATR when context exists.
                    atr_multiplier=cleaned.get("atr_multiplier"),  # Optional lookup: I supply the ATR multiplier.
                    target_price=cleaned.get("target_price"),  # Optional lookup: I supply the planned target price.
                )  # Closing call: I finish requesting the risk plan.

                # --------------------------------------------
                # 7.10 ADD INFORMATION FOR DISPLAY
                # --------------------------------------------
                result["symbol"] = selected_symbol  # Dictionary assignment: I include the standardised asset symbol.
                result["currency"] = cleaned.get("currency", "USD")  # Lookup with default: I include the supplied currency or USD if the key is absent.
                result["direction"] = cleaned["direction"]  # Dictionary assignment: I include the trade direction.
                result["risk_percentage"] = float(cleaned["risk_percentage"])  # Type conversion: I include the risk setting as a float.
                result["trading_capital"] = float(cleaned["trading_capital"])  # Type conversion: I include capital as a float.
                result["target_price"] = (  # Dictionary assignment: I prepare the optional target for display.
                    float(cleaned["target_price"])  # Type conversion: I convert a truthy target to float.
                    if cleaned.get("target_price")  # Truthiness condition: I check whether the target value is truthy.
                    else None  # Alternative value: I use None for a falsey target.
                )  # Closing parenthesis: I finish the display target expression.
            except ValueError as error:  # Exception and binding: I capture a ValueError from this processing block.
                form.add_error(None, str(error))  # Form method: I attach the exception text as a form-wide error.

    # --------------------------------------------------------
    # 7.11 BUILD THE TEMPLATE CONTEXT
    # --------------------------------------------------------
    context = {  # Dictionary: I collect the data made available to the template.
        "form": form,  # Key-value pair: I supply fields and validation errors.
        "result": result,  # Key-value pair: I supply the calculated plan or None.
        "market_context": market_context,  # Key-value pair: I supply the selected historical context.
        "market_context_map": market_context_map,  # Key-value pair: I supply the full symbol-context mapping.
        "selected_symbol": selected_symbol,  # Key-value pair: I preserve the selected ticker.
        "available_symbols": available_symbols,  # Key-value pair: I supply historical asset choices.
    }  # Closing brace: I finish the context dictionary.

    # --------------------------------------------------------
    # 7.12 DISPLAY THE RISK PLANNER
    # --------------------------------------------------------
    return render(  # Return statement and helper call: I produce the page's HTTP response.
        request,  # Positional argument: I pass the current request.
        "risk_management/calculator.html",  # Template path: I identify the page to render.
        context,  # Context argument: I pass the prepared display data.
    )  # Closing call: I finish rendering the Risk Planner.

# ============================================================
# 8. STRESS-TEST SUBMISSION
# ============================================================
@login_required  # Decorator: I require a logged-in user.
def stress_test(request):  # View function: I handle the stress-testing page and submitted inputs.
    """Run a user-selected stress scenario through the internal analytics engine."""

    # --------------------------------------------------------
    # 8.1 RETRIEVE THE USER'S STRATEGIES
    # --------------------------------------------------------
    strategies = (  # Assignment: I prepare the strategy QuerySet.
        Strategy.objects  # Model manager: I begin the strategy query.
        .filter(user=request.user)  # Ownership filter: I retrieve only the current user's strategies.
        .order_by("name")  # Ordering: I sort the choices by name.
    )  # Closing parenthesis: I finish the strategy query.

    # --------------------------------------------------------
    # 8.2 RETRIEVE AVAILABLE HISTORICAL SYMBOLS
    # --------------------------------------------------------
    symbols = list(  # List conversion: I evaluate the symbol query.
        MarketData.objects  # Model manager: I query stored historical data.
        .order_by("symbol")  # Ordering: I sort the symbols.
        .values_list("symbol", flat=True)  # Projection: I retrieve individual symbol values.
        .distinct()  # Query method: I remove duplicate symbols.
    )  # Closing parenthesis: I finish the symbol list.

    # --------------------------------------------------------
    # 8.3 READ AND CHECK SUBMITTED SELECTIONS
    # --------------------------------------------------------
    if request.method == "POST":  # Conditional: I process submitted inputs only for POST requests.
        strategy_id = request.POST.get("strategy")  # Request lookup: I read the selected strategy ID.
        symbol = request.POST.get("symbol", "").strip().upper()  # Lookup and string methods: I standardise the submitted symbol.
        scenario = request.POST.get("scenario", "crash")  # Lookup with default: I use crash if the scenario key is absent.
        if not strategy_id:  # Truthiness check: I require a strategy selection.
            messages.error(request, "Select a strategy first.")  # Feedback: I report the missing strategy.
        elif not symbol:  # Alternative condition: I require a non-empty symbol.
            messages.error(request, "Select an asset first.")  # Feedback: I report the missing asset.
        else:  # Alternative branch: I continue when both selections are present.
            strategy = get_object_or_404(  # Retrieval helper: I load the matching strategy or return a 404.
                Strategy,  # Model argument: I identify the object type.
                id=strategy_id,  # Lookup argument: I match the submitted record ID.
                user=request.user,  # Ownership restriction: I require the strategy to belong to the current user.
            )  # Closing call: I finish retrieving the strategy.

            # ------------------------------------------------
            # 8.4 PREDEFINED SCENARIO PARAMETERS
            # ------------------------------------------------
            scenarios = {  # Nested dictionary: I map scenario codes to analytics parameters.
                "crash": {  # Dictionary entry: I define severe-market-decline settings.
                    "crash_start": 0.70,  # Float: I preserve the scenario's start-position parameter.
                    "crash_magnitude": 0.20,  # Float: I preserve the decline-magnitude parameter.
                },  # Closing brace: I finish crash settings.
                "volatility_spike": {  # Dictionary entry: I define volatility-spike settings.
                    "spike_start": 0.50,  # Float: I preserve the spike start parameter.
                    "spike_duration": 0.10,  # Float: I preserve the spike duration parameter.
                    "spike_magnitude": 3.0,  # Float: I preserve the spike multiplier.
                },  # Closing brace: I finish volatility settings.
                "liquidity_crisis": {  # Dictionary entry: I define liquidity-shock settings.
                    "crisis_start": 0.60,  # Float: I preserve the crisis start parameter.
                    "crisis_duration": 0.20,  # Float: I preserve the crisis duration parameter.
                    "volume_reduction": 0.70,  # Float: I preserve the volume-reduction parameter.
                },  # Closing brace: I finish liquidity settings.
                "regime_change": {  # Dictionary entry: I define market-condition-change settings.
                    "change_point": 0.50,  # Float: I preserve the change-position parameter.
                    "new_trend": -0.01,  # Signed float: I preserve the new-trend parameter.
                },  # Closing brace: I finish regime-change settings.
            }  # Closing brace: I finish scenario presets.
            parameters = scenarios.get(scenario)  # Dictionary lookup: I retrieve the selected preset or None.
            if parameters is None:  # Identity comparison: I reject an unknown scenario code.
                messages.error(request, "Choose a valid stress scenario.")  # Feedback: I report the invalid selection.
            else:  # Alternative branch: I continue with a recognised scenario.

                # --------------------------------------------
                # 8.5 RUN THE INTERNAL ANALYTICS ENGINE
                # --------------------------------------------
                stress_result = run_stress_test(  # Function call: I delegate the stress-test calculation.
                    strategy,  # Positional argument: I supply the user-owned strategy.
                    symbol,  # Positional argument: I supply the standardised asset symbol.
                    scenario,  # Positional argument: I supply the scenario code.
                    parameters,  # Positional argument: I supply its predefined settings.
                )  # Closing call: I finish the engine request.
                if stress_result:  # Truthiness condition: I check whether the engine returned a truthy result.
                    messages.success(request, "Stress test completed successfully.")  # Feedback: I announce successful completion.
                    return redirect("risk_management:stress_test_results")  # Early return and named route: I send the browser to the results page.
                else:  # Alternative branch: I handle a falsey engine result.
                    messages.error(  # Feedback call: I report that the test could not complete.
                        request,  # Positional argument: I attach the message to the current request.
                        (  # Grouping parentheses: I combine the original message strings.
                            "MarketPulse could not complete the "  # String: I begin the error message.
                            "stress test. Make sure the selected "  # Adjacent string: I introduce the data requirement.
                            "asset has sufficient historical data."  # Adjacent string: I finish the guidance.
                        ),  # Closing parenthesis: I finish the message.
                    )  # Closing call: I finish adding the feedback.

    # --------------------------------------------------------
    # 8.6 DISPLAY THE STRESS-TEST PAGE
    # --------------------------------------------------------
    return render(  # Return statement: I render the form page for GET or unsuccessful POST processing.
        request,  # Request argument: I pass the current request.
        "risk_management/stress_test.html",  # Template path: I identify the stress-test page.
        {  # Context dictionary: I supply the available form choices.
            "strategies": strategies,  # Key-value pair: I supply the current user's strategies.
            "symbols": symbols,  # Key-value pair: I supply historical asset symbols.
        },  # Closing brace: I finish the context.
    )  # Closing call: I finish rendering the stress-test page.

# ============================================================
# 9. STRESS-TEST RESULTS
# ============================================================
@login_required  # Decorator: I require authentication before displaying saved results.
def stress_test_results(request):  # View function: I handle the user's stress-result page.
    """Display the logged-in user's latest 20 stress-test results."""
    tests = (  # Assignment: I prepare the results QuerySet.
        StressTest.objects  # Model manager: I access saved stress-test records.
        .filter(user=request.user)  # Ownership filter: I retrieve only the current user's results.
        .order_by("-created_at")[:20]  # Descending ordering and slicing: I select at most the newest twenty records.
    )  # Closing parenthesis: I finish the results query.
    return render(  # Return statement and helper: I produce the results page response.
        request,  # Request argument: I pass the current request.
        "risk_management/stress_test_results.html",  # Template path: I identify the results page.
        {  # Context dictionary: I supply the result collection.
            "tests": tests,  # Key-value pair: The template accesses these records as tests.
        },  # Closing brace: I finish the context.
    )  # Closing call: I finish rendering the results page.