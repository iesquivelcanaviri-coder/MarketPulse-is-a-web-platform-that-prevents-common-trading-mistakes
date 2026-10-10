"""
============================================================
MARKETPULSE - INTERNAL ANALYTICS ENGINE
============================================================

This module contains the analytical logic used by different
parts of the MarketPulse application.

IMPORTANT ARCHITECTURE:

analysis_tools is no longer a user-facing navigation section.

Instead:

DATA TAB
    ↓
Market Condition
    ↓
identify_market_regime()


STRATEGIES TAB
    ↓
Strategy Robustness
    ↓
detect_overfitting()


RISK TAB
    ↓
Stress Testing
    ↓
run_stress_test()


The analysis_tools Django app remains installed because it
contains:

- analytical service functions
- database models
- historical analytical results
- migrations


The user does not need to understand this internal structure.
They interact with the analysis from the Data, Strategies
and Risk areas instead.

============================================================
EDUCATIONAL PURPOSE
============================================================

These methods are transparent educational quantitative
heuristics.

They are designed to demonstrate:

- historical data analysis
- strategy robustness testing
- market regime classification
- scenario-based stress testing

They are not intended to represent institutional trading,
risk-management or investment-advisory systems.
============================================================
"""

# ============================================================
# FILE PURPOSE / FRAMEWORK MAP
# ============================================================
#
# This file is the internal calculation layer of MarketPulse.
#
# Django page / view
#     ↓
# calls a function in this file
#     ↓
# Django ORM reads core.MarketData
#     ↓
# pandas + NumPy perform calculations
#     ↓
# Django ORM saves analytical results
#     ↓
# View reads result
#     ↓
# Template shows result to the user
#
# ============================================================
# PROGRAMMING LANGUAGE CONCEPTS USED IN THIS FILE
# ============================================================
#
# import          = reuse code from another module/library
# function        = reusable block of instructions
# parameter       = information passed into a function
# variable        = named value stored by the program
# list            = ordered collection of values
# tuple           = ordered collection normally kept together
# dictionary      = key/value collection
# if / elif / else = decision making
# for             = repetition / iteration
# try / except    = exception handling
# return          = sends a result back from a function
# method          = function attached to an object
# comparison      = >, <, >=, == and other Boolean tests
# arithmetic      = +, -, *, / and other calculations
# type conversion = converting values between Python types
# ORM             = Python objects used to communicate with
#                   the relational database
#
# These are examples of programming-language features:
# the building blocks used to construct a program.

# ============================================================
# 1. PYTHON IMPORTS
# ============================================================

from datetime import date, timedelta  # Imports date tools; timedelta lets the program add/subtract periods of time.
from decimal import Decimal  # Imports Decimal for safer fixed-point database values.

# ============================================================
# 2. THIRD-PARTY IMPORTS
# ============================================================

import numpy as np  # Imports NumPy and gives it the short name np for numerical calculations.
import pandas as pd  # Imports pandas and gives it the short name pd for table/time-series calculations.

# ============================================================
# 3. DJANGO / MARKETPULSE IMPORTS
# ============================================================

from core.models import MarketData  # Imports the Django model containing stored historical market observations.

from .models import (  # Imports models from this analysis_tools Django application.
    MarketRegime,  # Stores the calculated market-condition result.
    OverfittingTest,  # Stores strategy robustness / overfitting results.
    StressTest,  # Stores stress-testing results.
)

# ============================================================
# 4. DECIMAL CONVERSION HELPER
# ============================================================

def to_decimal(value):  # Defines a reusable helper function and receives value as its parameter.
    """
    Convert Python / NumPy numeric values into Decimal values.

    Django DecimalField values should not normally be created
    directly from floating-point numbers because binary
    floating-point representation can introduce small
    precision differences.

    Converting through str() makes the value safer and easier
    to understand.
    """
    return Decimal(  # return sends the converted Decimal back to the code that called this function.
        str(value)  # str() first converts the numeric value into text.
    )

# ============================================================
# 5. MARKET DATAFRAME HELPER
# ============================================================

def _frame(  # Defines a private helper used to load market data into pandas.
    symbol,  # Parameter containing the market ticker such as SPY.
    start_date,  # Parameter containing the first requested date.
    end_date,  # Parameter containing the last requested date.
):
    """
    Retrieve historical OHLCV data from core.MarketData and
    return it as a pandas DataFrame.

    Framework mapping:

    PostgreSQL
        ↓
    core.MarketData
        ↓
    Django ORM
        ↓
    pandas DataFrame
        ↓
    MarketPulse analytics
    """

    # --------------------------------------------------------
    # 5.1 NORMALISE SYMBOL
    # Programming concept: strings + method chaining
    # --------------------------------------------------------

    symbol = (  # Reassigns a cleaned version of symbol back into the variable.
        symbol  # Starts with the symbol supplied to the function.
        .strip()  # Removes spaces from the beginning and end.
        .upper()  # Converts the ticker to uppercase.
    )

    # --------------------------------------------------------
    # 5.2 READ HISTORICAL OBSERVATIONS
    # Programming concept: ORM + objects + method chaining
    # --------------------------------------------------------

    rows = list(  # list() converts the QuerySet values into a normal Python list.
        MarketData.objects  # objects is Django's model manager used to query the database.
        .filter(  # filter() selects database rows matching these conditions.
            symbol=symbol,  # Keeps records for the selected ticker.
            date__gte=start_date,  # __gte means date must be greater than or equal to start_date.
            date__lte=end_date,  # __lte means date must be less than or equal to end_date.
        )
        .order_by("date")  # Sorts observations from oldest to newest.
        .values(  # Returns selected model fields instead of complete Django model objects.
            "date",  # Requests the observation date.
            "open_price",  # Requests the opening price.
            "high_price",  # Requests the highest price.
            "low_price",  # Requests the lowest price.
            "close_price",  # Requests the closing price.
            "volume",  # Requests trading volume.
        )
    )

    # --------------------------------------------------------
    # 5.3 HANDLE MISSING DATA
    # Programming concept: conditional statement
    # --------------------------------------------------------

    if not rows:  # Checks whether the list contains no market-data records.
        return pd.DataFrame()  # Returns an empty pandas DataFrame immediately.

    # --------------------------------------------------------
    # 5.4 CONVERT DATABASE RECORDS INTO PANDAS
    # Programming concept: object construction
    # --------------------------------------------------------

    dataframe = pd.DataFrame(  # Creates a pandas DataFrame object.
        rows  # Uses the database rows as the DataFrame's source data.
    )

    # --------------------------------------------------------
    # 5.5 PRICE COLUMNS
    # Programming concept: list
    # --------------------------------------------------------

    price_columns = [  # Creates a Python list containing the price-column names.
        "open_price",  # First string item in the list.
        "high_price",  # Second string item in the list.
        "low_price",  # Third string item in the list.
        "close_price",  # Fourth string item in the list.
    ]

    # --------------------------------------------------------
    # 5.6 CONVERT PRICE TYPES
    # Programming concept: for loop / iteration
    # --------------------------------------------------------

    for column in price_columns:  # Repeats the following operation once for every price-column name.
        dataframe[column] = (  # Replaces this DataFrame column with its converted version.
            dataframe[column]  # Selects the current column.
            .astype(float)  # Converts its values into Python-compatible floating-point numbers.
        )

    # --------------------------------------------------------
    # 5.7 CONVERT VOLUME TYPE
    # Programming concept: numeric conversion
    # --------------------------------------------------------

    dataframe["volume"] = (  # Reassigns the cleaned numeric volume column.
        pd.to_numeric(  # Attempts to convert each volume value into a numeric value.
            dataframe["volume"],  # Supplies the volume column.
            errors="coerce",  # Invalid values become NaN instead of raising an error.
        )
        .fillna(0)  # Replaces missing numeric values with zero.
    )

    # --------------------------------------------------------
    # 5.8 RETURN DATA
    # Programming concept: return value
    # --------------------------------------------------------

    return dataframe  # Sends the completed DataFrame back to the calling function.

