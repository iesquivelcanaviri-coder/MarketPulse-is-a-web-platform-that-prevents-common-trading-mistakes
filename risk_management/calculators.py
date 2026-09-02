"""
============================================================
MARKETPULSE - RISK CALCULATORS
============================================================

Framework mapping:

Data tab
    ↓
core.MarketData
    ↓
risk_management/calculators.py
    ↓
risk_management/views.py
    ↓
Trade & Portfolio Risk Planner


PURPOSE:

This module contains the calculation logic used by the
MarketPulse Risk area.

It deliberately keeps financial calculations outside the
Django templates so that the same functions can later be
reused by:

- Django views
- REST API endpoints
- Backtesting
- Strategy testing
- Portfolio analysis
- React components
- Stress testing


IMPORTANT:

Two groups of functions are kept in this file:

1. ORIGINAL / COMPATIBILITY FUNCTIONS
   These remain available because existing parts of
   MarketPulse may already import them.

2. ENHANCED RISK-PLANNER FUNCTIONS
   These support the redesigned Trade & Portfolio Risk page.

============================================================
"""


# ============================================================
# 1. IMPORTS
# ============================================================

import math

import numpy as np

from core.models import MarketData


# ============================================================
# 2. ORIGINAL POSITION SIZE CALCULATOR
# ============================================================

