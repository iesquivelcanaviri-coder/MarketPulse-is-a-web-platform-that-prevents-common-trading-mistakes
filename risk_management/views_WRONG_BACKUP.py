# ============================================================
# MARKETPULSE — MARKET CONDITION ANALYSIS BACKUP
# ============================================================
# Purpose: analyse historical market conditions and show results.
# Framework: request → view → ORM / analysis engine → template.
# Lecture: Python building blocks coordinate this Django workflow.

# ============================================================
# 1. IMPORTS — REUSE CODE FROM OTHER MODULES
# ============================================================
from django.contrib import messages  # Import Django's user-feedback tools.
from django.contrib.auth.decorators import login_required  # Import a decorator that requires authentication.
from django.shortcuts import redirect, render  # Import helpers for redirects and template responses.
from core.models import MarketData  # Import the model containing historical market observations.
from analysis_tools.analyzers import (  # Start a grouped import from the analysis module.
    identify_market_regime,  # Import the function that analyses market conditions.
)  # Finish the grouped import.
from analysis_tools.models import (  # Start a grouped import from the analysis models.
    MarketRegime,  # Import the model containing market-condition results.
)  # Finish the grouped import.

# ============================================================
# 2. MARKET CONDITION VIEW — HANDLE THE ANALYSIS PAGE
# ============================================================
@login_required  # Decorator: require the user to log in before accessing this view.
def market_condition(request):  # Function definition: receive the current HTTP request.
    """Analyse an asset's market condition and display its results."""

    # --------------------------------------------------------
    # 2.1 GET AND NORMALISE HISTORICAL SYMBOLS
    # --------------------------------------------------------
    stored_symbols_query = (  # Assignment: prepare a database query for stored symbols.
        MarketData.objects  # Access the model's database manager.
        .order_by("symbol")  # Order the records by symbol.
        .values_list("symbol", flat=True)  # Request symbol values rather than full model objects.
        .distinct()  # Remove duplicate symbol values in the query.
    )  # Finish the query expression.
    symbols = sorted(  # Function call: create a sorted list from the normalised set.
        {  # Set comprehension: collect unique normalised symbols.
            str(symbol).strip().upper()  # Convert to text, remove outer spaces, and use uppercase.
            for symbol in stored_symbols_query  # Iteration: process each symbol returned by the query.
            if symbol  # Filtering condition: skip values that are false-like before normalisation.
        }  # Finish the set comprehension.
    )  # Finish sorting; symbols is now a list.

    # --------------------------------------------------------
    # 2.2 CHOOSE THE CURRENT SYMBOL
    # --------------------------------------------------------
    # Priority: POST value → GET value → first stored symbol → "".
    selected_symbol = (  # Assignment: choose the first truthy value in this expression.
        request.POST.get("symbol")  # Dictionary-like lookup: read the submitted form symbol.
        or request.GET.get("symbol")  # Boolean operator: otherwise read the URL query parameter.
        or (symbols[0] if symbols else "")  # Conditional expression: use the first symbol or an empty string.
    )  # Finish selecting the symbol.
    selected_symbol = (  # Assignment: normalise the selected value.
        selected_symbol.strip().upper()  # Method chaining: remove spaces and convert to uppercase.
        if selected_symbol  # Conditional expression: normalise only when the value is truthy.
        else ""  # Use an empty string when no symbol was selected.
    )  # Finish the normalisation expression.

    # --------------------------------------------------------
    # 2.3 SUMMARISE THE SELECTED HISTORICAL DATA
    # --------------------------------------------------------
    historical_observations = 0  # Integer variable: start with no observations counted.
    earliest_date = None  # None represents an earliest date that is not yet available.
    latest_date = None  # None represents a latest date that is not yet available.
    if selected_symbol:  # Conditional: query historical data only when a symbol is present.
        selected_market_data = (  # Assignment: prepare the selected asset's historical query.
            MarketData.objects  # Access historical market records through the ORM.
            .filter(symbol=selected_symbol)  # Keyword argument: keep records matching the symbol.
            .order_by("date")  # Sort dates in ascending order.
        )  # Finish the historical query.
        historical_observations = selected_market_data.count()  # Count matching database records.
        first_record = selected_market_data.first()  # Get the earliest record, or None if empty.
        latest_record = selected_market_data.last()  # Get the latest record, or None if empty.
        if first_record:  # Conditional: check that an earliest record exists.
            earliest_date = first_record.date  # Attribute access: read its date.
        if latest_record:  # Conditional: check that a latest record exists.
            latest_date = latest_record.date  # Attribute access: read its date.

    # --------------------------------------------------------
    # 2.4 VALIDATE AND PROCESS AN ANALYSIS REQUEST
    # --------------------------------------------------------
    if request.method == "POST":  # Comparison: run analysis handling for POST requests.
        if not selected_symbol:  # Boolean negation: detect a missing or empty symbol.
            messages.error(  # Function call: add an error message for the user.
                request,  # Associate the message with this request.
                (  # Start an implicitly joined string expression.
                    "Select an asset before running "  # First part of the original message.
                    "Market Condition Analysis."  # Adjacent string literals join automatically.
                ),  # Finish the message argument.
            )  # Finish the error-message call.
        elif historical_observations < 20:  # Alternative branch: require at least 20 stored observations.
            messages.error(  # Add feedback explaining the insufficient data.
                request,  # Associate the feedback with this request.
                (  # Start the combined formatted message.
                    f"{selected_symbol} currently has only "  # f-string: insert the selected symbol.
                    f"{historical_observations} stored historical "  # Insert the observation count.
                    f"observations. More historical data is needed "  # Continue the original message.
                    f"before MarketPulse can analyse the market "  # Continue the original message.
                    f"condition reliably."  # Finish the original message.
                ),  # Finish the combined string argument.
            )  # Finish the error-message call.
        else:  # Branch: proceed when a symbol and enough observations are available.
            try:  # Exception handling: attempt the analysis and its response handling.

                # ------------------------------------------------
                # 2.5 CALL THE INTERNAL ANALYSIS ENGINE
                # ------------------------------------------------
                regime_result = (  # Assignment: store the analyser's return value.
                    identify_market_regime(selected_symbol)  # Function call: analyse the selected asset.
                )  # Finish the assignment expression.
                if regime_result:  # Conditional: treat a truthy return value as success.
                    messages.success(  # Add a success message to the request.
                        request,  # Associate the message with this request.
                        (  # Start the combined success message.
                            f"Market condition analysis for "  # First part of the original message.
                            f"{selected_symbol} completed."  # Insert the analysed symbol.
                        ),  # Finish the success-message argument.
                    )  # Finish the success-message call.
                    return redirect(  # Return statement: stop this view and return a redirect response.
                        "data_management:market_condition"  # Preserve the original redirect string.
                        + f"?symbol={selected_symbol}"  # String concatenation: append the symbol parameter.
                    )  # Finish the redirect call.
                messages.error(  # Add an error when the analyser returns a false-like result.
                    request,  # Associate the error with this request.
                    (  # Start the original combined error message.
                        "MarketPulse could not determine a "  # First part of the message.
                        "market condition from the available "  # Continue the message.
                        "historical observations."  # Finish the message.
                    ),  # Finish the message argument.
                )  # Finish the error-message call.
            except Exception as error:  # Catch Exception subclasses raised within this try block.
                messages.error(  # Show the caught failure through Django's message framework.
                    request,  # Associate the feedback with this request.
                    (  # Start the combined failure message.
                        "Market condition analysis could not "  # First part of the original message.
                        f"be completed: {error}"  # f-string: include the exception's text.
                    ),  # Finish the message argument.
                )  # Finish the error-message call.

    # --------------------------------------------------------
    # 2.6 GET THE LATEST STORED CONDITION RESULT
    # --------------------------------------------------------
    latest_regime = None  # Initialise the result variable before querying.
    if selected_symbol:  # Conditional: only query results when a symbol is selected.
        latest_regime = (  # Assignment: obtain the newest matching stored result.
            MarketRegime.objects  # Access market-condition results through the ORM.
            .filter(symbol=selected_symbol)  # Keep results for the selected symbol.
            .order_by("-date", "-created_at")  # Sort newest date first, then newest creation time.
            .first()  # Return the first matching result, or None.
        )  # Finish the latest-result query.

    # --------------------------------------------------------
    # 2.7 TRANSLATE TECHNICAL CODES INTO PLAIN LANGUAGE
    # --------------------------------------------------------
    market_interpretation = None  # Initialise the explanation as unavailable.
    if latest_regime:  # Conditional: create an interpretation when a stored result exists.
        regime_code = latest_regime.regime  # Attribute access: read the technical condition code.
        interpretations = {  # Dictionary: map each recognised code to an explanation.
            "bull": (  # Dictionary key: explanation for the bull condition.
                "Prices have generally been moving upward. "  # First part of the explanation.
                "This resembles an upward-trending market."  # Adjacent string: complete the explanation.
            ),  # Finish the bull dictionary entry.
            "bear": (  # Dictionary key: explanation for the bear condition.
                "Prices have generally been moving downward. "  # First part of the explanation.
                "This resembles a declining market environment."  # Complete the explanation.
            ),  # Finish the bear dictionary entry.
            "sideways": (  # Dictionary key: explanation for a sideways condition.
                "Prices have not shown a strong sustained "  # First part of the explanation.
                "direction. The market appears relatively "  # Continue the explanation.
                "range-bound or sideways."  # Complete the explanation.
            ),  # Finish the sideways dictionary entry.
            "high_volatility": (  # Dictionary key: explanation for high volatility.
                "Recent price movements have been relatively "  # First part of the explanation.
                "large. This indicates a higher-volatility "  # Continue the explanation.
                "market environment."  # Complete the explanation.
            ),  # Finish the high-volatility dictionary entry.
            "low_volatility": (  # Dictionary key: explanation for low volatility.
                "Recent price movements have been relatively "  # First part of the explanation.
                "small. This indicates a lower-volatility "  # Continue the explanation.
                "market environment."  # Complete the explanation.
            ),  # Finish the low-volatility dictionary entry.
        }  # Finish the interpretation dictionary.
        market_interpretation = (  # Assignment: choose a matching explanation or a fallback.
            interpretations.get(regime_code)  # Dictionary lookup: get the explanation, or None.
            or (  # Boolean operator: use this fallback if the lookup is false-like.
                "MarketPulse identified this market condition "  # First part of the fallback.
                "from the available historical price behaviour."  # Complete the fallback.
            )  # Finish the fallback string expression.
        )  # Finish choosing the interpretation.

    # --------------------------------------------------------
    # 2.8 GET RECENT CONDITION HISTORY
    # --------------------------------------------------------
    recent_regimes = []  # List literal: start with an empty history.
    if selected_symbol:  # Conditional: retrieve history when a symbol is present.
        recent_regimes = (  # Assignment: prepare the selected symbol's recent-result query.
            MarketRegime.objects  # Access the result model's manager.
            .filter(symbol=selected_symbol)  # Keep results for the selected asset.
            .order_by("-date", "-created_at")[:10]  # Sort newest first and limit the query to ten results.
        )  # Finish the recent-history query.

    # --------------------------------------------------------
    # 2.9 BUILD THE TEMPLATE CONTEXT
    # --------------------------------------------------------
    context = {  # Dictionary: give the template named values to display.
        "symbols": symbols,  # Supply the available normalised historical symbols.
        "selected_symbol": selected_symbol,  # Supply the currently selected symbol.
        "historical_observations": historical_observations,  # Supply the stored observation count.
        "earliest_date": earliest_date,  # Supply the earliest historical date, or None.
        "latest_date": latest_date,  # Supply the latest historical date, or None.
        "latest_regime": latest_regime,  # Supply the latest stored analysis result.
        "market_interpretation": market_interpretation,  # Supply its plain-English explanation.
        "recent_regimes": recent_regimes,  # Supply up to ten recent results.
        "page_title": "Market Condition",  # Supply the user-facing page title.
        "technical_name": "Market Regime Analysis",  # Supply the technical feature name.
    }  # Finish the context dictionary.

    # --------------------------------------------------------
    # 2.10 RENDER THE DATA WORKSPACE TEMPLATE
    # --------------------------------------------------------
    return render(  # Return a response created from the template and context.
        request,  # Pass the current request to Django's rendering helper.
        "data_management/market_condition.html",  # Select the original Data template.
        context,  # Pass the prepared display values.
    )  # Finish the render call.

