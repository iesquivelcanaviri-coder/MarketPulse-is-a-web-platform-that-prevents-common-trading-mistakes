# ============================================================
# MARKET CONDITION / REGIME ANALYSIS IMPORTS
# ============================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.models import MarketData

from analysis_tools.analyzers import (
    identify_market_regime,
)

from analysis_tools.models import (
    MarketRegime,
)

# ============================================================
# MARKET CONDITION ANALYSIS
# ============================================================

@login_required
def market_condition(request):
    """
    ============================================================
    MARKET CONDITION / REGIME ANALYSIS
    ============================================================

    USER-FACING PURPOSE:

    Instead of asking the user to understand the technical
    phrase "Market Regime Analysis", MarketPulse asks a simpler
    question:

        "What type of market has this asset been experiencing?"

    The analysis can identify conditions such as:

    - Uptrend
    - Downtrend
    - Sideways market
    - High-volatility market
    - Low-volatility market

    Framework mapping:

    Data Tab
        ↓
    core.MarketData
        ↓
    analysis_tools.analyzers.identify_market_regime()
        ↓
    analysis_tools.models.MarketRegime
        ↓
    Market Condition Result

    IMPORTANT:

    analysis_tools remains the internal quantitative engine.

    The user accesses the feature from the Data tab instead
    of a separate Analysis tab.
    ============================================================
    """


    # ========================================================
    # 1. GET SYMBOLS WITH HISTORICAL DATA
    # ========================================================

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
    # Normalise symbols
    # --------------------------------------------------------

    symbols = sorted(

        {

            str(symbol)
            .strip()
            .upper()

            for symbol in stored_symbols_query

            if symbol

        }
    )


    # ========================================================
    # 2. DETERMINE SELECTED SYMBOL
    # ========================================================

    # Priority:
    #
    # 1. POSTed symbol
    # 2. URL query parameter
    # 3. First available historical symbol
    # 4. Blank

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
            symbols[0]
            if symbols
            else ""
        )
    )


    selected_symbol = (

        selected_symbol
        .strip()
        .upper()

        if selected_symbol

        else ""
    )


    # ========================================================
    # 3. PREPARE CURRENT HISTORICAL INFORMATION
    # ========================================================

    historical_observations = 0

    earliest_date = None

    latest_date = None


    if selected_symbol:

        selected_market_data = (

            MarketData.objects
            .filter(
                symbol=selected_symbol
            )
            .order_by(
                "date"
            )
        )


        historical_observations = (
            selected_market_data.count()
        )


        first_record = (
            selected_market_data.first()
        )


        latest_record = (
            selected_market_data.last()
        )


        if first_record:

            earliest_date = (
                first_record.date
            )


        if latest_record:

            latest_date = (
                latest_record.date
            )


    # ========================================================
    # 4. PROCESS ANALYSIS REQUEST
    # ========================================================

    if request.method == "POST":

        # ----------------------------------------------------
        # Symbol required
        # ----------------------------------------------------

        if not selected_symbol:

            messages.error(
                request,
                (
                    "Select an asset before running "
                    "Market Condition Analysis."
                ),
            )


        # ----------------------------------------------------
        # Require historical observations
        # ----------------------------------------------------

        elif historical_observations < 20:

            messages.error(
                request,
                (
                    f"{selected_symbol} currently has only "
                    f"{historical_observations} stored historical "
                    f"observations. More historical data is needed "
                    f"before MarketPulse can analyse the market "
                    f"condition reliably."
                ),
            )


        else:

            try:

                # ============================================
                # RUN EXISTING MARKET REGIME ENGINE
                # ============================================

                regime_result = (
                    identify_market_regime(
                        selected_symbol
                    )
                )


                # ============================================
                # SUCCESS
                # ============================================

                if regime_result:

                    messages.success(
                        request,
                        (
                            f"Market condition analysis for "
                            f"{selected_symbol} completed."
                        ),
                    )


                    return redirect(

                        "data_management:market_condition"

                        +
                        f"?symbol={selected_symbol}"
                    )


                # ============================================
                # ANALYZER RETURNED NO RESULT
                # ============================================

                messages.error(
                    request,
                    (
                        "MarketPulse could not determine a "
                        "market condition from the available "
                        "historical observations."
                    ),
                )


            except Exception as error:

                # ------------------------------------------------
                # Development-friendly error handling
                #
                # Instead of producing a Django 500 page, explain
                # the analytical failure in the Data interface.
                # ------------------------------------------------

                messages.error(
                    request,
                    (
                        "Market condition analysis could not "
                        f"be completed: {error}"
                    ),
                )


    # ========================================================
    # 5. GET LATEST MARKET CONDITION RESULT
    # ========================================================

    latest_regime = None


    if selected_symbol:

        latest_regime = (

            MarketRegime.objects
            .filter(
                symbol=selected_symbol
            )
            .order_by(
                "-date",
                "-created_at",
            )
            .first()
        )


    # ========================================================
    # 6. CREATE USER-FRIENDLY INTERPRETATION
    # ========================================================

    market_interpretation = None


    if latest_regime:

        regime_code = (
            latest_regime.regime
        )


        # ----------------------------------------------------
        # User-friendly explanations
        # ----------------------------------------------------

        interpretations = {

            "bull": (
                "Prices have generally been moving upward. "
                "This resembles an upward-trending market."
            ),

            "bear": (
                "Prices have generally been moving downward. "
                "This resembles a declining market environment."
            ),

            "sideways": (
                "Prices have not shown a strong sustained "
                "direction. The market appears relatively "
                "range-bound or sideways."
            ),

            "high_volatility": (
                "Recent price movements have been relatively "
                "large. This indicates a higher-volatility "
                "market environment."
            ),

            "low_volatility": (
                "Recent price movements have been relatively "
                "small. This indicates a lower-volatility "
                "market environment."
            ),
        }


        market_interpretation = (

            interpretations.get(
                regime_code
            )

            or

            (
                "MarketPulse identified this market condition "
                "from the available historical price behaviour."
            )
        )


    # ========================================================
    # 7. RECENT CONDITION HISTORY
    # ========================================================

    recent_regimes = []


    if selected_symbol:

        recent_regimes = (

            MarketRegime.objects
            .filter(
                symbol=selected_symbol
            )
            .order_by(
                "-date",
                "-created_at",
            )[:10]
        )


    # ========================================================
    # 8. TEMPLATE CONTEXT
    # ========================================================

    context = {

        # ----------------------------------------------------
        # Available historical symbols
        # ----------------------------------------------------

        "symbols":
            symbols,


        # ----------------------------------------------------
        # Current symbol
        # ----------------------------------------------------

        "selected_symbol":
            selected_symbol,


        # ----------------------------------------------------
        # Historical-data summary
        # ----------------------------------------------------

        "historical_observations":
            historical_observations,

        "earliest_date":
            earliest_date,

        "latest_date":
            latest_date,


        # ----------------------------------------------------
        # Latest analytical result
        # ----------------------------------------------------

        "latest_regime":
            latest_regime,


        # ----------------------------------------------------
        # Plain-English explanation
        # ----------------------------------------------------

        "market_interpretation":
            market_interpretation,


        # ----------------------------------------------------
        # Previous results
        # ----------------------------------------------------

        "recent_regimes":
            recent_regimes,


        # ----------------------------------------------------
        # User-facing terminology
        # ----------------------------------------------------

        "page_title":
            "Market Condition",

        "technical_name":
            "Market Regime Analysis",
    }


    # ========================================================
    # 9. RENDER MARKET CONDITION PAGE
    # ========================================================

    return render(

        request,

        "data_management/market_condition.html",

        context,
    )