# ============================================================
# 6. GET LATEST STORED MARKET DATE
# ============================================================

def _latest_market_date(  # Defines a helper for finding the newest stored observation.
    symbol,  # Receives the ticker symbol.
):
    """
    Return the most recent MarketData date stored for a symbol.

    This is preferable to blindly assuming that MarketPulse
    contains data for today's calendar date.
    """

    symbol = (  # Cleans and normalises the supplied ticker.
        symbol  # Uses the original symbol value.
        .strip()  # Removes unnecessary outer spaces.
        .upper()  # Converts the symbol to uppercase.
    )

    return (  # Returns the result of the Django database query.
        MarketData.objects  # Accesses the MarketData model manager.
        .filter(  # Filters records by ticker symbol.
            symbol=symbol  # Requires the database symbol to match this symbol.
        )
        .order_by(  # Orders the matching rows.
            "-date"  # The minus sign means newest dates first.
        )
        .values_list(  # Requests values instead of complete model instances.
            "date",  # Requests only the date field.
            flat=True,  # Returns simple date values instead of one-item tuples.
        )
        .first()  # Returns the first/newest date or None if nothing exists.
    )

# ============================================================
# 7. STRATEGY PARAMETER HELPER
# ============================================================

def _strategy_parameters(  # Defines a helper that extracts strategy configuration values.
    strategy,  # Receives a Django Strategy object.
):
    """
    Extract moving-average parameters from the first active
    StrategyRule.

    MarketPulse's current educational Strategy Builder is
    based primarily on moving-average crossover rules.

    Defaults are supplied so the analysis remains stable if
    a rule does not contain explicit parameter values.
    """

    # --------------------------------------------------------
    # 7.1 FIND ACTIVE RULE
    # Programming concept: object relationship + ORM
    # --------------------------------------------------------

    rule = (  # Stores the first active StrategyRule.
        strategy.rules  # Accesses rules related to this strategy.
        .filter(  # Filters related rules.
            is_active=True  # Keeps only active rules.
        )
        .first()  # Returns the first matching rule or None.
    )

    # --------------------------------------------------------
    # 7.2 FALLBACK RULE
    # Programming concept: if statement
    # --------------------------------------------------------

    if rule is None:  # Tests whether no active rule was found.
        rule = (  # Tries to use any available rule instead.
            strategy.rules  # Accesses the strategy's related rules.
            .first()  # Returns the first available rule.
        )

    # --------------------------------------------------------
    # 7.3 PARAMETERS DICTIONARY
    # Programming concept: conditional expression
    # --------------------------------------------------------

    parameters = (  # Creates the parameters variable.
        rule.parameters  # Uses the rule's dictionary when a rule exists.
        if rule  # Tests whether rule has a value.
        else {}  # Otherwise uses an empty Python dictionary.
    )

    # --------------------------------------------------------
    # 7.4 FAST PERIOD
    # Programming concept: exception handling + type casting
    # --------------------------------------------------------

    try:  # Starts code that may raise a conversion error.
        fast_period = int(  # Converts the retrieved value into an integer.
            parameters.get(  # Gets a value from the dictionary.
                "fast_period",  # Dictionary key being requested.
                10,  # Default value if the key does not exist.
            )
        )
    except (  # Handles specific errors without crashing the analysis.
        TypeError,  # Handles incompatible Python object types.
        ValueError,  # Handles values that cannot be converted to int.
    ):
        fast_period = 10  # Uses the safe default after an invalid value.

    # --------------------------------------------------------
    # 7.5 SLOW PERIOD
    # Programming concept: exception handling + type casting
    # --------------------------------------------------------

    try:  # Starts another protected conversion.
        slow_period = int(  # Converts the slow period into an integer.
            parameters.get(  # Reads from the parameters dictionary.
                "slow_period",  # Requests the slow_period key.
                30,  # Uses 30 if the value is missing.
            )
        )
    except (  # Catches conversion failures.
        TypeError,  # Handles an invalid object type.
        ValueError,  # Handles invalid numeric text/value.
    ):
        slow_period = 30  # Uses the fallback value.

    # --------------------------------------------------------
    # 7.6 DEFENSIVE VALIDATION
    # Programming concept: built-in functions + constraints
    # --------------------------------------------------------

    fast_period = max(  # max() makes sure the fast period cannot be below 2.
        2,  # Minimum permitted value.
        fast_period,  # User/rule value being checked.
    )

    slow_period = max(  # Ensures the slow period remains longer than the fast period.
        fast_period + 1,  # Minimum valid slow period.
        slow_period,  # Existing slow-period value.
    )

    # --------------------------------------------------------
    # 7.7 RETURN MULTIPLE VALUES
    # Programming concept: tuple
    # --------------------------------------------------------

    return (  # Returns two related values as a tuple.
        fast_period,  # First tuple value.
        slow_period,  # Second tuple value.
    )

# ============================================================
# 8. MOVING-AVERAGE STRATEGY RETURN
# ============================================================

def _ma_return(  # Defines a helper that calculates the MA strategy's cumulative return.
    dataframe,  # Receives historical market data.
    fast_period=10,  # Optional parameter with default value 10.
    slow_period=30,  # Optional parameter with default value 30.
):
    """
    Calculate a simplified long-only moving-average strategy
    return.

    Logic:

    Fast MA > Slow MA
        ↓
    Position = 1

    Otherwise
        ↓
    Position = 0

    The signal is shifted by one observation so the strategy
    does not use the same period's closing price to create
    and execute a signal simultaneously.

    This reduces look-ahead bias in the educational model.
    """

    # --------------------------------------------------------
    # 8.1 DEFENSIVE DATA CHECKS
    # --------------------------------------------------------

    if dataframe.empty:  # Tests whether the pandas DataFrame contains no rows.
        return 0.0  # Returns a floating-point zero because no return can be calculated.

    if len(dataframe) < (  # Tests whether there are enough observations.
        slow_period + 2  # Requires slightly more rows than the slow moving-average length.
    ):
        return 0.0  # Returns zero when there is insufficient history.

    # --------------------------------------------------------
    # 8.2 CLOSE PRICE SERIES
    # --------------------------------------------------------

    close = (  # Creates a variable containing close prices.
        dataframe["close_price"]  # Selects the close_price Series.
        .astype(float)  # Makes sure the values are floats.
    )

    # --------------------------------------------------------
    # 8.3 FAST MOVING AVERAGE
    # --------------------------------------------------------

    fast_ma = (  # Stores the fast moving-average Series.
        close  # Starts with closing prices.
        .rolling(  # Creates a rolling calculation window.
            fast_period  # Uses the strategy's fast-period length.
        )
        .mean()  # Calculates the arithmetic mean inside each rolling window.
    )

    # --------------------------------------------------------
    # 8.4 SLOW MOVING AVERAGE
    # --------------------------------------------------------

    slow_ma = (  # Stores the slow moving-average Series.
        close  # Starts with closing prices.
        .rolling(  # Creates another rolling calculation window.
            slow_period  # Uses the longer slow-period length.
        )
        .mean()  # Calculates the rolling average.
    )

    # --------------------------------------------------------
    # 8.5 TRADING SIGNAL
    # Programming concept: comparison + Boolean conversion
    # --------------------------------------------------------

    signal = (  # Stores the strategy's 1/0 market-position signal.
        fast_ma  # Left side of comparison.
        >
        slow_ma  # Right side of comparison.
    ).astype(int)  # Converts True/False into 1/0 integers.

    # --------------------------------------------------------
    # 8.6 MARKET RETURNS
    # --------------------------------------------------------

    asset_returns = (  # Stores daily fractional price changes.
        close  # Uses close-price data.
        .pct_change()  # Calculates change relative to the preceding observation.
        .fillna(0)  # Replaces the first missing return with zero.
    )

    # --------------------------------------------------------
    # 8.7 STRATEGY RETURNS
    # --------------------------------------------------------

    strategy_returns = (  # Stores returns earned only while the signal is active.
        asset_returns  # Starts with market returns.
        *
        signal  # Uses the trading signal.
        .shift(1)  # Moves the signal one period forward to reduce look-ahead bias.
        .fillna(0)  # Replaces the newly created first missing signal with zero.
    )

    # --------------------------------------------------------
    # 8.8 CUMULATIVE RETURN
    # --------------------------------------------------------

    cumulative_return = (  # Stores total compounded strategy return.
        (
            1  # Represents the original capital base.
            +
            strategy_returns  # Converts each return into a growth multiplier.
        )
        .prod()  # Multiplies all growth multipliers together.
        -
        1  # Converts the final growth factor back into a return.
    )

    # --------------------------------------------------------
    # 8.9 RETURN RESULT
    # --------------------------------------------------------

    return float(  # Converts the result to a normal Python float.
        cumulative_return  # Value being returned.
    )

