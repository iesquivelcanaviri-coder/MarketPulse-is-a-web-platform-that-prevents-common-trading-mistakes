"""
============================================================
MARKETPULSE - RISK CALCULATORS
============================================================

Framework mapping:

Historical Market Data
        ↓
core.MarketData
        ↓
risk_management/calculators.py
        ↓
risk_management/views.py
        ↓
Trade & Portfolio Risk
        ↓
Position Sizing / Stops / Reward-Risk


PURPOSE:

This module contains reusable financial-risk calculations
for the MarketPulse Risk area.

Keeping these calculations outside Django templates and views
means they can later be reused by:

- Django views
- REST API endpoints
- React components
- Backtesting
- Strategy testing
- Portfolio analysis
- Stress-testing workflows


IMPORTANT ARCHITECTURE:

This file is responsible for NORMAL RISK CALCULATIONS.

Stress-test scenario generation remains inside:

    analysis_tools/analyzers.py

This means:

risk_management/calculators.py
    → position sizing and normal risk

analysis_tools/analyzers.py
    → stress scenarios and analytical tests

============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

import math

import numpy as np

from core.models import MarketData


# ============================================================
# 2. ORIGINAL POSITION-SIZE CALCULATOR
# ============================================================

def calculate_position_size(
    account_balance,
    risk_percentage,
    stop_loss_pct,
    entry_price,
):
    """
    ============================================================
    ORIGINAL POSITION-SIZE CALCULATOR
    ============================================================

    Kept for backward compatibility with existing MarketPulse
    code.

    IMPORTANT:

    This older helper expects percentages as DECIMALS.

    Example:

        account_balance = 10000
        risk_percentage = 0.01
        stop_loss_pct = 0.05
        entry_price = 100

    Meaning:

        1% risk
        5% stop-loss distance

    Result:

        Maximum loss = 100
        Risk per share = 5
        Position size = 20 shares

    The newer calculate_trade_risk_plan() function instead uses
    human-readable percentages:

        1 means 1%
        5 means 5%
    ============================================================
    """

    account_balance = float(
        account_balance
    )

    risk_percentage = float(
        risk_percentage
    )

    stop_loss_pct = float(
        stop_loss_pct
    )

    entry_price = float(
        entry_price
    )


    # --------------------------------------------------------
    # Validate inputs
    # --------------------------------------------------------

    if account_balance <= 0:

        raise ValueError(
            "Account balance must be greater than zero."
        )


    if risk_percentage <= 0:

        raise ValueError(
            "Risk percentage must be greater than zero."
        )


    if stop_loss_pct <= 0:

        raise ValueError(
            "Stop-loss percentage must be greater than zero."
        )


    if entry_price <= 0:

        raise ValueError(
            "Entry price must be greater than zero."
        )


    # --------------------------------------------------------
    # Position-size calculation
    # --------------------------------------------------------

    risk_amount = (
        account_balance
        *
        risk_percentage
    )


    risk_per_unit = (
        entry_price
        *
        stop_loss_pct
    )


    return (
        risk_amount
        /
        risk_per_unit
    )


# ============================================================
# 3. ORIGINAL STOP-LOSS CALCULATOR
# ============================================================

def calculate_stop_loss(
    entry_price,
    stop_loss_pct=0.05,
):
    """
    ============================================================
    ORIGINAL LONG-POSITION STOP-LOSS CALCULATOR
    ============================================================

    This compatibility helper assumes a LONG position.

    Example:

        Entry price = 100
        Stop loss = 0.05

        Result = 95
    ============================================================
    """

    entry_price = float(
        entry_price
    )

    stop_loss_pct = float(
        stop_loss_pct
    )


    if entry_price <= 0:

        raise ValueError(
            "Entry price must be greater than zero."
        )


    if stop_loss_pct <= 0:

        raise ValueError(
            "Stop-loss percentage must be greater than zero."
        )


    if stop_loss_pct >= 1:

        raise ValueError(
            "This compatibility function expects the "
            "stop-loss as a decimal below 1. "
            "For example, use 0.05 for 5%."
        )


    return (
        entry_price
        *
        (
            1
            -
            stop_loss_pct
        )
    )


# ============================================================
# 4. ORIGINAL REWARD / RISK CALCULATOR
# ============================================================

def calculate_risk_reward_ratio(
    entry,
    stop,
    target,
):
    """
    ============================================================
    REWARD / RISK RATIO
    ============================================================

    Example:

        Entry = 100
        Stop = 95
        Target = 110

        Risk = 5
        Reward = 10

        Reward / Risk = 2.0
    ============================================================
    """

    entry = float(
        entry
    )

    stop = float(
        stop
    )

    target = float(
        target
    )


    risk = abs(
        entry
        -
        stop
    )


    reward = abs(
        target
        -
        entry
    )


    if risk == 0:

        return 0.0


    return float(
        reward
        /
        risk
    )


# ============================================================
# 5. HISTORICAL VOLATILITY
# ============================================================

def calculate_volatility(
    symbol,
    period=60,
):
    """
    ============================================================
    HISTORICAL VOLATILITY
    ============================================================

    Uses stored MarketPulse historical closing prices.

    Data flow:

        Historical provider
            ↓
        Data tab
            ↓
        core.MarketData
            ↓
        calculate_volatility()

    Steps:

    1. Retrieve historical closing prices.
    2. Calculate daily percentage returns.
    3. Calculate standard deviation.
    4. Annualise using sqrt(252).


    RETURNS:

        Decimal volatility.

    Example:

        0.25 = approximately 25% annualised volatility.
    ============================================================
    """

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )


    try:

        period = int(
            period
        )

    except (
        TypeError,
        ValueError,
    ):

        period = 60


    period = max(
        period,
        2,
    )


    # --------------------------------------------------------
    # Retrieve most recent observations
    # --------------------------------------------------------

    close_prices = list(

        MarketData.objects
        .filter(
            symbol=symbol
        )
        .order_by(
            "-date"
        )
        .values_list(
            "close_price",
            flat=True,
        )[:period + 1]

    )


    # --------------------------------------------------------
    # Need enough observations
    # --------------------------------------------------------

    if len(
        close_prices
    ) < 3:

        return 0.0


    # --------------------------------------------------------
    # Convert Decimal → float and restore chronological order
    # --------------------------------------------------------

    prices = np.array(

        [
            float(price)

            for price in reversed(
                close_prices
            )
        ],

        dtype=float,
    )


    # --------------------------------------------------------
    # Protect against invalid zero prices
    # --------------------------------------------------------

    previous_prices = (
        prices[:-1]
    )


    current_prices = (
        prices[1:]
    )


    valid_mask = (
        previous_prices
        >
        0
    )


    if np.count_nonzero(
        valid_mask
    ) < 2:

        return 0.0


    # --------------------------------------------------------
    # Daily returns
    # --------------------------------------------------------

    returns = (

        current_prices[
            valid_mask
        ]
        /
        previous_prices[
            valid_mask
        ]
        -
        1

    )


    if len(
        returns
    ) < 2:

        return 0.0


    # --------------------------------------------------------
    # Annualised volatility
    # --------------------------------------------------------

    annualised_volatility = (

        np.std(
            returns,
            ddof=1,
        )
        *
        math.sqrt(
            252
        )
    )


    return float(
        annualised_volatility
    )


# ============================================================
# 6. VOLATILITY-ADJUSTED RISK
# ============================================================

def volatility_adjusted_risk(
    base,
    vol,
):
    """
    ============================================================
    VOLATILITY-ADJUSTED RISK
    ============================================================

    Reduces an existing risk amount when historical volatility
    becomes higher.

    This function is retained because existing MarketPulse code
    may already use it.

    Example:

        base = 100
        volatility = 0.35

        result = 70
    ============================================================
    """

    base = float(
        base
    )

    vol = float(
        vol
    )


    if base < 0:

        raise ValueError(
            "Base risk cannot be negative."
        )


    if vol < 0:

        raise ValueError(
            "Volatility cannot be negative."
        )


    if vol >= 0.50:

        return (
            base
            *
            0.50
        )


    if vol >= 0.30:

        return (
            base
            *
            0.70
        )


    if vol >= 0.20:

        return (
            base
            *
            0.85
        )


    return base


# ============================================================
# 7. MARKET RISK CONTEXT
# ============================================================

def get_market_risk_context(
    symbol,
):
    """
    ============================================================
    MARKET RISK CONTEXT
    ============================================================

    Converts historical OHLC data stored by MarketPulse into
    useful risk information.


    CALCULATED METRICS:

    - Latest stored close
    - Latest stored date
    - Historical observation count
    - 14-day Average True Range
    - 20-day annualised historical volatility
    - 30-day high
    - 30-day low
    - Historical maximum drawdown


    IMPORTANT:

    These are HISTORICAL metrics calculated by MarketPulse.

    They are different from Alpaca's latest market snapshot.

    Therefore the Risk page can show:

        Alpaca
            → latest/current market information

        MarketPulse database
            → historical risk information


    Parameters
    ----------

    symbol:
        Example: AAPL, MSFT, NVDA


    Returns
    -------

    dict:
        Historical risk metrics.

    None:
        If MarketPulse does not contain historical observations
        for the requested symbol.
    ============================================================
    """

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )


    if not symbol:

        return None


    # --------------------------------------------------------
    # Retrieve historical data chronologically
    # --------------------------------------------------------

    data = list(

        MarketData.objects
        .filter(
            symbol=symbol
        )
        .order_by(
            "date"
        )
        .values(
            "date",
            "high_price",
            "low_price",
            "close_price",
        )

    )


    if not data:

        return None


    # ========================================================
    # 7.1 CONVERT STORED DECIMAL VALUES TO FLOAT
    # ========================================================

    closes = np.array(

        [
            float(
                row[
                    "close_price"
                ]
            )

            for row in data
        ],

        dtype=float,
    )


    highs = np.array(

        [
            float(
                row[
                    "high_price"
                ]
            )

            for row in data
        ],

        dtype=float,
    )


    lows = np.array(

        [
            float(
                row[
                    "low_price"
                ]
            )

            for row in data
        ],

        dtype=float,
    )


    # ========================================================
    # 7.2 LATEST STORED CLOSE
    # ========================================================

    latest_close = float(
        closes[-1]
    )


    # ========================================================
    # 7.3 DAILY RETURNS
    # ========================================================

    returns = np.array(
        [],
        dtype=float,
    )


    if len(
        closes
    ) >= 2:


        previous_prices = (
            closes[:-1]
        )


        current_prices = (
            closes[1:]
        )


        valid_mask = (
            previous_prices
            >
            0
        )


        if np.any(
            valid_mask
        ):

            returns = (

                current_prices[
                    valid_mask
                ]
                /
                previous_prices[
                    valid_mask
                ]
                -
                1

            )


    # ========================================================
    # 7.4 20-DAY ANNUALISED VOLATILITY
    # ========================================================

    annualised_volatility_pct = None


    if len(
        returns
    ) >= 2:


        recent_returns = (
            returns[-20:]
        )


        if len(
            recent_returns
        ) >= 2:


            daily_volatility = float(

                np.std(
                    recent_returns,
                    ddof=1,
                )

            )


            annualised_volatility_pct = (

                daily_volatility
                *
                math.sqrt(
                    252
                )
                *
                100

            )


    # ========================================================
    # 7.5 14-DAY AVERAGE TRUE RANGE
    # ========================================================

    true_ranges = []


    for index in range(
        len(
            data
        )
    ):


        high = float(
            highs[
                index
            ]
        )


        low = float(
            lows[
                index
            ]
        )


        # ----------------------------------------------------
        # First observation
        # ----------------------------------------------------

        if index == 0:

            true_range = (

                high
                -
                low

            )


        # ----------------------------------------------------
        # Subsequent observations
        # ----------------------------------------------------

        else:

            previous_close = float(

                closes[
                    index - 1
                ]

            )


            true_range = max(

                high
                -
                low,

                abs(
                    high
                    -
                    previous_close
                ),

                abs(
                    low
                    -
                    previous_close
                ),

            )


        true_ranges.append(
            true_range
        )


    atr_14 = None


    if true_ranges:

        recent_true_ranges = (
            true_ranges[-14:]
        )


        atr_14 = (

            sum(
                recent_true_ranges
            )
            /
            len(
                recent_true_ranges
            )

        )


    # ========================================================
    # 7.6 30-DAY HIGH / LOW
    # ========================================================

    recent_highs = (
        highs[-30:]
    )


    recent_lows = (
        lows[-30:]
    )


    high_30 = float(

        np.max(
            recent_highs
        )

    )


    low_30 = float(

        np.min(
            recent_lows
        )

    )


    # ========================================================
    # 7.7 HISTORICAL MAXIMUM DRAWDOWN
    # ========================================================

    running_peak = float(
        closes[0]
    )


    maximum_drawdown = 0.0


    for close in closes:


        close = float(
            close
        )


        # Update highest observed price.
        running_peak = max(
            running_peak,
            close,
        )


        if running_peak > 0:


            drawdown = (

                close
                /
                running_peak
                -
                1

            )


            maximum_drawdown = min(
                maximum_drawdown,
                drawdown,
            )


    # Store drawdown as a positive percentage.
    #
    # Example:
    #
    # raw drawdown = -0.25
    #
    # displayed maximum drawdown = 25%

    maximum_drawdown_pct = (

        abs(
            maximum_drawdown
        )
        *
        100

    )


    # ========================================================
    # 7.8 RETURN COMPLETE HISTORICAL CONTEXT
    # ========================================================

    return {

        "symbol":
            symbol,


        "latest_close":
            round(
                latest_close,
                4,
            ),


        "latest_date":
            data[-1][
                "date"
            ].isoformat(),


        "observations":
            len(
                data
            ),


        "atr_14":
            (
                round(
                    atr_14,
                    4,
                )

                if atr_14 is not None

                else None
            ),


        "annualised_volatility_pct":
            (
                round(
                    annualised_volatility_pct,
                    2,
                )

                if annualised_volatility_pct is not None

                else None
            ),


        "high_30":
            round(
                high_30,
                4,
            ),


        "low_30":
            round(
                low_30,
                4,
            ),


        "maximum_drawdown_pct":
            round(
                maximum_drawdown_pct,
                2,
            ),
    }


# ============================================================
# 8. ENHANCED TRADE RISK PLAN
# ============================================================

def calculate_trade_risk_plan(
    trading_capital,
    risk_percentage,
    entry_price,
    direction,
    stop_method,
    stop_loss_percentage=None,
    fixed_stop_price=None,
    atr=None,
    atr_multiplier=None,
    target_price=None,
):
    """
    ============================================================
    TRADE RISK PLAN
    ============================================================

    Main risk engine used by the redesigned MarketPulse Risk tab.


    EXAMPLE USER INPUT:

        Trading capital:
            10,000

        Maximum risk:
            1%

        Entry:
            100

        Stop:
            5%

        Target:
            110


    CALCULATIONS:

        Maximum risk budget
            = 10,000 × 1%
            = 100

        Stop price
            = 100 - 5%
            = 95

        Risk per unit
            = 100 - 95
            = 5

        Position size
            = 100 / 5
            = 20 units

        Position value
            = 20 × 100
            = 2,000

        Potential loss
            = 20 × 5
            = 100

        Potential reward
            = 20 × 10
            = 200

        Reward / Risk
            = 200 / 100
            = 2 : 1


    IMPORTANT:

    risk_percentage uses HUMAN-READABLE percentages.

        1 = 1%
        2 = 2%

    stop_loss_percentage also uses human-readable percentages.

        5 = 5%


    POSITION-SIZING CONSTRAINTS:

    1. Risk budget
    2. Available trading capital

    This educational implementation assumes no leverage.
    ============================================================
    """


    # ========================================================
    # 8.1 NORMALISE VALUES
    # ========================================================

    trading_capital = float(
        trading_capital
    )


    risk_percentage = float(
        risk_percentage
    )


    entry_price = float(
        entry_price
    )


    direction = (
        str(direction)
        .strip()
        .lower()
    )


    stop_method = (
        str(stop_method)
        .strip()
        .lower()
    )


    # ========================================================
    # 8.2 VALIDATE CORE INPUTS
    # ========================================================

    if trading_capital <= 0:

        raise ValueError(
            "Trading capital must be greater than zero."
        )


    if entry_price <= 0:

        raise ValueError(
            "Entry price must be greater than zero."
        )


    if risk_percentage <= 0:

        raise ValueError(
            "Risk percentage must be greater than zero."
        )


    if risk_percentage > 100:

        raise ValueError(
            "Risk percentage cannot exceed 100%."
        )


    if direction not in {
        "long",
        "short",
    }:

        raise ValueError(
            "Trade direction must be either long or short."
        )


    if stop_method not in {
        "percentage",
        "atr",
        "fixed",
    }:

        raise ValueError(
            "Unknown stop-loss method."
        )


    # ========================================================
    # 8.3 MAXIMUM RISK BUDGET
    # ========================================================

    maximum_risk_amount = (

        trading_capital
        *
        (
            risk_percentage
            /
            100
        )

    )


    # ========================================================
    # 9. STOP-LOSS CALCULATION
    # ========================================================

    stop_price = None

    stop_distance_amount = None

    stop_distance_percentage = None


    # ========================================================
    # 9.1 PERCENTAGE-BASED STOP
    # ========================================================

    if stop_method == "percentage":


        if stop_loss_percentage is None:

            raise ValueError(
                "A stop-loss percentage is required."
            )


        stop_loss_percentage = float(
            stop_loss_percentage
        )


        if stop_loss_percentage <= 0:

            raise ValueError(
                "Stop-loss percentage must be greater than zero."
            )


        if stop_loss_percentage >= 100:

            raise ValueError(
                "Stop-loss percentage must be less than 100%."
            )


        stop_distance_percentage = (
            stop_loss_percentage
        )


        stop_distance_amount = (

            entry_price
            *
            (
                stop_loss_percentage
                /
                100
            )

        )


        if direction == "long":

            stop_price = (

                entry_price
                -
                stop_distance_amount

            )


        else:

            stop_price = (

                entry_price
                +
                stop_distance_amount

            )


    # ========================================================
    # 9.2 ATR-BASED STOP
    # ========================================================

    elif stop_method == "atr":


        if atr is None:

            raise ValueError(
                "ATR is unavailable for this asset. "
                "Import historical OHLCV data first or use "
                "a percentage/fixed-price stop."
            )


        atr = float(
            atr
        )


        if atr <= 0:

            raise ValueError(
                "ATR must be greater than zero."
            )


        multiplier = float(

            atr_multiplier

            if atr_multiplier is not None

            else 2

        )


        if multiplier <= 0:

            raise ValueError(
                "ATR multiplier must be greater than zero."
            )


        stop_distance_amount = (

            atr
            *
            multiplier

        )


        stop_distance_percentage = (

            stop_distance_amount
            /
            entry_price
            *
            100

        )


        if direction == "long":

            stop_price = (

                entry_price
                -
                stop_distance_amount

            )


        else:

            stop_price = (

                entry_price
                +
                stop_distance_amount

            )


    # ========================================================
    # 9.3 FIXED STOP PRICE
    # ========================================================

    elif stop_method == "fixed":


        if fixed_stop_price is None:

            raise ValueError(
                "A fixed stop price is required."
            )


        stop_price = float(
            fixed_stop_price
        )


        if stop_price <= 0:

            raise ValueError(
                "Fixed stop price must be greater than zero."
            )


        stop_distance_amount = abs(

            entry_price
            -
            stop_price

        )


        stop_distance_percentage = (

            stop_distance_amount
            /
            entry_price
            *
            100

        )


    # ========================================================
    # 10. VALIDATE STOP DIRECTION
    # ========================================================

    if (
        direction == "long"
        and
        stop_price >= entry_price
    ):

        raise ValueError(
            "For a long position, the stop price must "
            "be below the entry price."
        )


    if (
        direction == "short"
        and
        stop_price <= entry_price
    ):

        raise ValueError(
            "For a short position, the stop price must "
            "be above the entry price."
        )


    if stop_price <= 0:

        raise ValueError(
            "Calculated stop price must be greater than zero."
        )


    # ========================================================
    # 11. RISK PER SHARE / UNIT
    # ========================================================

    risk_per_unit = abs(

        entry_price
        -
        stop_price

    )


    if risk_per_unit <= 0:

        raise ValueError(
            "Stop price must be different from entry price."
        )


    # ========================================================
    # 12. RISK-BASED POSITION SIZE
    # ========================================================

    risk_based_quantity = math.floor(

        maximum_risk_amount
        /
        risk_per_unit

    )


    # ========================================================
    # 13. CAPITAL-CONSTRAINED POSITION SIZE
    # ========================================================

    # This assumes no leverage.
    #
    # Example:
    #
    # Capital = 10,000
    # Entry = 100
    #
    # Maximum affordable whole units = 100.

    capital_limited_quantity = math.floor(

        trading_capital
        /
        entry_price

    )


    # ========================================================
    # 14. FINAL POSITION SIZE
    # ========================================================

    quantity = min(

        risk_based_quantity,

        capital_limited_quantity,

    )


    quantity = max(
        quantity,
        0,
    )


    # ========================================================
    # 15. IDENTIFY LIMITING CONSTRAINT
    # ========================================================

    capital_cap_applied = (

        capital_limited_quantity
        <
        risk_based_quantity

    )


    # ========================================================
    # 16. POSITION VALUE
    # ========================================================

    position_value = (

        quantity
        *
        entry_price

    )


    # ========================================================
    # 17. CAPITAL ALLOCATION
    # ========================================================

    capital_allocation_pct = (

        position_value
        /
        trading_capital
        *
        100

    )


    # ========================================================
    # 18. ACTUAL PLANNED LOSS
    # ========================================================

    # Because MarketPulse currently uses whole-unit position
    # sizing, this amount may be slightly smaller than the
    # requested maximum risk budget.

    planned_loss = (

        quantity
        *
        risk_per_unit

    )


    actual_risk_percentage = (

        planned_loss
        /
        trading_capital
        *
        100

        if trading_capital > 0

        else 0

    )


    # ========================================================
    # 19. TARGET / POTENTIAL REWARD
    # ========================================================

    potential_reward = None

    reward_per_unit = None

    reward_risk_ratio = None


    if target_price is not None:


        target_price = float(
            target_price
        )


        if target_price <= 0:

            raise ValueError(
                "Target price must be greater than zero."
            )


        # ----------------------------------------------------
        # Validate long target
        # ----------------------------------------------------

        if (
            direction == "long"
            and
            target_price <= entry_price
        ):

            raise ValueError(
                "For a long position, the target price must "
                "be above the entry price."
            )


        # ----------------------------------------------------
        # Validate short target
        # ----------------------------------------------------

        if (
            direction == "short"
            and
            target_price >= entry_price
        ):

            raise ValueError(
                "For a short position, the target price must "
                "be below the entry price."
            )


        # ----------------------------------------------------
        # Reward per share/unit
        # ----------------------------------------------------

        if direction == "long":

            reward_per_unit = (

                target_price
                -
                entry_price

            )


        else:

            reward_per_unit = (

                entry_price
                -
                target_price

            )


        # ----------------------------------------------------
        # Total potential reward
        # ----------------------------------------------------

        potential_reward = (

            reward_per_unit
            *
            quantity

        )


        # ----------------------------------------------------
        # Reward / Risk
        # ----------------------------------------------------

        if planned_loss > 0:

            reward_risk_ratio = (

                potential_reward
                /
                planned_loss

            )


    # ========================================================
    # 20. ATR RELATIONSHIP
    # ========================================================

    stop_atr_multiple = None


    if atr is not None:


        atr_value = float(
            atr
        )


        if atr_value > 0:

            stop_atr_multiple = (

                risk_per_unit
                /
                atr_value

            )


    # ========================================================
    # 21. POSITION STATUS
    # ========================================================

    if quantity <= 0:

        position_status = (
            "The selected risk budget and stop distance do not "
            "allow the purchase of one whole unit."
        )


    elif capital_cap_applied:

        position_status = (
            "Available trading capital is the limiting factor "
            "for this position size."
        )


    else:

        position_status = (
            "The position size is constrained by the selected "
            "maximum risk budget."
        )


    # ========================================================
    # 22. REWARD / RISK INTERPRETATION
    # ========================================================

    reward_risk_status = None


    if reward_risk_ratio is not None:


        if reward_risk_ratio >= 2:

            reward_risk_status = (
                "The potential reward is at least twice the "
                "planned risk in this simulation."
            )


        elif reward_risk_ratio >= 1:

            reward_risk_status = (
                "Potential reward exceeds planned risk, but "
                "the margin is below 2:1."
            )


        else:

            reward_risk_status = (
                "Potential reward is smaller than the planned "
                "risk based on the selected target and stop."
            )


    # ========================================================
    # 23. RETURN COMPLETE PLAN
    # ========================================================

    return {

        # ----------------------------------------------------
        # Risk budget
        # ----------------------------------------------------

        "maximum_risk_amount":
            round(
                maximum_risk_amount,
                2,
            ),


        "requested_risk_percentage":
            round(
                risk_percentage,
                2,
            ),


        "actual_risk_percentage":
            round(
                actual_risk_percentage,
                2,
            ),


        # ----------------------------------------------------
        # Entry
        # ----------------------------------------------------

        "entry_price":
            round(
                entry_price,
                4,
            ),


        # ----------------------------------------------------
        # Stop
        # ----------------------------------------------------

        "stop_price":
            round(
                stop_price,
                4,
            ),


        "stop_distance_amount":
            round(
                stop_distance_amount,
                4,
            ),


        "stop_distance_percentage":
            round(
                stop_distance_percentage,
                2,
            ),


        "stop_method":
            stop_method,


        # ----------------------------------------------------
        # Direction
        # ----------------------------------------------------

        "direction":
            direction,


        # ----------------------------------------------------
        # Risk per unit
        # ----------------------------------------------------

        "risk_per_unit":
            round(
                risk_per_unit,
                4,
            ),


        # ----------------------------------------------------
        # Position quantities
        # ----------------------------------------------------

        "risk_based_quantity":
            risk_based_quantity,


        "capital_limited_quantity":
            capital_limited_quantity,


        "quantity":
            quantity,


        # ----------------------------------------------------
        # Position value
        # ----------------------------------------------------

        "position_value":
            round(
                position_value,
                2,
            ),


        # ----------------------------------------------------
        # Capital allocation
        # ----------------------------------------------------

        "capital_allocation_pct":
            round(
                capital_allocation_pct,
                2,
            ),


        # ----------------------------------------------------
        # Planned loss
        # ----------------------------------------------------

        "planned_loss":
            round(
                planned_loss,
                2,
            ),


        # ----------------------------------------------------
        # Target
        # ----------------------------------------------------

        "target_price":
            (
                round(
                    target_price,
                    4,
                )

                if target_price is not None

                else None
            ),


        # ----------------------------------------------------
        # Reward
        # ----------------------------------------------------

        "reward_per_unit":
            (
                round(
                    reward_per_unit,
                    4,
                )

                if reward_per_unit is not None

                else None
            ),


        "potential_reward":
            (
                round(
                    potential_reward,
                    2,
                )

                if potential_reward is not None

                else None
            ),


        # ----------------------------------------------------
        # Reward / Risk
        # ----------------------------------------------------

        "reward_risk_ratio":
            (
                round(
                    reward_risk_ratio,
                    2,
                )

                if reward_risk_ratio is not None

                else None
            ),


        "reward_risk_status":
            reward_risk_status,


        # ----------------------------------------------------
        # Constraints
        # ----------------------------------------------------

        "capital_cap_applied":
            capital_cap_applied,


        "position_status":
            position_status,


        # ----------------------------------------------------
        # ATR context
        # ----------------------------------------------------

        "stop_atr_multiple":
            (
                round(
                    stop_atr_multiple,
                    2,
                )

                if stop_atr_multiple is not None

                else None
            ),
    }


# ============================================================
# 24. SIMPLE STRESS-IMPACT CALCULATOR
# ============================================================

def calculate_position_stress_impact(
    position_value,
    trading_capital,
    shock_percentage,
):
    """
    ============================================================
    SIMPLE POSITION STRESS IMPACT
    ============================================================

    Calculates the direct financial effect of a percentage
    market shock on a hypothetical position.

    This is useful for the Risk tab's simple explanatory
    stress-test summaries.

    More advanced historical scenario simulation remains in:

        analysis_tools/analyzers.py


    Example:

        Position value = 4,000
        Trading capital = 10,000
        Shock = 10%

    Result:

        Estimated position loss = 400
        Portfolio impact = 4%
    ============================================================
    """


    position_value = float(
        position_value
    )


    trading_capital = float(
        trading_capital
    )


    shock_percentage = float(
        shock_percentage
    )


    if position_value < 0:

        raise ValueError(
            "Position value cannot be negative."
        )


    if trading_capital <= 0:

        raise ValueError(
            "Trading capital must be greater than zero."
        )


    if shock_percentage < 0:

        raise ValueError(
            "Shock percentage cannot be negative."
        )


    if shock_percentage > 100:

        raise ValueError(
            "Shock percentage cannot exceed 100%."
        )


    # --------------------------------------------------------
    # Estimated loss
    # --------------------------------------------------------

    estimated_loss = (

        position_value
        *
        (
            shock_percentage
            /
            100
        )

    )


    # --------------------------------------------------------
    # Stressed position value
    # --------------------------------------------------------

    stressed_position_value = max(

        position_value
        -
        estimated_loss,

        0,

    )


    # --------------------------------------------------------
    # Impact on total capital
    # --------------------------------------------------------

    portfolio_impact_pct = (

        estimated_loss
        /
        trading_capital
        *
        100

    )


    return {

        "shock_percentage":
            round(
                shock_percentage,
                2,
            ),


        "position_value":
            round(
                position_value,
                2,
            ),


        "stressed_position_value":
            round(
                stressed_position_value,
                2,
            ),


        "estimated_loss":
            round(
                estimated_loss,
                2,
            ),


        "portfolio_impact_pct":
            round(
                portfolio_impact_pct,
                2,
            ),
    }