# ============================================================
# MARKET CONDITION RESULT HISTORY
# ============================================================

@login_required
def market_condition_results(request):
    """
    ============================================================
    MARKET CONDITION HISTORY
    ============================================================

    Shows previously calculated market-condition results.

    This remains inside the Data workflow because market regime
    describes the characteristics of historical market data.
    ============================================================
    """


    # ========================================================
    # 1. OPTIONAL SYMBOL FILTER
    # ========================================================

    selected_symbol = (

        request.GET.get(
            "symbol",
            ""
        )
        .strip()
        .upper()
    )


    # ========================================================
    # 2. BASE QUERY
    # ========================================================

    regimes = (

        MarketRegime.objects
        .all()
        .order_by(
            "-date",
            "-created_at",
        )
    )


    # ========================================================
    # 3. FILTER TO ONE SYMBOL WHEN REQUESTED
    # ========================================================

    if selected_symbol:

        regimes = (
            regimes.filter(
                symbol=selected_symbol
            )
        )


    # ========================================================
    # 4. LIMIT RESULTS
    # ========================================================

    regimes = (
        regimes[:50]
    )


    # ========================================================
    # 5. AVAILABLE SYMBOLS
    # ========================================================

    symbols = sorted(

        set(

            MarketRegime.objects
            .values_list(
                "symbol",
                flat=True,
            )
            .distinct()
        )
    )


    # ========================================================
    # 6. TEMPLATE CONTEXT
    # ========================================================

    context = {

        "regimes":
            regimes,

        "symbols":
            symbols,

        "selected_symbol":
            selected_symbol,

        "page_title":
            "Market Condition History",

        "technical_name":
            "Market Regime Analysis",
    }


    # ========================================================
    # 7. RENDER
    # ========================================================

    return render(

        request,

        "data_management/market_condition_results.html",

        context,
    )