# ============================================================
# 9. STRATEGY EQUITY CURVE
# ============================================================

def _strategy_equity_curve(  # Defines a helper that builds the strategy's value through time.
    dataframe,  # Receives historical market observations.
    strategy,  # Receives the Django Strategy object.
):
    """
    Build an educational strategy equity curve using the
    strategy's moving-average parameters.

    This is useful for scenario stress testing because the
    test should examine strategy behaviour rather than only
    the raw market price.
    """

    if dataframe.empty:  # Stops the calculation when no data exists.
        return pd.Series(  # Returns an empty pandas Series.
            dtype=float  # Sets its expected value type to float.
        )

    fast_period, slow_period = (  # Tuple unpacking stores the two returned values separately.
        _strategy_parameters(  # Calls the strategy-parameter helper.
            strategy  # Supplies the current strategy.
        )
    )

    if len(dataframe) < (  # Checks whether enough data exists for the slow average.
        slow_period + 2  # Defines the required minimum number of observations.
    ):
        return pd.Series(  # Returns an empty Series when data is insufficient.
            dtype=float  # Sets the Series numeric type.
        )

    close = (  # Stores closing prices.
        dataframe["close_price"]  # Selects the close-price column.
        .astype(float)  # Converts values into floats.
    )

    fast_ma = (  # Calculates the fast moving average.
        close  # Uses closing prices.
        .rolling(  # Creates the rolling window.
            fast_period  # Sets the fast window length.
        )
        .mean()  # Calculates each window's mean.
    )

    slow_ma = (  # Calculates the slow moving average.
        close  # Uses the same closing prices.
        .rolling(  # Creates the longer rolling window.
            slow_period  # Sets the slow window length.
        )
        .mean()  # Calculates the window mean.
    )

    signal = (  # Creates the long-only trading signal.
        fast_ma  # Fast moving average.
        >
        slow_ma  # Slow moving average.
    ).astype(int)  # Converts Boolean results to integer 1 or 0.

    returns = (  # Calculates asset returns.
        close  # Starts with close prices.
        .pct_change()  # Calculates fractional changes.
        .fillna(0)  # Replaces the initial NaN with zero.
    )

    strategy_returns = (  # Calculates returns produced by the strategy signal.
        returns  # Uses market returns.
        *
        signal  # Uses the position signal.
        .shift(1)  # Delays the signal by one observation.
        .fillna(0)  # Replaces the first missing signal with zero.
    )

    equity_curve = (  # Builds the cumulative strategy value.
        1  # Starting growth factor.
        +
        strategy_returns  # Adds each strategy return to 1.
    ).cumprod()  # Cumulatively multiplies the growth factors.

    return equity_curve  # Sends the complete pandas Series back to the caller.

# ============================================================
# 10. STRATEGY ROBUSTNESS / OVERFITTING ANALYSIS
# ============================================================