def calculate_position_size(
    account_balance,
    risk_percentage,
    stop_loss_pct,
    entry_price,
):
    """
    ============================================================
    ORIGINAL POSITION SIZE CALCULATOR
    ============================================================

    This function is preserved for backward compatibility
    with existing MarketPulse views and API endpoints.

    IMPORTANT:

    This original function expects percentages as decimal
    proportions.

    Example:

        account_balance = 10000
        risk_percentage = 0.01
        stop_loss_pct = 0.05
        entry_price = 100

    This represents:

        1% account risk
        5% stop-loss

    The redesigned Trade Risk Planner uses a more explicit
    calculation function later in this file where the user
    can enter:

        1 = 1%
        5 = 5%
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

    if min(
        account_balance,
        risk_percentage,
        stop_loss_pct,
        entry_price,
    ) <= 0:

        raise ValueError(
            "All values must be greater than zero."
        )


    # --------------------------------------------------------
    # Position-size formula
    # --------------------------------------------------------

    position_size = (

        account_balance
        *
        risk_percentage

    ) / (

        entry_price
        *
        stop_loss_pct

    )


    return position_size


# ============================================================
# 3. ORIGINAL STOP-LOSS CALCULATOR
# ============================================================

def calculate_stop_loss(
    entry_price,
    stop_loss_pct=0.05,
):
    """
    Calculates a percentage stop-loss below the entry price.

    This original helper assumes a LONG position.

    Example:

        Entry = 100
        Stop = 5%

        Stop price = 95
    """

    entry_price = float(
        entry_price
    )

    stop_loss_pct = float(
        stop_loss_pct
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
    Calculates the reward-to-risk ratio.

    Example:

        Entry = 100
        Stop = 95
        Target = 110

        Risk = 5
        Reward = 10

        Reward / Risk = 2.0
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

        return 0


    return (
        reward
        /
        risk
    )


# ============================================================
# 5. ORIGINAL HISTORICAL VOLATILITY CALCULATOR
# ============================================================

def calculate_volatility(
    symbol,
    period=60,
):
    """
    ============================================================
    HISTORICAL VOLATILITY
    ============================================================

    Reads Close prices from core.MarketData.

    Steps:

    1. Retrieve historical closing prices.
    2. Calculate daily percentage returns.
    3. Calculate daily return standard deviation.
    4. Annualise using sqrt(252).

    The returned value is a DECIMAL.

    Example:

        0.25 = approximately 25% annualised volatility.
    ============================================================
    """


    close_prices = list(

        MarketData.objects
        .filter(
            symbol=symbol.upper()
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
    # Need sufficient observations
    # --------------------------------------------------------

    if len(close_prices) < 3:

        return 0.0


    # --------------------------------------------------------
    # Convert Decimal database values to floats
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
    # Daily simple returns
    # --------------------------------------------------------

    returns = (

        np.diff(
            prices
        )
        /
        prices[:-1]

    )


    if len(returns) <= 1:

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
# 6. ORIGINAL VOLATILITY-ADJUSTED RISK
# ============================================================

def volatility_adjusted_risk(
    base,
    vol,
):
    """
    Reduces a base risk amount when volatility increases.

    This original function is kept because other parts of
    MarketPulse may already depend on its behaviour.
    """

    base = float(
        base
    )

    vol = float(
        vol
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

    Connects historical data imported through the Data tab
    directly to the Risk tab.

    MarketPulse calculates:

    - Latest stored close
    - Latest stored date
    - Number of observations
    - 14-day Average True Range (ATR)
    - 20-day annualised historical volatility
    - 30-day high
    - 30-day low
    - Historical maximum drawdown


    Framework mapping:

    Yahoo Finance
        ↓
    Data tab
        ↓
    core.MarketData
        ↓
    get_market_risk_context()
        ↓
    Risk Planner


    Parameters
    ----------

    symbol:
        Market ticker such as AAPL, MSFT or SPY.


    Returns
    -------

    Dictionary containing calculated market-risk information.

    Returns None if no historical observations exist.
    ============================================================
    """


    # --------------------------------------------------------
    # Standardise ticker
    # --------------------------------------------------------

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )


    # --------------------------------------------------------
    # Retrieve historical data in chronological order
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


    # --------------------------------------------------------
    # No data available
    # --------------------------------------------------------

    if not data:

        return None


    # ========================================================
    # 7.1 CONVERT DATABASE VALUES TO FLOATS
    # ========================================================

    closes = np.array(

        [
            float(
                row["close_price"]
            )
            for row in data
        ],

        dtype=float,
    )


    highs = np.array(

        [
            float(
                row["high_price"]
            )
            for row in data
        ],

        dtype=float,
    )


    lows = np.array(

        [
            float(
                row["low_price"]
            )
            for row in data
        ],

        dtype=float,
    )


    # ========================================================
    # 7.2 LATEST CLOSE
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


        # Avoid division by zero.
        valid_mask = (
            previous_prices
            !=
            0
        )


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
        len(data)
    ):


        high = float(
            highs[index]
        )


        low = float(
            lows[index]
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
        # Remaining observations
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
    # 7.6 30-DAY PRICE RANGE
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


        # ----------------------------------------------------
        # Update historical peak
        # ----------------------------------------------------

        running_peak = max(
            running_peak,
            close,
        )


        # ----------------------------------------------------
        # Calculate drawdown from historical peak
        # ----------------------------------------------------

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


    maximum_drawdown_pct = (

        abs(
            maximum_drawdown
        )
        *
        100

    )


    # ========================================================
    # 7.8 RETURN MARKET CONTEXT
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
                if annualised_volatility_pct
                is not None
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

    Main calculation engine used by the redesigned Risk tab.


    USER INPUT EXAMPLE:

        Trading Capital:
            10,000

        Maximum Risk:
            1%

        Entry:
            100

        Stop:
            5%

        Target:
            110


    MARKETPULSE THEN CALCULATES:

        Maximum risk amount
            = 100

        Stop price
            = 95

        Risk per share
            = 5

        Position size
            = 20 shares

        Position value
            = 2,000

        Potential loss
            = 100

        Potential reward
            = 200

        Reward / Risk
            = 2 : 1


    IMPORTANT:

    The risk_percentage parameter uses the human-readable
    percentage entered on the form:

        1 means 1%
        2 means 2%

    This is intentionally different from the older
    calculate_position_size() helper.


    The calculation also assumes no leverage.

    Therefore position size is constrained by:

    1. Maximum acceptable risk.
    2. Total available trading capital.

    ============================================================
    """


    # ========================================================
    # 8.1 CONVERT VALUES
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
    # 8.2 VALIDATE BASE VALUES
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
            "Trade direction must be long or short."
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
    # 9.1 PERCENTAGE STOP
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


        # ----------------------------------------------------
        # Long position
        # ----------------------------------------------------

        if direction == "long":

            stop_price = (

                entry_price
                -
                stop_distance_amount

            )


        # ----------------------------------------------------
        # Short position
        # ----------------------------------------------------

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
                "ATR could not be calculated for this dataset."
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
    # 9.4 UNKNOWN METHOD
    # ========================================================

    else:

        raise ValueError(
            "Unknown stop-loss method."
        )


    # ========================================================
    # 10. VALIDATE STOP DIRECTION
    # ========================================================

    if (
        direction == "long"
        and stop_price >= entry_price
    ):

        raise ValueError(
            "For a long position, the stop price must "
            "be below the entry price."
        )


    if (
        direction == "short"
        and stop_price <= entry_price
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

    # Example:
    #
    # Capital = 10,000
    # Entry = 100
    #
    # Maximum affordable position = 100 units.
    #
    # This educational version assumes no leverage.

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


    # --------------------------------------------------------
    # Identify whether capital, rather than risk, limited
    # the resulting position.
    # --------------------------------------------------------

    capital_cap_applied = (

        capital_limited_quantity
        <
        risk_based_quantity

    )


    # ========================================================
    # 15. POSITION VALUE
    # ========================================================

    position_value = (

        quantity
        *
        entry_price

    )


    # ========================================================
    # 16. CAPITAL ALLOCATION
    # ========================================================

    capital_allocation_pct = (

        position_value
        /
        trading_capital
        *
        100

    )


    # ========================================================
    # 17. ACTUAL PLANNED LOSS
    # ========================================================

    # Whole-unit rounding means actual planned loss may be
    # slightly below the maximum requested risk amount.

    planned_loss = (

        quantity
        *
        risk_per_unit

    )


    # ========================================================
    # 18. TARGET / POTENTIAL REWARD
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
        # Validate target for long trade
        # ----------------------------------------------------

        if (
            direction == "long"
            and target_price <= entry_price
        ):

            raise ValueError(
                "For a long position, the target price "
                "must be above the entry price."
            )


        # ----------------------------------------------------
        # Validate target for short trade
        # ----------------------------------------------------

        if (
            direction == "short"
            and target_price >= entry_price
        ):

            raise ValueError(
                "For a short position, the target price "
                "must be below the entry price."
            )


        # ----------------------------------------------------
        # Reward per unit
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
    # 19. STOP DISTANCE IN ATR UNITS
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
    # 20. POSITION-SIZING STATUS
    # ========================================================

    # Useful explanatory text for the Risk UI.

    if quantity <= 0:

        position_status = (
            "The current risk budget is too small to purchase "
            "one whole unit at the selected stop distance."
        )


    elif capital_cap_applied:

        position_status = (
            "The position size is limited by available trading "
            "capital rather than the risk budget."
        )


    else:

        position_status = (
            "The position size is constrained by the selected "
            "maximum risk budget."
        )


    # ========================================================
    # 21. RETURN COMPLETE RISK PLAN
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


        # ----------------------------------------------------
        # Risk per unit
        # ----------------------------------------------------

        "risk_per_unit":
            round(
                risk_per_unit,
                4,
            ),


        # ----------------------------------------------------
        # Quantities
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
        # Potential reward
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
        # Reward/risk ratio
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


        # ----------------------------------------------------
        # Position constraint information
        # ----------------------------------------------------

        "capital_cap_applied":
            capital_cap_applied,


        "position_status":
            position_status,


        # ----------------------------------------------------
        # ATR relationship
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