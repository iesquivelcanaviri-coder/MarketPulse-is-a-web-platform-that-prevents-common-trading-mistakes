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
# 1. PYTHON IMPORTS
# ============================================================

from datetime import date, timedelta
from decimal import Decimal


# ============================================================
# 2. THIRD-PARTY IMPORTS
# ============================================================

import numpy as np
import pandas as pd


# ============================================================
# 3. DJANGO / MARKETPULSE IMPORTS
# ============================================================

from core.models import MarketData

from .models import (
    MarketRegime,
    OverfittingTest,
    StressTest,
)


# ============================================================
# 4. DECIMAL CONVERSION HELPER
# ============================================================

def to_decimal(value):
    """
    Convert Python / NumPy numeric values into Decimal values.

    Django DecimalField values should not normally be created
    directly from floating-point numbers because binary
    floating-point representation can introduce small
    precision differences.

    Converting through str() makes the value safer and easier
    to understand.
    """

    return Decimal(
        str(value)
    )


# ============================================================
# 5. MARKET DATAFRAME HELPER
# ============================================================

def _frame(
    symbol,
    start_date,
    end_date,
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
    # Normalise symbol
    # --------------------------------------------------------

    symbol = (
        symbol
        .strip()
        .upper()
    )


    # --------------------------------------------------------
    # Read historical observations
    # --------------------------------------------------------

    rows = list(

        MarketData.objects
        .filter(
            symbol=symbol,
            date__gte=start_date,
            date__lte=end_date,
        )
        .order_by("date")
        .values(
            "date",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
        )
    )


    # --------------------------------------------------------
    # Return empty DataFrame when there is no stored data
    # --------------------------------------------------------

    if not rows:

        return pd.DataFrame()


    # --------------------------------------------------------
    # Convert database records into pandas
    # --------------------------------------------------------

    dataframe = pd.DataFrame(
        rows
    )


    # --------------------------------------------------------
    # Convert Decimal database prices to float for numerical
    # calculations.
    # --------------------------------------------------------

    price_columns = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
    ]


    for column in price_columns:

        dataframe[column] = (
            dataframe[column]
            .astype(float)
        )


    # Volume should also be numeric.
    dataframe["volume"] = (
        pd.to_numeric(
            dataframe["volume"],
            errors="coerce",
        )
        .fillna(0)
    )


    return dataframe


# ============================================================
# 6. GET LATEST STORED MARKET DATE
# ============================================================

def _latest_market_date(
    symbol,
):
    """
    Return the most recent MarketData date stored for a symbol.

    This is preferable to blindly assuming that MarketPulse
    contains data for today's calendar date.
    """


    symbol = (
        symbol
        .strip()
        .upper()
    )


    return (

        MarketData.objects
        .filter(
            symbol=symbol
        )
        .order_by(
            "-date"
        )
        .values_list(
            "date",
            flat=True,
        )
        .first()
    )


# ============================================================
# 7. STRATEGY PARAMETER HELPER
# ============================================================