def detect_overfitting(  # Defines the main educational strategy-robustness function.
    strategy,  # Receives the Strategy model object.
    symbol,  # Receives the ticker symbol.
    periods,  # Receives historical periods to test.
):
    """
    ============================================================
    STRATEGY ROBUSTNESS CHECK
    ============================================================

    User-facing location:

        STRATEGIES
            ↓
        Strategy Robustness


    Technical method:

        Overfitting Analysis


    PURPOSE:

    Compare performance inside one section of historical data
    with performance in a later unseen section.

    Each supplied period is divided approximately:

        70% in-sample
        30% out-of-sample


    A large deterioration between the two sections increases
    the overfitting score.

    IMPORTANT:

    This is an educational robustness heuristic and not a
    replacement for professional walk-forward analysis,
    purged cross-validation or advanced model-validation
    techniques.
    ============================================================
    """

    # ========================================================
    # 10.1 NORMALISE INPUT
    # Programming concept: string methods
    # ========================================================

    symbol = (  # Replaces symbol with a clean normalised version.
        symbol  # Uses the supplied ticker.
        .strip()  # Removes outer whitespace.
        .upper()  # Converts the ticker to uppercase.
    )

    # ========================================================
    # 10.2 READ STRATEGY PARAMETERS
    # Programming concept: function call + tuple unpacking
    # ========================================================

    fast_period, slow_period = (  # Stores both parameter values returned by the helper.
        _strategy_parameters(  # Calls the helper function.
            strategy  # Passes the Strategy object.
        )
    )

    # ========================================================
    # 10.3 RESULT COLLECTION
    # Programming concept: list
    # ========================================================

    created_tests = []  # Creates an empty list that will collect saved OverfittingTest objects.

    # ========================================================
    # 10.4 LOOP THROUGH TEST PERIODS
    # Programming concept: loop + tuple unpacking
    # ========================================================

    for (  # Repeats the robustness calculation for every supplied date period.
        period_start,  # Receives the first tuple value.
        period_end,  # Receives the second tuple value.
    ) in periods:  # Iterates through the periods collection.

        # ====================================================
        # 10.5 VALIDATE PERIOD
        # ====================================================

        total_days = (  # Calculates the length of the requested historical period.
            period_end  # End date.
            -
            period_start  # Start date.
        ).days  # Extracts the number of calendar days from the timedelta.

        if total_days <= 0:  # Rejects zero-length or backwards periods.
            continue  # Skips directly to the next loop iteration.

        # ====================================================
        # 10.6 70 / 30 SPLIT
        # ====================================================

        split_days = int(  # Converts the calculated split into a whole number of days.
            total_days  # Uses total historical days.
            *
            0.70  # Allocates approximately 70% to in-sample testing.
        )

        split_date = (  # Calculates the final in-sample date.
            period_start  # Starts from the period's first date.
            +
            timedelta(  # Creates a duration to add to the date.
                days=split_days  # Uses the calculated 70% number of days.
            )
        )

        out_sample_start = (  # Calculates the first out-of-sample date.
            split_date  # Starts from the split boundary.
            +
            timedelta(  # Creates another one-day time duration.
                days=1  # Moves one calendar day after the in-sample section.
            )
        )

        # ====================================================
        # 10.7 LOAD BOTH DATA WINDOWS
        # Programming concept: function reuse
        # ====================================================

        in_sample_data = _frame(  # Loads the first historical data section.
            symbol,  # Supplies the ticker.
            period_start,  # Supplies its beginning date.
            split_date,  # Supplies its final date.
        )

        out_sample_data = _frame(  # Loads the later unseen historical data section.
            symbol,  # Supplies the ticker.
            out_sample_start,  # Supplies the beginning date.
            period_end,  # Supplies the end date.
        )

        # ====================================================
        # 10.8 STRATEGY RETURNS
        # ====================================================

        in_sample_return = (  # Stores return calculated on the first data section.
            _ma_return(  # Calls the moving-average return helper.
                in_sample_data,  # Supplies in-sample observations.
                fast_period,  # Supplies the fast moving-average length.
                slow_period,  # Supplies the slow moving-average length.
            )
        )

        out_sample_return = (  # Stores return calculated on unseen data.
            _ma_return(  # Calls the same function so both periods use the same rules.
                out_sample_data,  # Supplies out-of-sample observations.
                fast_period,  # Uses the same fast period.
                slow_period,  # Uses the same slow period.
            )
        )

        # ====================================================
        # 10.9 OVERFITTING SCORE
        # Programming concept: comparison + branching
        # ====================================================

        # We only assign deterioration when the in-sample
        # performance is stronger than the out-of-sample
        # performance.

        if (  # Tests whether performance became worse on unseen data.
            in_sample_return  # First-period result.
            >
            out_sample_return  # Later-period result.
        ):
            denominator = max(  # Creates a safe denominator and avoids very small divisors.
                abs(  # Converts a negative value into its positive magnitude.
                    in_sample_return  # Value whose magnitude is required.
                ),
                0.01,  # Minimum denominator allowed by this heuristic.
            )

            deterioration = (  # Measures relative deterioration between both results.
                in_sample_return  # Original in-sample result.
                -
                out_sample_return  # Subtracts later unseen-data result.
            ) / denominator  # Divides by the safe reference value.

            overfitting_score = max(  # Prevents a result below zero.
                0.0,  # Minimum allowed score.
                min(  # Prevents a score above one.
                    1.0,  # Maximum allowed score.
                    deterioration,  # Raw calculated deterioration.
                ),
            )
        else:  # Runs when unseen-data performance did not deteriorate.
            overfitting_score = 0.0  # Assigns zero deterioration.

        # ====================================================
        # 10.10 CLASSIFICATION
        # Programming concept: Boolean expression
        # ====================================================

        is_overfitted = (  # Stores either True or False.
            overfitting_score  # Uses the calculated score.
            >
            0.30  # Classifies scores above 30% as overfitted.
        )

        # ====================================================
        # 10.11 PLAIN-LANGUAGE INTERPRETATION
        # ====================================================

        if is_overfitted:  # Selects the warning message when classification is True.
            recommendation = (  # Stores text explaining the result.
                "Large out-of-sample deterioration was detected. "
                "Consider simplifying the strategy rules, reducing "
                "parameter tuning and testing on additional unseen "
                "historical periods."
            )
        else:  # Selects the alternative interpretation.
            recommendation = (  # Stores text for a more stable result.
                "Performance was reasonably stable across this "
                "historical test window. Continue testing across "
                "additional periods and market conditions."
            )

        # ====================================================
        # 10.12 SAVE RESULT
        # Programming concept: Django ORM object creation
        # ====================================================

        test = (  # Stores the newly created OverfittingTest Django object.
            OverfittingTest.objects  # Uses the model's ORM manager.
            .create(  # Creates and saves a new database row.
                user=
                    strategy.user,  # Associates the result with the strategy owner.
                strategy=
                    strategy,  # Stores the tested Strategy relationship.
                symbol=
                    symbol,  # Stores the normalised ticker.
                test_period=
                    (
                        f"{period_start} "  # f-string inserts the first date into text.
                        f"to "
                        f"{period_end}"  # f-string inserts the final date.
                    ),
                in_sample_return=
                    to_decimal(  # Converts the float into Decimal.
                        in_sample_return  # Supplies the calculated in-sample return.
                    ),
                out_sample_return=
                    to_decimal(  # Converts the second float into Decimal.
                        out_sample_return  # Supplies the calculated out-of-sample return.
                    ),
                overfitting_score=
                    to_decimal(  # Converts the robustness score for DecimalField storage.
                        overfitting_score  # Supplies the calculated score.
                    ),
                is_overfitted=
                    is_overfitted,  # Stores the Boolean classification.
                recommendations=
                    recommendation,  # Stores the explanatory message.
            )
        )

        created_tests.append(  # Calls the Python list append method.
            test  # Adds the saved Django object to the result list.
        )

    # ========================================================
    # 10.13 RETURN ALL CREATED TESTS
    # ========================================================

    return created_tests  # Returns the list of database objects created by the function.

# ============================================================
# 11. MARKET CONDITION / REGIME ANALYSIS
# ============================================================