# ============================================================
# 3. MARKET CONDITION HISTORY VIEW
# ============================================================
@login_required  # Decorator: require authentication before showing history.
def market_condition_results(request):  # Function definition: handle the history-page request.
    """Display stored market-condition results in the Data workflow."""

    # --------------------------------------------------------
    # 3.1 READ THE OPTIONAL SYMBOL FILTER
    # --------------------------------------------------------
    selected_symbol = (  # Assignment: read and normalise the requested symbol.
        request.GET.get("symbol", "")  # Read the query parameter; default to an empty string if absent.
        .strip()  # Remove leading and trailing whitespace.
        .upper()  # Convert the symbol to uppercase.
    )  # Finish the normalisation expression.

    # --------------------------------------------------------
    # 3.2 PREPARE THE BASE RESULT QUERY
    # --------------------------------------------------------
    regimes = (  # Assignment: prepare a query for stored condition results.
        MarketRegime.objects  # Access the result model's database manager.
        .all()  # Include all results; this query does not filter by user.
        .order_by("-date", "-created_at")  # Order newest result date and creation time first.
    )  # Finish the base query.

    # --------------------------------------------------------
    # 3.3 APPLY THE OPTIONAL FILTER AND LIMIT
    # --------------------------------------------------------
    if selected_symbol:  # Conditional: apply filtering only when a symbol is present.
        regimes = regimes.filter(symbol=selected_symbol)  # Keep results matching the selected symbol.
    regimes = regimes[:50]  # Slicing: limit the result query to the first fifty records.

    # --------------------------------------------------------
    # 3.4 GET SYMBOLS WITH STORED ANALYSIS RESULTS
    # --------------------------------------------------------
    symbols = sorted(  # Function call: return the unique result symbols in sorted order.
        set(  # Set conversion: remove duplicate symbol values.
            MarketRegime.objects  # Access stored analysis results.
            .values_list("symbol", flat=True)  # Retrieve only their symbol values.
            .distinct()  # Request distinct values from the database.
        )  # Finish constructing the set; these symbols are not normalised here.
    )  # Finish constructing the sorted symbol list.

    # --------------------------------------------------------
    # 3.5 BUILD THE HISTORY TEMPLATE CONTEXT
    # --------------------------------------------------------
    context = {  # Dictionary: collect the history page's display values.
        "regimes": regimes,  # Supply the result query, limited to fifty records.
        "symbols": symbols,  # Supply symbols found in stored analysis results.
        "selected_symbol": selected_symbol,  # Supply the current optional filter.
        "page_title": "Market Condition History",  # Supply the user-facing heading.
        "technical_name": "Market Regime Analysis",  # Supply the technical feature name.
    }  # Finish the history context dictionary.

    # --------------------------------------------------------
    # 3.6 RENDER THE HISTORY PAGE
    # --------------------------------------------------------
    return render(  # Return the rendered history-page response.
        request,  # Pass the current HTTP request.
        "data_management/market_condition_results.html",  # Select the original history template.
        context,  # Pass the prepared history values.
    )  # Finish the render call.