def _strategy_parameters(
    strategy,
):
    """
    Extract moving-average parameters from the first active
    StrategyRule.

    MarketPulse's current educational Strategy Builder is
    based primarily on moving-average crossover rules.

    Defaults are supplied so the analysis remains stable if
    a rule does not contain explicit parameter values.
    """


    rule = (

        strategy.rules
        .filter(
            is_active=True
        )
        .first()
    )


    # If there is no active rule, try any existing rule.
    if rule is None:

        rule = (
            strategy.rules
            .first()
        )


    parameters = (
        rule.parameters
        if rule
        else {}
    )


    try:

        fast_period = int(
            parameters.get(
                "fast_period",
                10,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        fast_period = 10


    try:

        slow_period = int(
            parameters.get(
                "slow_period",
                30,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        slow_period = 30


    # --------------------------------------------------------
    # Defensive validation
    # --------------------------------------------------------

    fast_period = max(
        2,
        fast_period,
    )


    slow_period = max(
        fast_period + 1,
        slow_period,
    )


    return (
        fast_period,
        slow_period,
    )


# ============================================================
# 8. MOVING-AVERAGE STRATEGY RETURN
# ============================================================

def _ma_return(
    dataframe,
    fast_period=10,
    slow_period=30,
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


    if dataframe.empty:

        return 0.0


    if len(dataframe) < (
        slow_period + 2
    ):

        return 0.0


    close = (
        dataframe["close_price"]
        .astype(float)
    )


    fast_ma = (
        close
        .rolling(
            fast_period
        )
        .mean()
    )


    slow_ma = (
        close
        .rolling(
            slow_period
        )
        .mean()
    )


    signal = (
        fast_ma
        >
        slow_ma
    ).astype(int)


    asset_returns = (
        close
        .pct_change()
        .fillna(0)
    )


    strategy_returns = (

        asset_returns
        *
        signal
        .shift(1)
        .fillna(0)
    )


    cumulative_return = (

        (
            1
            +
            strategy_returns
        )
        .prod()
        -
        1
    )


    return float(
        cumulative_return
    )


# ============================================================
# 9. STRATEGY EQUITY CURVE
# ============================================================

def _strategy_equity_curve(
    dataframe,
    strategy,
):
    """
    Build an educational strategy equity curve using the
    strategy's moving-average parameters.

    This is useful for scenario stress testing because the
    test should examine strategy behaviour rather than only
    the raw market price.
    """


    if dataframe.empty:

        return pd.Series(
            dtype=float
        )


    fast_period, slow_period = (
        _strategy_parameters(
            strategy
        )
    )


    if len(dataframe) < (
        slow_period + 2
    ):

        return pd.Series(
            dtype=float
        )


    close = (
        dataframe["close_price"]
        .astype(float)
    )


    fast_ma = (
        close
        .rolling(
            fast_period
        )
        .mean()
    )


    slow_ma = (
        close
        .rolling(
            slow_period
        )
        .mean()
    )


    signal = (
        fast_ma
        >
        slow_ma
    ).astype(int)


    returns = (
        close
        .pct_change()
        .fillna(0)
    )


    strategy_returns = (

        returns
        *
        signal
        .shift(1)
        .fillna(0)
    )


    equity_curve = (

        1
        +
        strategy_returns
    ).cumprod()


    return equity_curve


# ============================================================
# 10. STRATEGY ROBUSTNESS / OVERFITTING ANALYSIS
# ============================================================

def detect_overfitting(
    strategy,
    symbol,
    periods,
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


    symbol = (
        symbol
        .strip()
        .upper()
    )


    fast_period, slow_period = (
        _strategy_parameters(
            strategy
        )
    )


    created_tests = []


    for (
        period_start,
        period_end,
    ) in periods:


        # ====================================================
        # 10.1 VALIDATE PERIOD
        # ====================================================

        total_days = (

            period_end
            -
            period_start
        ).days


        if total_days <= 0:

            continue


        # ====================================================
        # 10.2 70 / 30 SPLIT
        # ====================================================

        split_days = int(
            total_days
            *
            0.70
        )


        split_date = (

            period_start
            +
            timedelta(
                days=split_days
            )
        )


        out_sample_start = (

            split_date
            +
            timedelta(
                days=1
            )
        )


        # ====================================================
        # 10.3 LOAD BOTH DATA WINDOWS
        # ====================================================

        in_sample_data = _frame(
            symbol,
            period_start,
            split_date,
        )


        out_sample_data = _frame(
            symbol,
            out_sample_start,
            period_end,
        )


        # ====================================================
        # 10.4 STRATEGY RETURNS
        # ====================================================

        in_sample_return = (
            _ma_return(
                in_sample_data,
                fast_period,
                slow_period,
            )
        )


        out_sample_return = (
            _ma_return(
                out_sample_data,
                fast_period,
                slow_period,
            )
        )


        # ====================================================
        # 10.5 OVERFITTING SCORE
        # ====================================================

        # We only assign deterioration when the in-sample
        # performance is stronger than the out-of-sample
        # performance.

        if (
            in_sample_return
            >
            out_sample_return
        ):

            denominator = max(
                abs(
                    in_sample_return
                ),
                0.01,
            )


            deterioration = (

                in_sample_return
                -
                out_sample_return

            ) / denominator


            overfitting_score = max(
                0.0,
                min(
                    1.0,
                    deterioration,
                ),
            )

        else:

            overfitting_score = 0.0


        # ====================================================
        # 10.6 CLASSIFICATION
        # ====================================================

        is_overfitted = (
            overfitting_score
            >
            0.30
        )


        # ====================================================
        # 10.7 PLAIN-LANGUAGE INTERPRETATION
        # ====================================================

        if is_overfitted:

            recommendation = (
                "Large out-of-sample deterioration was detected. "
                "Consider simplifying the strategy rules, reducing "
                "parameter tuning and testing on additional unseen "
                "historical periods."
            )

        else:

            recommendation = (
                "Performance was reasonably stable across this "
                "historical test window. Continue testing across "
                "additional periods and market conditions."
            )


        # ====================================================
        # 10.8 SAVE RESULT
        # ====================================================

        test = (
            OverfittingTest.objects
            .create(

                user=
                    strategy.user,

                strategy=
                    strategy,

                symbol=
                    symbol,

                test_period=
                    (
                        f"{period_start} "
                        f"to "
                        f"{period_end}"
                    ),

                in_sample_return=
                    to_decimal(
                        in_sample_return
                    ),

                out_sample_return=
                    to_decimal(
                        out_sample_return
                    ),

                overfitting_score=
                    to_decimal(
                        overfitting_score
                    ),

                is_overfitted=
                    is_overfitted,

                recommendations=
                    recommendation,
            )
        )


        created_tests.append(
            test
        )


    return created_tests


# ============================================================
# 11. MARKET CONDITION / REGIME ANALYSIS
# ============================================================

def identify_market_regime(
    symbol,
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


    symbol = (
        symbol
        .strip()
        .upper()
    )


    # ========================================================
    # 11.1 GET MOST RECENT STORED MARKET DATE
    # ========================================================

    latest_date = (
        _latest_market_date(
            symbol
        )
    )


    if latest_date is None:

        return None


    # ========================================================
    # 11.2 LOAD APPROXIMATELY 300 CALENDAR DAYS
    # ========================================================

    start_date = (

        latest_date
        -
        timedelta(
            days=300
        )
    )


    dataframe = _frame(
        symbol,
        start_date,
        latest_date,
    )


    # At least 60 observations are needed because the
    # classifier uses a 60-period moving average.

    if len(dataframe) < 60:

        return None


    # ========================================================
    # 11.3 PRICE SERIES
    # ========================================================

    close = (
        dataframe[
            "close_price"
        ]
        .astype(float)
    )


    # ========================================================
    # 11.4 ANNUALISED VOLATILITY
    # ========================================================

    daily_returns = (
        close
        .pct_change()
        .dropna()
    )


    if daily_returns.empty:

        return None


    volatility = float(

        daily_returns.std()
        *
        np.sqrt(252)
    )


    # ========================================================
    # 11.5 MOVING AVERAGES
    # ========================================================

    ma_20 = float(

        close
        .rolling(20)
        .mean()
        .iloc[-1]
    )


    ma_60 = float(

        close
        .rolling(60)
        .mean()
        .iloc[-1]
    )


    current_price = float(
        close.iloc[-1]
    )


    # ========================================================
    # 11.6 TREND STRENGTH
    # ========================================================

    if ma_60:

        trend_strength = (

            ma_20
            /
            ma_60
            -
            1
        )

    else:

        trend_strength = 0.0


    # ========================================================
    # 11.7 REGIME CLASSIFICATION
    # ========================================================

    if volatility > 0.40:

        regime = "volatile"


    elif (
        current_price
        >
        ma_20
        >
        ma_60
        and
        trend_strength
        >
        0.01
    ):

        regime = "bull"


    elif (
        current_price
        <
        ma_20
        <
        ma_60
        and
        trend_strength
        <
        -0.01
    ):

        regime = "bear"


    else:

        regime = "sideways"


    # ========================================================
    # 11.8 CONFIDENCE SCORE
    # ========================================================

    trend_component = (

        abs(
            trend_strength
        )
        *
        10
    )


    volatility_component = min(
        volatility,
        0.50,
    )


    confidence = min(
        1.0,
        trend_component
        +
        volatility_component,
    )


    # ========================================================
    # 11.9 SAVE OR UPDATE RESULT
    # ========================================================

    market_regime, created = (

        MarketRegime.objects
        .update_or_create(

            symbol=
                symbol,

            date=
                latest_date,

            defaults={

                "regime":
                    regime,

                "confidence":
                    to_decimal(
                        confidence
                    ),

                "volatility":
                    to_decimal(
                        volatility
                    ),

                "trend_strength":
                    to_decimal(
                        trend_strength
                    ),
            },
        )
    )


    return market_regime


# ============================================================
# 12. STRESS SCENARIO HELPERS
# ============================================================

def _apply_crash_scenario(
    dataframe,
    parameters,
):
    """
    Simulate a sudden downward price shock.
    """


    dataframe = (
        dataframe.copy()
    )


    number_of_rows = len(
        dataframe
    )


    crash_start = float(
        parameters.get(
            "crash_start",
            0.70,
        )
    )


    crash_magnitude = float(
        parameters.get(
            "crash_magnitude",
            0.20,
        )
    )


    crash_start = max(
        0.0,
        min(
            1.0,
            crash_start,
        ),
    )


    crash_magnitude = max(
        0.0,
        min(
            0.95,
            crash_magnitude,
        ),
    )


    start_index = int(
        number_of_rows
        *
        crash_start
    )


    price_columns = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
    ]


    dataframe.loc[
        start_index:,
        price_columns,
    ] *= (
        1
        -
        crash_magnitude
    )


    return dataframe


# ============================================================
# 13. VOLATILITY SPIKE SCENARIO
# ============================================================

def _apply_volatility_spike(
    dataframe,
    parameters,
):
    """
    Simulate a temporary period of substantially higher
    price volatility.

    A fixed random seed is used so repeated educational tests
    are reproducible.
    """


    dataframe = (
        dataframe.copy()
    )


    number_of_rows = len(
        dataframe
    )


    spike_start = float(
        parameters.get(
            "spike_start",
            0.50,
        )
    )


    spike_duration = float(
        parameters.get(
            "spike_duration",
            0.10,
        )
    )


    spike_magnitude = float(
        parameters.get(
            "spike_magnitude",
            3.0,
        )
    )


    start_index = int(

        number_of_rows
        *
        max(
            0.0,
            min(
                1.0,
                spike_start,
            ),
        )
    )


    duration = max(

        1,

        int(
            number_of_rows
            *
            max(
                0.01,
                min(
                    1.0,
                    spike_duration,
                ),
            )
        ),
    )


    historical_volatility = (

        dataframe[
            "close_price"
        ]
        .pct_change()
        .std()
    )


    if (
        historical_volatility is None
        or
        np.isnan(
            historical_volatility
        )
        or
        historical_volatility == 0
    ):

        historical_volatility = 0.01


    random_generator = (
        np.random.default_rng(
            42
        )
    )


    price_columns = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
    ]


    end_index = min(
        start_index
        +
        duration,
        number_of_rows,
    )


    for row_index in range(
        start_index,
        end_index,
    ):


        shock = (
            random_generator.normal(

                0,

                historical_volatility
                *
                spike_magnitude,
            )
        )


        shock_factor = max(
            0.05,
            1
            +
            shock,
        )


        dataframe.loc[
            row_index,
            price_columns,
        ] *= shock_factor


    return dataframe


# ============================================================
# 14. LIQUIDITY CRISIS SCENARIO
# ============================================================

def _apply_liquidity_crisis(
    dataframe,
    parameters,
):
    """
    Simulate a substantial reduction in trading volume.

    This is an educational liquidity proxy.

    MarketPulse does not currently model a complete order book,
    therefore this scenario should not be interpreted as a
    professional market-impact model.
    """


    dataframe = (
        dataframe.copy()
    )


    number_of_rows = len(
        dataframe
    )


    crisis_start = float(
        parameters.get(
            "crisis_start",
            0.60,
        )
    )


    crisis_duration = float(
        parameters.get(
            "crisis_duration",
            0.20,
        )
    )


    volume_reduction = float(
        parameters.get(
            "volume_reduction",
            0.70,
        )
    )


    crisis_start = max(
        0.0,
        min(
            1.0,
            crisis_start,
        ),
    )


    crisis_duration = max(
        0.01,
        min(
            1.0,
            crisis_duration,
        ),
    )


    volume_reduction = max(
        0.0,
        min(
            0.99,
            volume_reduction,
        ),
    )


    start_index = int(
        number_of_rows
        *
        crisis_start
    )


    duration = max(
        1,
        int(
            number_of_rows
            *
            crisis_duration
        ),
    )


    end_index = min(
        start_index
        +
        duration,
        number_of_rows
        -
        1,
    )


    dataframe.loc[
        start_index:end_index,
        "volume",
    ] *= (
        1
        -
        volume_reduction
    )


    return dataframe


# ============================================================
# 15. REGIME CHANGE SCENARIO
# ============================================================

def _apply_regime_change(
    dataframe,
    parameters,
):
    """
    Simulate a structural change in market direction.

    The supplied new_trend is used as an educational price
    adjustment after the selected change point.
    """


    dataframe = (
        dataframe.copy()
    )


    number_of_rows = len(
        dataframe
    )


    change_point = float(
        parameters.get(
            "change_point",
            0.50,
        )
    )


    new_trend = float(
        parameters.get(
            "new_trend",
            -0.01,
        )
    )


    change_point = max(
        0.0,
        min(
            1.0,
            change_point,
        ),
    )


    # Avoid impossible price adjustments.
    new_trend = max(
        -0.95,
        min(
            1.0,
            new_trend,
        ),
    )


    start_index = int(
        number_of_rows
        *
        change_point
    )


    price_columns = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
    ]


    adjustment_factor = max(
        0.05,
        1
        +
        new_trend,
    )


    for row_index in range(
        start_index,
        number_of_rows,
    ):

        dataframe.loc[
            row_index,
            price_columns,
        ] *= adjustment_factor


    return dataframe


# ============================================================
# 16. STRESS PERFORMANCE METRICS
# ============================================================

def _stress_performance(
    dataframe,
    strategy,
):
    """
    Calculate stress performance metrics from the strategy
    equity curve.

    Returns:

    - maximum drawdown
    - recovery time
    - whether recovery occurred
    """


    equity_curve = (
        _strategy_equity_curve(
            dataframe,
            strategy,
        )
    )


    if equity_curve.empty:

        return None


    # ========================================================
    # 16.1 RUNNING PEAK
    # ========================================================

    running_peak = (
        equity_curve
        .cummax()
    )


    # ========================================================
    # 16.2 POSITIVE DRAWDOWN MAGNITUDE
    # ========================================================

    drawdown = (

        running_peak
        -
        equity_curve

    ) / running_peak.replace(
        0,
        np.nan,
    )


    drawdown = (
        drawdown
        .fillna(0)
    )


    maximum_drawdown = float(
        drawdown.max()
    )


    # ========================================================
    # 16.3 DRAWDOWN TROUGH
    # ========================================================

    trough_index = int(
        drawdown.idxmax()
    )


    peak_before_trough = float(
        running_peak.iloc[
            trough_index
        ]
    )


    # ========================================================
    # 16.4 RECOVERY TIME
    # ========================================================

    recovery_time = 0

    recovered = False


    after_trough = (
        equity_curve.iloc[
            trough_index + 1:
        ]
    )


    for (
        relative_index,
        equity_value,
    ) in enumerate(
        after_trough,
        start=1,
    ):

        if (
            float(
                equity_value
            )
            >=
            peak_before_trough
        ):

            recovery_time = (
                relative_index
            )

            recovered = True

            break


    # If recovery was not observed, record the remaining
    # number of sessions in the available sample.
    if not recovered:

        recovery_time = max(
            0,
            len(
                equity_curve
            )
            -
            trough_index
            -
            1,
        )


    return {
        "maximum_drawdown":
            maximum_drawdown,

        "recovery_time":
            recovery_time,

        "recovered":
            recovered,
    }


# ============================================================
# 17. STRESS TEST
# ============================================================

def run_stress_test(
    strategy,
    symbol,
    test_type,
    parameters,
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


    symbol = (
        symbol
        .strip()
        .upper()
    )


    # ========================================================
    # 17.1 FIND LATEST STORED DATA
    # ========================================================

    latest_date = (
        _latest_market_date(
            symbol
        )
    )


    if latest_date is None:

        return None


    # ========================================================
    # 17.2 LOAD APPROXIMATELY TWO YEARS
    # ========================================================

    start_date = (

        latest_date
        -
        timedelta(
            days=730
        )
    )


    dataframe = (
        _frame(
            symbol,
            start_date,
            latest_date,
        )
        .reset_index(
            drop=True
        )
    )


    # Require enough historical observations to produce a
    # meaningful educational scenario.
    if len(dataframe) < 100:

        return None


    # ========================================================
    # 17.3 APPLY SELECTED SCENARIO
    # ========================================================

    if test_type == "crash":

        stressed_data = (
            _apply_crash_scenario(
                dataframe,
                parameters,
            )
        )


    elif test_type == "volatility_spike":

        stressed_data = (
            _apply_volatility_spike(
                dataframe,
                parameters,
            )
        )


    elif test_type == "liquidity_crisis":

        stressed_data = (
            _apply_liquidity_crisis(
                dataframe,
                parameters,
            )
        )


    elif test_type == "regime_change":

        stressed_data = (
            _apply_regime_change(
                dataframe,
                parameters,
            )
        )


    else:

        return None


    # ========================================================
    # 17.4 CALCULATE STRESSED STRATEGY PERFORMANCE
    # ========================================================

    performance = (
        _stress_performance(
            stressed_data,
            strategy,
        )
    )


    if performance is None:

        return None


    maximum_drawdown = (
        performance[
            "maximum_drawdown"
        ]
    )


    recovery_time = (
        performance[
            "recovery_time"
        ]
    )


    recovered = (
        performance[
            "recovered"
        ]
    )


    # ========================================================
    # 17.5 ROBUSTNESS SCORE
    # ========================================================

    # Larger drawdowns reduce the score.
    drawdown_penalty = (

        maximum_drawdown
        *
        1.5
    )


    # Longer recovery periods also reduce the score.
    recovery_penalty = (

        min(
            recovery_time,
            180,
        )
        /
        360
    )


    robustness_score = (

        1
        -
        drawdown_penalty
        -
        recovery_penalty
    )


    robustness_score = max(
        0.0,
        min(
            1.0,
            robustness_score,
        ),
    )


    # ========================================================
    # 17.6 PASS / FAIL
    # ========================================================

    passed_test = (
        robustness_score
        >=
        0.50
    )


    # ========================================================
    # 17.7 HUMAN-READABLE RESULT
    # ========================================================

    if recovered:

        recovery_text = (
            f"Estimated recovery occurred after "
            f"{recovery_time} trading sessions."
        )

    else:

        recovery_text = (
            "The strategy did not recover to its previous "
            "equity peak within the available historical "
            "stress window."
        )


    if passed_test:

        assessment_text = (
            "The strategy passed this educational stress "
            "scenario, although additional scenarios should "
            "still be tested."
        )

    else:

        assessment_text = (
            "The strategy showed weak resilience under this "
            "scenario. Review position sizing, stop-loss "
            "assumptions and strategy complexity."
        )


    notes = (
        f"Maximum drawdown: "
        f"{maximum_drawdown:.2%}. "
        f"{recovery_text} "
        f"{assessment_text}"
    )


    # ========================================================
    # 17.8 SAVE STRESS TEST RESULT
    # ========================================================

    stress_test = (
        StressTest.objects
        .create(

            user=
                strategy.user,

            strategy=
                strategy,

            symbol=
                symbol,

            test_type=
                test_type,

            test_parameters=
                parameters,

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
                to_decimal(
                    maximum_drawdown
                ),

            recovery_time=
                recovery_time,

            robustness_score=
                to_decimal(
                    robustness_score
                ),

            passed_test=
                passed_test,

            notes=
                notes,
        )
    )


    return stress_test