def identify_market_regime(  # Defines the market-condition classification function.
    symbol,  # Receives the ticker to analyse.
):
    """
    ============================================================
    MARKET CONDITION ANALYSIS
    ============================================================

    User-facing location:

        DATA
            ↓
        Market Condition


    Technical method:

        Market Regime Analysis


    MarketPulse considers:

    - recent close prices
    - 20-day moving average
    - 60-day moving average
    - annualised historical volatility
    - trend strength


    Possible conditions:

    bull
        Rising market trend

    bear
        Falling market trend

    sideways
        No strong directional trend

    volatile
        Unusually high historical volatility


    The function uses update_or_create() because MarketRegime
    has one result per symbol/date. This means the user can
    safely rerun today's analysis without causing a database
    uniqueness error.
    ============================================================
    """

    # ========================================================
    # 11.1 NORMALISE SYMBOL
    # ========================================================

    symbol = (  # Stores the cleaned ticker.
        symbol  # Starts with supplied text.
        .strip()  # Removes surrounding spaces.
        .upper()  # Converts it to uppercase.
    )

    # ========================================================
    # 11.2 GET MOST RECENT STORED MARKET DATE
    # ========================================================

    latest_date = (  # Stores the most recent available date.
        _latest_market_date(  # Calls the helper defined earlier.
            symbol  # Supplies the ticker.
        )
    )

    if latest_date is None:  # Tests whether the database contained no observations.
        return None  # Ends the function without a market-regime result.

    # ========================================================
    # 11.3 LOAD APPROXIMATELY 300 CALENDAR DAYS
    # ========================================================

    start_date = (  # Calculates the beginning of the analysis window.
        latest_date  # Uses the newest stored market date.
        -
        timedelta(  # Creates a time difference.
            days=300  # Goes backwards approximately 300 calendar days.
        )
    )

    dataframe = _frame(  # Loads the historical observations into pandas.
        symbol,  # Supplies the ticker.
        start_date,  # Supplies the beginning date.
        latest_date,  # Supplies the ending date.
    )

    # At least 60 observations are needed because the
    # classifier uses a 60-period moving average.

    if len(dataframe) < 60:  # Checks whether at least 60 observations exist.
        return None  # Stops because the slow moving average cannot be calculated reliably.

    # ========================================================
    # 11.4 PRICE SERIES
    # ========================================================

    close = (  # Creates the closing-price Series.
        dataframe[  # Accesses the pandas DataFrame.
            "close_price"  # Selects its close_price column.
        ]
        .astype(float)  # Converts values to floats for calculations.
    )

    # ========================================================
    # 11.5 ANNUALISED VOLATILITY
    # ========================================================

    daily_returns = (  # Calculates a Series of daily market returns.
        close  # Uses closing prices.
        .pct_change()  # Calculates fractional change from one observation to the next.
        .dropna()  # Removes missing values generated by the first observation.
    )

    if daily_returns.empty:  # Checks whether any usable returns remain.
        return None  # Stops if volatility cannot be calculated.

    volatility = float(  # Converts the NumPy/pandas result to a standard Python float.
        daily_returns.std()  # Calculates standard deviation of daily returns.
        *
        np.sqrt(252)  # Multiplies by square root of 252 to annualise daily volatility.
    )

    # ========================================================
    # 11.6 MOVING AVERAGES
    # ========================================================

    ma_20 = float(  # Stores the latest 20-observation moving-average value.
        close  # Uses the close-price Series.
        .rolling(20)  # Creates a rolling 20-observation window.
        .mean()  # Calculates the average for each window.
        .iloc[-1]  # Selects the final/latest calculated value.
    )

    ma_60 = float(  # Stores the latest 60-observation moving-average value.
        close  # Uses the same closing-price Series.
        .rolling(60)  # Creates a 60-observation window.
        .mean()  # Calculates its mean.
        .iloc[-1]  # Selects the latest value.
    )

    current_price = float(  # Converts the latest closing price to a normal float.
        close.iloc[-1]  # iloc[-1] selects the final Series element.
    )

    # ========================================================
    # 11.7 TREND STRENGTH
    # Programming concept: conditional branch
    # ========================================================

    if ma_60:  # Tests whether the slow moving average is non-zero.
        trend_strength = (  # Calculates the difference between both moving averages.
            ma_20  # Shorter-term moving average.
            /
            ma_60  # Longer-term moving average.
            -
            1  # Converts the ratio into relative difference.
        )
    else:  # Protects against division by zero.
        trend_strength = 0.0  # Uses a neutral trend value.

    # ========================================================
    # 11.8 REGIME CLASSIFICATION
    # Programming concept: if / elif / else decision tree
    # ========================================================

    if volatility > 0.40:  # Gives high volatility the first classification priority.
        regime = "volatile"  # Stores the volatile regime label.
    elif (  # Tests for a bullish moving-average structure.
        current_price  # Latest market price.
        >
        ma_20  # Must be above the 20-period moving average.
        >
        ma_60  # The 20-period average must also be above the 60-period average.
        and  # Both sides of this condition must be True.
        trend_strength  # Uses measured moving-average separation.
        >
        0.01  # Requires more than 1% positive trend strength.
    ):
        regime = "bull"  # Stores the bullish regime label.
    elif (  # Tests for the opposite bearish structure.
        current_price  # Latest close price.
        <
        ma_20  # Must be below the 20-period moving average.
        <
        ma_60  # The 20-period average must be below the 60-period average.
        and  # Requires the additional trend-strength condition.
        trend_strength  # Uses calculated relative trend.
        <
        -0.01  # Requires less than -1% trend strength.
    ):
        regime = "bear"  # Stores the bearish regime label.
    else:  # Runs when none of the previous classifications apply.
        regime = "sideways"  # Treats the condition as lacking a strong directional trend.

    # ========================================================
    # 11.9 CONFIDENCE SCORE
    # ========================================================

    trend_component = (  # Converts trend strength into part of the confidence score.
        abs(  # Uses magnitude regardless of bullish/bearish direction.
            trend_strength  # Supplies the trend value.
        )
        *
        10  # Scales the trend magnitude.
    )

    volatility_component = min(  # Caps the volatility contribution.
        volatility,  # Uses annualised historical volatility.
        0.50,  # Maximum volatility contribution permitted here.
    )

    confidence = min(  # Ensures final confidence cannot exceed 1.
        1.0,  # Maximum score.
        trend_component  # Adds trend information.
        +
        volatility_component,  # Adds volatility information.
    )

    # ========================================================
    # 11.10 SAVE OR UPDATE RESULT
    # Programming concept: ORM + tuple unpacking + dictionary
    # ========================================================

    market_regime, created = (  # update_or_create returns the object plus a created Boolean.
        MarketRegime.objects  # Accesses the MarketRegime ORM manager.
        .update_or_create(  # Updates an existing matching row or creates a new row.
            symbol=
                symbol,  # Uses symbol as part of the lookup.
            date=
                latest_date,  # Uses market date as part of the lookup.
            defaults={  # Dictionary contains fields to create/update.
                "regime":
                    regime,  # Saves the calculated regime label.
                "confidence":
                    to_decimal(  # Converts the float for DecimalField storage.
                        confidence  # Supplies calculated confidence.
                    ),
                "volatility":
                    to_decimal(  # Converts annualised volatility.
                        volatility  # Supplies the calculated volatility.
                    ),
                "trend_strength":
                    to_decimal(  # Converts relative trend strength.
                        trend_strength  # Supplies calculated trend strength.
                    ),
            },
        )
    )

    return market_regime  # Returns the saved or updated Django model object.

# ============================================================
# 12. CRASH STRESS-SCENARIO HELPER
# ============================================================

def _apply_crash_scenario(  # Defines a helper that modifies data to simulate a market crash.
    dataframe,  # Receives historical market data.
    parameters,  # Receives scenario settings in a dictionary.
):
    """
    Simulate a sudden downward price shock.
    """

    dataframe = (  # Reassigns dataframe to an independent copy.
        dataframe.copy()  # copy() prevents modification of the original DataFrame.
    )

    number_of_rows = len(  # Counts observations in the DataFrame.
        dataframe  # Object whose rows are counted.
    )

    crash_start = float(  # Converts the configured starting point into a float.
        parameters.get(  # Reads from the scenario parameter dictionary.
            "crash_start",  # Key being requested.
            0.70,  # Default means begin 70% through the data.
        )
    )

    crash_magnitude = float(  # Converts crash magnitude into a float.
        parameters.get(  # Reads another scenario setting.
            "crash_magnitude",  # Requests the loss magnitude.
            0.20,  # Defaults to a 20% price shock.
        )
    )

    crash_start = max(  # Enforces the lower boundary.
        0.0,  # Minimum allowed start proportion.
        min(  # Enforces the upper boundary.
            1.0,  # Maximum allowed proportion.
            crash_start,  # Original configured start value.
        ),
    )

    crash_magnitude = max(  # Prevents negative crash magnitudes.
        0.0,  # Minimum magnitude.
        min(  # Caps excessively large values.
            0.95,  # Maximum permitted crash magnitude.
            crash_magnitude,  # Configured magnitude.
        ),
    )

    start_index = int(  # Converts the calculated starting row into an integer.
        number_of_rows  # Number of observations.
        *
        crash_start  # Proportion at which the crash starts.
    )

    price_columns = [  # Creates a list of all OHLC price columns.
        "open_price",  # Opening price.
        "high_price",  # High price.
        "low_price",  # Low price.
        "close_price",  # Closing price.
    ]

    dataframe.loc[  # Uses label-based pandas selection to change part of the table.
        start_index:,  # Selects rows from the crash point onward.
        price_columns,  # Selects all four price columns.
    ] *= (  # Multiplies the selected values in place.
        1  # Starts with the full original price.
        -
        crash_magnitude  # Removes the configured crash percentage.
    )

    return dataframe  # Returns the stressed copy of the historical data.

# ============================================================
# 13. VOLATILITY SPIKE SCENARIO
# ============================================================

def _apply_volatility_spike(  # Defines a helper for injecting temporary random price shocks.
    dataframe,  # Receives the historical DataFrame.
    parameters,  # Receives scenario settings.
):
    """
    Simulate a temporary period of substantially higher
    price volatility.

    A fixed random seed is used so repeated educational tests
    are reproducible.
    """

    dataframe = (  # Creates an independent DataFrame.
        dataframe.copy()  # Prevents changes to original historical data.
    )

    number_of_rows = len(  # Counts available observations.
        dataframe  # Supplies the DataFrame to len().
    )

    spike_start = float(  # Converts the configured start proportion to float.
        parameters.get(  # Reads a dictionary value.
            "spike_start",  # Requests the scenario start.
            0.50,  # Defaults to halfway through the sample.
        )
    )

    spike_duration = float(  # Converts duration to float.
        parameters.get(  # Reads the duration parameter.
            "spike_duration",  # Dictionary key.
            0.10,  # Defaults to 10% of available observations.
        )
    )

    spike_magnitude = float(  # Converts shock multiplier to float.
        parameters.get(  # Reads the scenario setting.
            "spike_magnitude",  # Requests volatility multiplier.
            3.0,  # Defaults to three times normal volatility.
        )
    )

    start_index = int(  # Converts the selected start row into an integer.
        number_of_rows  # Uses number of historical observations.
        *
        max(  # Prevents a value below zero.
            0.0,  # Minimum start fraction.
            min(  # Prevents a value above one.
                1.0,  # Maximum start fraction.
                spike_start,  # Configured start value.
            ),
        )
    )

    duration = max(  # Guarantees at least one row is affected.
        1,  # Minimum duration.
        int(  # Converts row count into an integer.
            number_of_rows  # Uses total observations.
            *
            max(  # Provides a minimum percentage.
                0.01,  # At least one percent of the sample.
                min(  # Provides an upper bound.
                    1.0,  # At most the entire sample.
                    spike_duration,  # Configured duration proportion.
                ),
            )
        ),
    )

    historical_volatility = (  # Calculates ordinary historical return volatility.
        dataframe[  # Accesses the DataFrame.
            "close_price"  # Selects closing prices.
        ]
        .pct_change()  # Calculates fractional price changes.
        .std()  # Calculates standard deviation of those changes.
    )

    if (  # Checks whether the calculated volatility cannot safely be used.
        historical_volatility is None  # Handles a missing Python value.
        or  # Any of these conditions will trigger the fallback.
        np.isnan(  # NumPy checks whether the value is NaN.
            historical_volatility  # Supplies the volatility value.
        )
        or
        historical_volatility == 0  # Protects against zero volatility.
    ):
        historical_volatility = 0.01  # Uses a small fallback volatility value.

    random_generator = (  # Stores a NumPy random-number generator object.
        np.random.default_rng(  # Creates the generator.
            42  # Fixed seed makes repeated tests reproducible.
        )
    )

    price_columns = [  # Stores all market-price column names.
        "open_price",  # Opening prices.
        "high_price",  # High prices.
        "low_price",  # Low prices.
        "close_price",  # Closing prices.
    ]

    end_index = min(  # Prevents the stress window exceeding available rows.
        start_index  # Starts with the chosen first row.
        +
        duration,  # Adds the stress duration.
        number_of_rows,  # Maximum boundary is total observations.
    )

    for row_index in range(  # Iterates through each row inside the spike window.
        start_index,  # First stressed row.
        end_index,  # Stops before this index.
    ):
        shock = (  # Generates one random shock value.
            random_generator.normal(  # Draws from a normal probability distribution.
                0,  # Distribution mean is zero.
                historical_volatility  # Starts with normal market volatility.
                *
                spike_magnitude,  # Multiplies volatility by scenario severity.
            )
        )

        shock_factor = max(  # Prevents the multiplier becoming impossibly low.
            0.05,  # Minimum price multiplier.
            1  # Neutral price multiplier.
            +
            shock,  # Adds the randomly generated shock.
        )

        dataframe.loc[  # Selects one DataFrame row and all OHLC prices.
            row_index,  # Current loop row.
            price_columns,  # Columns being stressed.
        ] *= shock_factor  # Multiplies prices by the random shock factor.

    return dataframe  # Returns the stressed DataFrame.

# ============================================================
# 14. LIQUIDITY CRISIS SCENARIO
# ============================================================

def _apply_liquidity_crisis(  # Defines a helper that simulates falling trading volume.
    dataframe,  # Receives historical observations.
    parameters,  # Receives scenario configuration.
):
    """
    Simulate a substantial reduction in trading volume.

    This is an educational liquidity proxy.

    MarketPulse does not currently model a complete order book,
    therefore this scenario should not be interpreted as a
    professional market-impact model.
    """

    dataframe = (  # Creates an independent copy.
        dataframe.copy()  # Keeps the original dataset untouched.
    )

    number_of_rows = len(  # Counts observations.
        dataframe  # DataFrame being counted.
    )

    crisis_start = float(  # Converts starting location to float.
        parameters.get(  # Reads parameter dictionary.
            "crisis_start",  # Requests starting proportion.
            0.60,  # Defaults to 60% through the history.
        )
    )

    crisis_duration = float(  # Converts duration to a float.
        parameters.get(  # Reads the requested dictionary key.
            "crisis_duration",  # Scenario duration.
            0.20,  # Defaults to 20% of observations.
        )
    )

    volume_reduction = float(  # Converts volume reduction to a float.
        parameters.get(  # Reads the scenario parameter.
            "volume_reduction",  # Requests reduction magnitude.
            0.70,  # Defaults to reducing volume by 70%.
        )
    )

    crisis_start = max(  # Applies a lower boundary.
        0.0,  # Earliest possible start.
        min(  # Applies an upper boundary.
            1.0,  # Latest allowed proportion.
            crisis_start,  # User/configured value.
        ),
    )

    crisis_duration = max(  # Prevents an extremely small/negative duration.
        0.01,  # Minimum duration proportion.
        min(  # Caps duration.
            1.0,  # Maximum full-sample duration.
            crisis_duration,  # Configured value.
        ),
    )

    volume_reduction = max(  # Prevents negative volume reductions.
        0.0,  # Minimum reduction.
        min(  # Caps the maximum reduction.
            0.99,  # Leaves at least a very small amount of volume.
            volume_reduction,  # Configured value.
        ),
    )

    start_index = int(  # Calculates integer starting row.
        number_of_rows  # Total observations.
        *
        crisis_start  # Starting fraction.
    )

    duration = max(  # Guarantees at least one affected observation.
        1,  # Minimum row count.
        int(  # Converts calculated count into integer.
            number_of_rows  # Total observations.
            *
            crisis_duration  # Fraction of data affected.
        ),
    )

    end_index = min(  # Keeps the end inside the DataFrame.
        start_index  # Crisis start.
        +
        duration,  # Adds crisis length.
        number_of_rows  # Uses total row count.
        -
        1,  # Converts the count into the last valid index.
    )

    dataframe.loc[  # Selects the affected DataFrame section.
        start_index:end_index,  # Selects rows inside the crisis period.
        "volume",  # Selects only trading volume.
    ] *= (  # Modifies volume values in place.
        1  # Starts from full volume.
        -
        volume_reduction  # Removes the configured proportion.
    )

    return dataframe  # Returns the modified historical scenario.

# ============================================================
# 15. REGIME CHANGE SCENARIO
# ============================================================

def _apply_regime_change(  # Defines a helper that changes price behaviour after a point in time.
    dataframe,  # Receives historical data.
    parameters,  # Receives scenario parameters.
):
    """
    Simulate a structural change in market direction.

    The supplied new_trend is used as an educational price
    adjustment after the selected change point.
    """

    dataframe = (  # Makes an independent data copy.
        dataframe.copy()  # Prevents changes to the original historical input.
    )

    number_of_rows = len(  # Counts observations.
        dataframe  # DataFrame being measured.
    )

    change_point = float(  # Converts selected change position to a float.
        parameters.get(  # Reads from the configuration dictionary.
            "change_point",  # Requests change-point fraction.
            0.50,  # Defaults to halfway through the sample.
        )
    )

    new_trend = float(  # Converts trend adjustment into float.
        parameters.get(  # Reads from scenario configuration.
            "new_trend",  # Requests new trend adjustment.
            -0.01,  # Defaults to a negative one-percent adjustment.
        )
    )

    change_point = max(  # Prevents a negative change point.
        0.0,  # Earliest possible fraction.
        min(  # Caps the change point.
            1.0,  # Latest possible fraction.
            change_point,  # Configured value.
        ),
    )

    # Avoid impossible price adjustments.
    new_trend = max(  # Applies a lower bound.
        -0.95,  # Maximum negative adjustment.
        min(  # Applies an upper bound.
            1.0,  # Maximum positive adjustment.
            new_trend,  # Configured trend.
        ),
    )

    start_index = int(  # Calculates starting row of structural change.
        number_of_rows  # Number of observations.
        *
        change_point  # Fraction at which new regime begins.
    )

    price_columns = [  # Contains all OHLC price fields.
        "open_price",  # Opening price.
        "high_price",  # Highest price.
        "low_price",  # Lowest price.
        "close_price",  # Closing price.
    ]

    adjustment_factor = max(  # Prevents impossible or negative adjusted prices.
        0.05,  # Minimum multiplication factor.
        1  # Neutral factor.
        +
        new_trend,  # Applies the configured trend adjustment.
    )

    for row_index in range(  # Iterates over every row after the change point.
        start_index,  # Begins at the calculated regime-change location.
        number_of_rows,  # Continues to the end of the dataset.
    ):
        dataframe.loc[  # Selects price fields on the current row.
            row_index,  # Current observation.
            price_columns,  # All OHLC price columns.
        ] *= adjustment_factor  # Applies the same regime adjustment factor.

    return dataframe  # Returns the modified DataFrame.

# ============================================================
# 16. STRESS PERFORMANCE METRICS
# ============================================================

def _stress_performance(  # Defines a helper for measuring strategy performance after stress.
    dataframe,  # Receives stressed market data.
    strategy,  # Receives the Strategy object to test.
):
    """
    Calculate stress performance metrics from the strategy
    equity curve.

    Returns:

    - maximum drawdown
    - recovery time
    - whether recovery occurred
    """

    # ========================================================
    # 16.1 CREATE EQUITY CURVE
    # ========================================================

    equity_curve = (  # Stores the strategy's cumulative value through the stressed data.
        _strategy_equity_curve(  # Calls the previously defined helper.
            dataframe,  # Supplies stressed historical data.
            strategy,  # Supplies the strategy.
        )
    )

    if equity_curve.empty:  # Checks whether the strategy could produce an equity curve.
        return None  # Stops if performance cannot be measured.

    # ========================================================
    # 16.2 RUNNING PEAK
    # ========================================================

    running_peak = (  # Stores the highest equity value observed up to each point.
        equity_curve  # Uses the calculated strategy value.
        .cummax()  # Calculates cumulative maximum values.
    )

    # ========================================================
    # 16.3 POSITIVE DRAWDOWN MAGNITUDE
    # ========================================================

    drawdown = (  # Calculates distance below the previous equity peak.
        running_peak  # Previous/highest value.
        -
        equity_curve  # Current strategy equity.
    ) / running_peak.replace(  # Divides loss by the relevant peak.
        0,  # Searches for zero peaks.
        np.nan,  # Replaces zero with NaN to prevent division by zero.
    )

    drawdown = (  # Cleans the resulting drawdown Series.
        drawdown  # Uses calculated drawdowns.
        .fillna(0)  # Converts missing values into zero.
    )

    maximum_drawdown = float(  # Converts largest drawdown into a normal Python float.
        drawdown.max()  # Selects the largest loss magnitude.
    )

    # ========================================================
    # 16.4 DRAWDOWN TROUGH
    # ========================================================

    trough_index = int(  # Converts the index into an integer.
        drawdown.idxmax()  # Finds the index where maximum drawdown occurs.
    )

    peak_before_trough = float(  # Stores the previous equity peak used for recovery testing.
        running_peak.iloc[  # Selects a value by integer position.
            trough_index  # Uses the maximum-drawdown position.
        ]
    )

    # ========================================================
    # 16.5 RECOVERY VARIABLES
    # Programming concept: state variables
    # ========================================================

    recovery_time = 0  # Starts with zero observed recovery sessions.
    recovered = False  # Boolean records whether recovery has happened.

    after_trough = (  # Selects all equity values after maximum drawdown.
        equity_curve.iloc[  # Uses pandas integer-position indexing.
            trough_index + 1:  # Begins immediately after the trough.
        ]
    )

    # ========================================================
    # 16.6 SEARCH FOR RECOVERY
    # Programming concept: enumerate + loop + break
    # ========================================================

    for (  # Iterates through post-trough equity observations.
        relative_index,  # Receives a running counter.
        equity_value,  # Receives each equity value.
    ) in enumerate(  # enumerate supplies both position and value.
        after_trough,  # Collection being iterated.
        start=1,  # Starts the recovery counter at one.
    ):
        if (  # Tests whether the strategy has regained its previous peak.
            float(  # Converts the pandas value into a standard float.
                equity_value  # Current strategy-equity value.
            )
            >=
            peak_before_trough  # Required recovery level.
        ):
            recovery_time = (  # Stores how many observations recovery required.
                relative_index  # Uses loop counter.
            )

            recovered = True  # Marks the strategy as recovered.
            break  # Stops searching because recovery has already occurred.

    # If recovery was not observed, record the remaining
    # number of sessions in the available sample.

    if not recovered:  # Runs only when recovery was never detected.
        recovery_time = max(  # Makes sure recovery time cannot become negative.
            0,  # Minimum possible value.
            len(  # Counts total equity observations.
                equity_curve  # Series being measured.
            )
            -
            trough_index  # Removes observations before the trough.
            -
            1,  # Adjusts for index position.
        )

    # ========================================================
    # 16.7 RETURN PERFORMANCE DICTIONARY
    # Programming concept: dictionary
    # ========================================================

    return {  # Returns three named values in a Python dictionary.
        "maximum_drawdown":
            maximum_drawdown,  # Stores maximum loss magnitude.
        "recovery_time":
            recovery_time,  # Stores number of sessions required/available.
        "recovered":
            recovered,  # Stores Boolean recovery status.
    }

# ============================================================
# 17. STRESS TEST
# ============================================================

def run_stress_test(  # Defines the public service function for educational stress testing.
    strategy,  # Receives the strategy being tested.
    symbol,  # Receives the market ticker.
    test_type,  # Receives the selected scenario name.
    parameters,  # Receives scenario settings as a dictionary.
):
    """
    ============================================================
    STRESS TESTING
    ============================================================

    User-facing location:

        RISK
            ↓
        Stress Test


    PURPOSE:

    Evaluate how a strategy behaves after MarketPulse modifies
    historical data to simulate severe market conditions.


    Supported scenarios:

    crash
        Sudden market decline

    volatility_spike
        Temporary increase in price volatility

    liquidity_crisis
        Substantial reduction in trading volume

    regime_change
        Structural change in market behaviour


    IMPORTANT:

    These are hypothetical historical scenarios.
    They are not predictions of future market losses.
    ============================================================
    """

    # ========================================================
    # 17.1 NORMALISE SYMBOL
    # ========================================================

    symbol = (  # Stores a cleaned ticker.
        symbol  # Starts with user/application supplied text.
        .strip()  # Removes unnecessary spaces.
        .upper()  # Uses a consistent uppercase representation.
    )

    # ========================================================
    # 17.2 FIND LATEST STORED DATA
    # ========================================================

    latest_date = (  # Stores newest available market-data date.
        _latest_market_date(  # Calls shared database helper.
            symbol  # Supplies ticker.
        )
    )

    if latest_date is None:  # Tests whether no history exists for the symbol.
        return None  # Stops stress testing because there is no source data.

    # ========================================================
    # 17.3 LOAD APPROXIMATELY TWO YEARS
    # ========================================================

    start_date = (  # Calculates beginning of the stress-test data window.
        latest_date  # Starts with newest available date.
        -
        timedelta(  # Creates date difference.
            days=730  # Moves backwards approximately two calendar years.
        )
    )

    dataframe = (  # Stores the prepared historical DataFrame.
        _frame(  # Loads historical data through the shared helper.
            symbol,  # Supplies ticker.
            start_date,  # Supplies window start.
            latest_date,  # Supplies window end.
        )
        .reset_index(  # Resets pandas row labels.
            drop=True  # Discards the old index instead of adding it as a column.
        )
    )

    # Require enough historical observations to produce a
    # meaningful educational scenario.
    if len(dataframe) < 100:  # Requires at least 100 stored observations.
        return None  # Stops if historical sample is too small.

    # ========================================================
    # 17.4 APPLY SELECTED SCENARIO
    # Programming concept: if / elif dispatch
    # ========================================================

    if test_type == "crash":  # Checks whether the selected scenario is a crash.
        stressed_data = (  # Stores the modified market data.
            _apply_crash_scenario(  # Calls the crash helper.
                dataframe,  # Supplies historical observations.
                parameters,  # Supplies scenario configuration.
            )
        )
    elif test_type == "volatility_spike":  # Checks for volatility-spike scenario.
        stressed_data = (  # Stores simulated stressed observations.
            _apply_volatility_spike(  # Calls volatility helper.
                dataframe,  # Supplies source data.
                parameters,  # Supplies scenario settings.
            )
        )
    elif test_type == "liquidity_crisis":  # Checks for liquidity-crisis scenario.
        stressed_data = (  # Stores the scenario result.
            _apply_liquidity_crisis(  # Calls liquidity helper.
                dataframe,  # Supplies market data.
                parameters,  # Supplies scenario configuration.
            )
        )
    elif test_type == "regime_change":  # Checks for structural-regime-change scenario.
        stressed_data = (  # Stores transformed data.
            _apply_regime_change(  # Calls regime-change helper.
                dataframe,  # Supplies historical data.
                parameters,  # Supplies scenario parameters.
            )
        )
    else:  # Handles unsupported test_type values.
        return None  # Stops instead of running an unknown scenario.

    # ========================================================
    # 17.5 CALCULATE STRESSED STRATEGY PERFORMANCE
    # ========================================================

    performance = (  # Stores dictionary returned by performance helper.
        _stress_performance(  # Calculates drawdown and recovery information.
            stressed_data,  # Supplies scenario-modified historical data.
            strategy,  # Supplies the Strategy object.
        )
    )

    if performance is None:  # Checks whether metrics could not be calculated.
        return None  # Ends without creating a StressTest result.

    maximum_drawdown = (  # Extracts maximum drawdown from the dictionary.
        performance[
            "maximum_drawdown"  # Dictionary key containing drawdown.
        ]
    )

    recovery_time = (  # Extracts recovery duration.
        performance[
            "recovery_time"  # Dictionary key containing duration.
        ]
    )

    recovered = (  # Extracts Boolean recovery status.
        performance[
            "recovered"  # Dictionary key containing True or False.
        ]
    )

    # ========================================================
    # 17.6 ROBUSTNESS SCORE
    # ========================================================

    # Larger drawdowns reduce the score.
    drawdown_penalty = (  # Calculates score penalty from maximum drawdown.
        maximum_drawdown  # Uses positive drawdown magnitude.
        *
        1.5  # Scales its influence on the score.
    )

    # Longer recovery periods also reduce the score.
    recovery_penalty = (  # Calculates score penalty from recovery time.
        min(  # Caps the recovery time used by the scoring formula.
            recovery_time,  # Actual calculated recovery duration.
            180,  # Maximum duration included in penalty.
        )
        /
        360  # Scales recovery duration into the final score.
    )

    robustness_score = (  # Creates initial resilience score.
        1  # Starts from perfect score of 1.
        -
        drawdown_penalty  # Removes drawdown penalty.
        -
        recovery_penalty  # Removes recovery-time penalty.
    )

    robustness_score = max(  # Provides lower boundary.
        0.0,  # Minimum permitted score.
        min(  # Provides upper boundary.
            1.0,  # Maximum permitted score.
            robustness_score,  # Raw calculated score.
        ),
    )

    # ========================================================
    # 17.7 PASS / FAIL
    # Programming concept: Boolean comparison
    # ========================================================

    passed_test = (  # Produces True or False.
        robustness_score  # Uses final score.
        >=
        0.50  # Requires at least 50% to pass.
    )

    # ========================================================
    # 17.8 HUMAN-READABLE RECOVERY RESULT
    # ========================================================

    if recovered:  # Runs when the previous equity peak was regained.
        recovery_text = (  # Creates readable explanatory text.
            f"Estimated recovery occurred after "  # Starts an f-string message.
            f"{recovery_time} trading sessions."  # Inserts calculated recovery time.
        )
    else:  # Runs when no recovery occurred within available observations.
        recovery_text = (  # Creates alternative explanation.
            "The strategy did not recover to its previous "
            "equity peak within the available historical "
            "stress window."
        )

    # ========================================================
    # 17.9 HUMAN-READABLE PASS / FAIL RESULT
    # ========================================================

    if passed_test:  # Checks the Boolean stress-test classification.
        assessment_text = (  # Stores positive assessment text.
            "The strategy passed this educational stress "
            "scenario, although additional scenarios should "
            "still be tested."
        )
    else:  # Runs for scores below the passing threshold.
        assessment_text = (  # Stores warning assessment text.
            "The strategy showed weak resilience under this "
            "scenario. Review position sizing, stop-loss "
            "assumptions and strategy complexity."
        )

    # ========================================================
    # 17.10 COMBINE NOTES
    # Programming concept: f-strings / string concatenation
    # ========================================================

    notes = (  # Creates one readable summary string.
        f"Maximum drawdown: "  # Begins the formatted text.
        f"{maximum_drawdown:.2%}. "  # Formats drawdown as a percentage with two decimals.
        f"{recovery_text} "  # Inserts the recovery explanation.
        f"{assessment_text}"  # Inserts the final assessment.
    )

    # ========================================================
    # 17.11 SAVE STRESS TEST RESULT
    # Programming concept: Django ORM persistence
    # ========================================================

    stress_test = (  # Stores newly created StressTest model object.
        StressTest.objects  # Accesses StressTest model manager.
        .create(  # Creates and immediately saves a database row.
            user=
                strategy.user,  # Associates result with strategy owner.
            strategy=
                strategy,  # Associates result with tested Strategy.
            symbol=
                symbol,  # Stores analysed ticker.
            test_type=
                test_type,  # Stores selected stress-scenario type.
            test_parameters=
                parameters,  # Stores scenario settings.

            # IMPORTANT:
            # Drawdown is saved as a positive loss magnitude.
            #
            # Example:
            #
            # 25% drawdown
            #
            # stored as:
            #
            # 0.25

            max_drawdown=
                to_decimal(  # Converts float into Decimal before database storage.
                    maximum_drawdown  # Supplies calculated maximum drawdown.
                ),
            recovery_time=
                recovery_time,  # Saves number of trading sessions.
            robustness_score=
                to_decimal(  # Converts float score into Decimal.
                    robustness_score  # Supplies final robustness score.
                ),
            passed_test=
                passed_test,  # Saves True/False test result.
            notes=
                notes,  # Saves the readable assessment.
        )
    )

    # ========================================================
    # 17.12 RETURN SAVED RESULT
    # ========================================================

    return stress_test  # Sends the newly created StressTest object back to the caller.