"""
============================================================
MARKETPULSE - RISK CALCULATORS
============================================================
PURPOSE:
Reusable position sizing, stop, reward/risk, historical risk,
and simple position-shock calculations.
FRAMEWORK:
core.MarketData → historical metrics → risk views → templates.
Validated form inputs → trade risk plan → risk views → templates.
Advanced stress scenarios remain in analysis_tools/analyzers.py.
PERCENTAGE CONVENTIONS:
Older helpers: 0.01 means 1%; 0.05 means 5%.
Main trade planner: 1 means 1%; 5 means 5%.
LECTURE:
Functions, parameters, default arguments, variables, arithmetic,
conditions, loops, comprehensions, slicing, arrays, dictionaries,
exceptions, and return values.
============================================================
"""  # Module docstring: explain the module's purpose.

# ============================================================
# 1. IMPORTS
# ============================================================
import math  # Import Python's mathematical tools, including sqrt() and floor().
import numpy as np  # Import NumPy using the shorter alias np.
from core.models import MarketData  # Import the Django model containing historical prices.

# ============================================================
# 2. ORIGINAL POSITION-SIZE CALCULATOR
# ============================================================
def calculate_position_size(  # Define a reusable function.
    account_balance,  # Parameter: total account capital.
    risk_percentage,  # Parameter: risk fraction; 0.01 means 1%.
    stop_loss_pct,  # Parameter: stop-distance fraction; 0.05 means 5%.
    entry_price,  # Parameter: price of one unit.
):  # Finish the function signature.
    """Compatibility helper: calculate quantity using decimal risk fractions."""  # Function documentation.
    account_balance = float(account_balance)  # Convert the balance to a floating-point number.
    risk_percentage = float(risk_percentage)  # Convert the risk fraction to float.
    stop_loss_pct = float(stop_loss_pct)  # Convert the stop fraction to float.
    entry_price = float(entry_price)  # Convert the entry price to float.

    # --------------------------------------------------------
    # 2.1 VALIDATE INPUTS
    # --------------------------------------------------------
    if account_balance <= 0:  # Comparison: reject a non-positive balance.
        raise ValueError("Account balance must be greater than zero.")  # Raise the original input error.
    if risk_percentage <= 0:  # Reject a non-positive risk fraction.
        raise ValueError("Risk percentage must be greater than zero.")  # Raise the original error.
    if stop_loss_pct <= 0:  # Reject a non-positive stop fraction.
        raise ValueError("Stop-loss percentage must be greater than zero.")  # Raise the original error.
    if entry_price <= 0:  # Reject a non-positive entry price.
        raise ValueError("Entry price must be greater than zero.")  # Raise the original error.

    # --------------------------------------------------------
    # 2.2 CALCULATE QUANTITY
    # --------------------------------------------------------
    risk_amount = account_balance * risk_percentage  # Multiplication: calculate the monetary risk budget.
    risk_per_unit = entry_price * stop_loss_pct  # Calculate the assumed loss per unit at the stop.
    return risk_amount / risk_per_unit  # Division: return quantity; this helper does not round to whole units.

# ============================================================
# 3. ORIGINAL LONG-POSITION STOP CALCULATOR
# ============================================================
def calculate_stop_loss(  # Define the compatibility stop-price function.
    entry_price,  # Parameter: the entry price.
    stop_loss_pct=0.05,  # Default argument: use a 5% stop fraction when omitted.
):  # Finish the signature.
    """Calculate a long-position stop using a decimal stop fraction."""  # Function documentation.
    entry_price = float(entry_price)  # Convert the entry price to float.
    stop_loss_pct = float(stop_loss_pct)  # Convert the stop fraction to float.
    if entry_price <= 0:  # Validate the entry price.
        raise ValueError("Entry price must be greater than zero.")  # Raise the original error.
    if stop_loss_pct <= 0:  # Validate the lower stop-fraction bound.
        raise ValueError("Stop-loss percentage must be greater than zero.")  # Raise the original error.
    if stop_loss_pct >= 1:  # Require a stop fraction below one.
        raise ValueError(  # Construct the original explanatory error.
            "This compatibility function expects the "  # First part of the message.
            "stop-loss as a decimal below 1. "  # Adjacent string literals join automatically.
            "For example, use 0.05 for 5%."  # Finish the message.
        )  # Close the error constructor.
    return entry_price * (1 - stop_loss_pct)  # Arithmetic: place the stop below entry.

# ============================================================
# 4. ORIGINAL REWARD / RISK RATIO
# ============================================================
def calculate_risk_reward_ratio(  # Define a reusable ratio helper.
    entry,  # Parameter: entry price.
    stop,  # Parameter: stop price.
    target,  # Parameter: target price.
):  # Finish the signature.
    """Return absolute target distance divided by absolute stop distance."""  # Function documentation.
    entry = float(entry)  # Convert entry to float.
    stop = float(stop)  # Convert stop to float.
    target = float(target)  # Convert target to float.
    risk = abs(entry - stop)  # Absolute value: calculate the unsigned stop distance.
    reward = abs(target - entry)  # Calculate the unsigned target distance.
    if risk == 0:  # Equality comparison: avoid division by zero.
        return 0.0  # Early return: preserve the zero-risk result.
    return float(reward / risk)  # Return the ratio; this helper does not validate trade direction.

# ============================================================
# 5. HISTORICAL VOLATILITY
# ============================================================
def calculate_volatility(  # Define a historical volatility function.
    symbol,  # Parameter: the asset symbol.
    period=60,  # Default argument: request up to 60 return intervals.
):  # Finish the signature.
    """Calculate annualised volatility from stored close-to-close returns."""  # Function documentation.
    symbol = str(symbol).strip().upper()  # Method chaining: convert to text, trim spaces, and uppercase.

    # --------------------------------------------------------
    # 5.1 NORMALISE THE PERIOD
    # --------------------------------------------------------
    try:  # Exception handling: attempt integer conversion.
        period = int(period)  # Convert the requested period to an integer.
    except (TypeError, ValueError):  # Catch the two original conversion-error types.
        period = 60  # Use the original fallback period.
    period = max(period, 2)  # Ensure the requested period is at least two.

    # --------------------------------------------------------
    # 5.2 RETRIEVE RECENT CLOSES
    # --------------------------------------------------------
    close_prices = list(  # Evaluate the query and store its values in a list.
        MarketData.objects  # Access the model's database manager.
        .filter(symbol=symbol)  # Keep records for the selected symbol.
        .order_by("-date")  # Order newest observations first.
        .values_list("close_price", flat=True)[:period + 1]  # Retrieve enough prices for up to period returns.
    )  # Close the list conversion.
    if len(close_prices) < 3:  # Require at least three prices.
        return 0.0  # Return the original insufficient-data value.
    prices = np.array(  # Construct a NumPy array.
        [float(price) for price in reversed(close_prices)],  # Comprehension: convert prices and restore chronological order.
        dtype=float,  # Keyword argument: use floating-point array values.
    )  # Close the array constructor.

    # --------------------------------------------------------
    # 5.3 CALCULATE VALID RETURNS
    # --------------------------------------------------------
    previous_prices = prices[:-1]  # Slice: take every price except the last.
    current_prices = prices[1:]  # Slice: take every price except the first.
    valid_mask = previous_prices > 0  # Array comparison: mark intervals whose previous price is positive.
    if np.count_nonzero(valid_mask) < 2:  # Count intervals allowed by the mask.
        return 0.0  # Return when fewer than two valid intervals exist.
    returns = current_prices[valid_mask] / previous_prices[valid_mask] - 1  # Boolean indexing and arithmetic: calculate fractional returns.
    if len(returns) < 2:  # Preserve the additional return-count check.
        return 0.0  # Return the original insufficient-return value.

    # --------------------------------------------------------
    # 5.4 ANNUALISE VOLATILITY
    # --------------------------------------------------------
    annualised_volatility = np.std(returns, ddof=1) * math.sqrt(252)  # Sample standard deviation scaled using the 252-session assumption.
    return float(annualised_volatility)  # Return a Python float fraction; 0.25 represents 25%.

# ============================================================
# 6. VOLATILITY-ADJUSTED RISK
# ============================================================
def volatility_adjusted_risk(  # Define the threshold-based adjustment helper.
    base,  # Parameter: the original risk amount.
    vol,  # Parameter: volatility as a fraction.
):  # Finish the signature.
    """Reduce a base risk amount using the existing volatility thresholds."""  # Function documentation.
    base = float(base)  # Convert the risk amount to float.
    vol = float(vol)  # Convert volatility to float.
    if base < 0:  # Reject a negative base amount.
        raise ValueError("Base risk cannot be negative.")  # Raise the original error.
    if vol < 0:  # Reject negative volatility.
        raise ValueError("Volatility cannot be negative.")  # Raise the original error.
    if vol >= 0.50:  # Check the highest threshold first.
        return base * 0.50  # Return half the base risk.
    if vol >= 0.30:  # Check the next threshold if the previous branch did not return.
        return base * 0.70  # Return 70% of base risk.
    if vol >= 0.20:  # Check the remaining adjustment threshold.
        return base * 0.85  # Return 85% of base risk.
    return base  # Return the unchanged amount below these thresholds.

# ============================================================
# 7. HISTORICAL MARKET RISK CONTEXT
# ============================================================
def get_market_risk_context(  # Define the historical risk-summary function.
    symbol,  # Parameter: the asset symbol.
):  # Finish the signature.
    """Return historical price metrics, or None when no matching data exists."""  # Function documentation.
    symbol = str(symbol).strip().upper()  # Normalise the symbol text.
    if not symbol:  # Boolean negation: check for an empty symbol.
        return None  # Early return: no context is available.

    # --------------------------------------------------------
    # 7.1 RETRIEVE HISTORICAL OHLC VALUES
    # --------------------------------------------------------
    data = list(  # Evaluate the query into a list of dictionaries.
        MarketData.objects  # Access the historical-data manager.
        .filter(symbol=symbol)  # Keep the selected asset's observations.
        .order_by("date")  # Order oldest observations first.
        .values("date", "high_price", "low_price", "close_price")  # Request only the fields needed here.
    )  # Close the list conversion.
    if not data:  # Check whether the query returned any observations.
        return None  # Return the original no-data value.
    closes = np.array(  # Construct the closing-price array.
        [float(row["close_price"]) for row in data],  # Comprehension: read and convert each close.
        dtype=float,  # Store floating-point values.
    )  # Close the array constructor.
    highs = np.array(  # Construct the high-price array.
        [float(row["high_price"]) for row in data],  # Read and convert each observation's high.
        dtype=float,  # Store floating-point values.
    )  # Close the array constructor.
    lows = np.array(  # Construct the low-price array.
        [float(row["low_price"]) for row in data],  # Read and convert each observation's low.
        dtype=float,  # Store floating-point values.
    )  # Close the array constructor.

    # --------------------------------------------------------
    # 7.2 LATEST CLOSE AND RETURNS
    # --------------------------------------------------------
    latest_close = float(closes[-1])  # Negative indexing: read the latest chronological close.
    returns = np.array([], dtype=float)  # Initialise an empty return array.
    if len(closes) >= 2:  # Require two closes before calculating a return.
        previous_prices = closes[:-1]  # Select the previous closes.
        current_prices = closes[1:]  # Select the corresponding current closes.
        valid_mask = previous_prices > 0  # Mark intervals with positive previous closes.
        if np.any(valid_mask):  # Check whether at least one interval passes the mask.
            returns = current_prices[valid_mask] / previous_prices[valid_mask] - 1  # Calculate fractional close-to-close returns.

    # --------------------------------------------------------
    # 7.3 VOLATILITY — UP TO 20 RECENT VALID RETURNS
    # --------------------------------------------------------
    annualised_volatility_pct = None  # Initialise volatility as unavailable.
    if len(returns) >= 2:  # Require at least two returns.
        recent_returns = returns[-20:]  # Slice: take up to the last twenty valid returns.
        if len(recent_returns) >= 2:  # Preserve the second sample-size check.
            daily_volatility = float(np.std(recent_returns, ddof=1))  # Calculate sample standard deviation.
            annualised_volatility_pct = daily_volatility * math.sqrt(252) * 100  # Annualise under the daily-data assumption and express as a percentage.

    # --------------------------------------------------------
    # 7.4 ATR — SIMPLE MEAN OF UP TO 14 TRUE RANGES
    # --------------------------------------------------------
    true_ranges = []  # List: collect one true-range value per observation.
    for index in range(len(data)):  # Loop: visit every observation by its index.
        high = float(highs[index])  # Read the current high.
        low = float(lows[index])  # Read the current low.
        if index == 0:  # Condition: the first observation has no earlier close in this data.
            true_range = high - low  # Use its high-low range.
        else:  # Branch: later observations have a previous close.
            previous_close = float(closes[index - 1])  # Read that previous close.
            true_range = max(  # Select the largest of the three range measures.
                high - low,  # Current high-low distance.
                abs(high - previous_close),  # Absolute high-to-previous-close distance.
                abs(low - previous_close),  # Absolute low-to-previous-close distance.
            )  # Close the maximum calculation.
        true_ranges.append(true_range)  # Method call: add this observation's range to the list.
    atr_14 = None  # Initialise ATR as unavailable.
    if true_ranges:  # Check that range values exist.
        recent_true_ranges = true_ranges[-14:]  # Take up to fourteen recent ranges.
        atr_14 = sum(recent_true_ranges) / len(recent_true_ranges)  # Calculate their simple arithmetic mean.

    # --------------------------------------------------------
    # 7.5 HIGH / LOW — UP TO 30 RECENT OBSERVATIONS
    # --------------------------------------------------------
    recent_highs = highs[-30:]  # Select up to thirty recent highs.
    recent_lows = lows[-30:]  # Select up to thirty recent lows.
    high_30 = float(np.max(recent_highs))  # Find the highest value in that high-price window.
    low_30 = float(np.min(recent_lows))  # Find the lowest value in that low-price window.

    # --------------------------------------------------------
    # 7.6 HISTORICAL CLOSE-PRICE MAXIMUM DRAWDOWN
    # --------------------------------------------------------
    running_peak = float(closes[0])  # Initialise the running peak from the first close.
    maximum_drawdown = 0.0  # Initialise the most negative drawdown.
    for close in closes:  # Loop over all chronological closing prices.
        close = float(close)  # Convert the current close to a Python float.
        running_peak = max(running_peak, close)  # Update the highest close seen so far.
        if running_peak > 0:  # Avoid dividing by a non-positive running peak.
            drawdown = close / running_peak - 1  # Calculate the fractional change from that peak.
            maximum_drawdown = min(maximum_drawdown, drawdown)  # Retain the deepest negative drawdown.
    maximum_drawdown_pct = abs(maximum_drawdown) * 100  # Convert the negative fraction to a positive percentage.

    # --------------------------------------------------------
    # 7.7 RETURN THE HISTORICAL CONTEXT
    # --------------------------------------------------------
    return {  # Return a dictionary of named display values.
        "symbol": symbol,  # Return the normalised asset symbol.
        "latest_close": round(latest_close, 4),  # Round the latest stored close to four decimal places.
        "latest_date": data[-1]["date"].isoformat(),  # Convert the latest stored date to ISO text.
        "observations": len(data),  # Return the total number of matching observations.
        "atr_14": round(atr_14, 4) if atr_14 is not None else None,  # Return rounded ATR or its unavailable value.
        "annualised_volatility_pct": round(annualised_volatility_pct, 2) if annualised_volatility_pct is not None else None,  # Return rounded volatility percentage when available.
        "high_30": round(high_30, 4),  # Return the recent high.
        "low_30": round(low_30, 4),  # Return the recent low.
        "maximum_drawdown_pct": round(maximum_drawdown_pct, 2),  # Return historical close-price drawdown as a percentage.
    }  # Close the context dictionary.

# ============================================================
# 8. MAIN TRADE RISK PLAN
# ============================================================
def calculate_trade_risk_plan(  # Define the main risk-planning function.
    trading_capital,  # Parameter: available simulated capital.
    risk_percentage,  # Parameter: human-readable risk percentage; 1 means 1%.
    entry_price,  # Parameter: entry price per unit.
    direction,  # Parameter: long or short.
    stop_method,  # Parameter: percentage, atr, or fixed.
    stop_loss_percentage=None,  # Optional parameter: human-readable stop percentage.
    fixed_stop_price=None,  # Optional parameter: exact stop price.
    atr=None,  # Optional parameter: historical ATR value.
    atr_multiplier=None,  # Optional parameter: ATR multiplier.
    target_price=None,  # Optional parameter: favourable target price.
):  # Finish the function signature.
    """Build a whole-unit risk plan constrained by risk budget and capital."""  # Function documentation.

    # --------------------------------------------------------
    # 8.1 NORMALISE INPUTS
    # --------------------------------------------------------
    trading_capital = float(trading_capital)  # Convert capital to float.
    risk_percentage = float(risk_percentage)  # Convert the human-readable risk percentage to float.
    entry_price = float(entry_price)  # Convert entry price to float.
    direction = str(direction).strip().lower()  # Normalise the direction text.
    stop_method = str(stop_method).strip().lower()  # Normalise the stop-method text.

    # --------------------------------------------------------
    # 8.2 VALIDATE CORE INPUTS
    # --------------------------------------------------------
    if trading_capital <= 0:  # Require positive capital.
        raise ValueError("Trading capital must be greater than zero.")  # Raise the original error.
    if entry_price <= 0:  # Require a positive entry price.
        raise ValueError("Entry price must be greater than zero.")  # Raise the original error.
    if risk_percentage <= 0:  # Require a positive risk percentage.
        raise ValueError("Risk percentage must be greater than zero.")  # Raise the original error.
    if risk_percentage > 100:  # Enforce the original upper risk bound.
        raise ValueError("Risk percentage cannot exceed 100%.")  # Raise the original error.
    if direction not in {"long", "short"}:  # Set membership: accept only the two supported directions.
        raise ValueError("Trade direction must be either long or short.")  # Raise the original error.
    if stop_method not in {"percentage", "atr", "fixed"}:  # Set membership: accept only the supported stop methods.
        raise ValueError("Unknown stop-loss method.")  # Raise the original error.

    # --------------------------------------------------------
    # 8.3 MAXIMUM RISK BUDGET
    # --------------------------------------------------------
    maximum_risk_amount = trading_capital * (risk_percentage / 100)  # Convert percentage to a fraction and multiply by capital.

    # ========================================================
    # 9. STOP-LOSS CALCULATION
    # ========================================================
    stop_price = None  # Initialise the calculated stop price.
    stop_distance_amount = None  # Initialise the monetary stop distance.
    stop_distance_percentage = None  # Initialise the percentage stop distance.

    # --------------------------------------------------------
    # 9.1 PERCENTAGE STOP
    # --------------------------------------------------------
    if stop_method == "percentage":  # Branch: calculate a percentage-based stop.
        if stop_loss_percentage is None:  # Check whether its required input is missing.
            raise ValueError("A stop-loss percentage is required.")  # Raise the original error.
        stop_loss_percentage = float(stop_loss_percentage)  # Convert the supplied percentage to float.
        if stop_loss_percentage <= 0:  # Require a positive distance.
            raise ValueError("Stop-loss percentage must be greater than zero.")  # Raise the original error.
        if stop_loss_percentage >= 100:  # Require a distance below 100%.
            raise ValueError("Stop-loss percentage must be less than 100%.")  # Raise the original error.
        stop_distance_percentage = stop_loss_percentage  # Store the supplied percentage.
        stop_distance_amount = entry_price * (stop_loss_percentage / 100)  # Convert the percentage into a monetary distance.
        if direction == "long":  # Choose the long-position stop.
            stop_price = entry_price - stop_distance_amount  # Place it below entry.
        else:  # The already validated alternative direction is short.
            stop_price = entry_price + stop_distance_amount  # Place it above entry.

    # --------------------------------------------------------
    # 9.2 ATR STOP
    # --------------------------------------------------------
    elif stop_method == "atr":  # Alternative branch: calculate an ATR-based stop.
        if atr is None:  # Check whether historical ATR is unavailable.
            raise ValueError(  # Construct the original explanatory error.
                "ATR is unavailable for this asset. "  # First part of the message.
                "Import historical OHLCV data first or use "  # Continue the message.
                "a percentage/fixed-price stop."  # Finish the message.
            )  # Close the error constructor.
        atr = float(atr)  # Convert ATR to float.
        if atr <= 0:  # Require positive ATR.
            raise ValueError("ATR must be greater than zero.")  # Raise the original error.
        multiplier = float(atr_multiplier if atr_multiplier is not None else 2)  # Conditional expression: use the supplied multiplier or the default two.
        if multiplier <= 0:  # Require a positive multiplier.
            raise ValueError("ATR multiplier must be greater than zero.")  # Raise the original error.
        stop_distance_amount = atr * multiplier  # Multiply ATR by the chosen multiplier.
        stop_distance_percentage = stop_distance_amount / entry_price * 100  # Express the distance as a percentage of entry.
        if direction == "long":  # Choose the long-position stop.
            stop_price = entry_price - stop_distance_amount  # Place it below entry.
        else:  # Choose the short-position stop.
            stop_price = entry_price + stop_distance_amount  # Place it above entry.

    # --------------------------------------------------------
    # 9.3 FIXED STOP
    # --------------------------------------------------------
    elif stop_method == "fixed":  # Alternative branch: use an exact supplied stop price.
        if fixed_stop_price is None:  # Require the fixed-price input.
            raise ValueError("A fixed stop price is required.")  # Raise the original error.
        stop_price = float(fixed_stop_price)  # Convert the fixed price to float.
        if stop_price <= 0:  # Require a positive fixed price.
            raise ValueError("Fixed stop price must be greater than zero.")  # Raise the original error.
        stop_distance_amount = abs(entry_price - stop_price)  # Calculate the unsigned distance from entry.
        stop_distance_percentage = stop_distance_amount / entry_price * 100  # Convert the distance to a percentage.

    # ========================================================
    # 10. VALIDATE STOP DIRECTION
    # ========================================================
    if direction == "long" and stop_price >= entry_price:  # Boolean AND: reject a long stop at or above entry.
        raise ValueError(  # Construct the original error.
            "For a long position, the stop price must "  # First part of the message.
            "be below the entry price."  # Finish the message.
        )  # Close the error constructor.
    if direction == "short" and stop_price <= entry_price:  # Reject a short stop at or below entry.
        raise ValueError(  # Construct the original error.
            "For a short position, the stop price must "  # First part of the message.
            "be above the entry price."  # Finish the message.
        )  # Close the error constructor.
    if stop_price <= 0:  # Require the final calculated stop to remain positive.
        raise ValueError("Calculated stop price must be greater than zero.")  # Raise the original error.

    # ========================================================
    # 11. RISK PER UNIT
    # ========================================================
    risk_per_unit = abs(entry_price - stop_price)  # Calculate the assumed loss per unit at the planned stop.
    if risk_per_unit <= 0:  # Reject zero distance before dividing by it.
        raise ValueError("Stop price must be different from entry price.")  # Raise the original error.

    # ========================================================
    # 12. RISK-BASED QUANTITY
    # ========================================================
    risk_based_quantity = math.floor(maximum_risk_amount / risk_per_unit)  # Divide risk budget by unit risk and round down to whole units.

    # ========================================================
    # 13. CAPITAL-LIMITED QUANTITY
    # ========================================================
    capital_limited_quantity = math.floor(trading_capital / entry_price)  # Calculate whole units under the model's capital cap.

    # ========================================================
    # 14. FINAL QUANTITY
    # ========================================================
    quantity = min(risk_based_quantity, capital_limited_quantity)  # Select the smaller of the two quantity limits.
    quantity = max(quantity, 0)  # Prevent a negative final quantity.

    # ========================================================
    # 15. LIMITING CONSTRAINT
    # ========================================================
    capital_cap_applied = capital_limited_quantity < risk_based_quantity  # Store whether the capital limit is strictly smaller.

    # ========================================================
    # 16. POSITION VALUE
    # ========================================================
    position_value = quantity * entry_price  # Multiply final quantity by entry price.

    # ========================================================
    # 17. CAPITAL ALLOCATION
    # ========================================================
    capital_allocation_pct = position_value / trading_capital * 100  # Express position value as a percentage of capital.

    # ========================================================
    # 18. PLANNED LOSS
    # ========================================================
    planned_loss = quantity * risk_per_unit  # Calculate loss at the assumed stop price for this quantity.
    actual_risk_percentage = planned_loss / trading_capital * 100 if trading_capital > 0 else 0  # Preserve the conditional percentage calculation.

    # ========================================================
    # 19. TARGET AND POTENTIAL REWARD
    # ========================================================
    potential_reward = None  # Initialise total reward as unavailable.
    reward_per_unit = None  # Initialise unit reward as unavailable.
    reward_risk_ratio = None  # Initialise the ratio as unavailable.
    if target_price is not None:  # Only calculate rewards when a target was supplied.
        target_price = float(target_price)  # Convert the target price to float.
        if target_price <= 0:  # Require a positive target price.
            raise ValueError("Target price must be greater than zero.")  # Raise the original error.
        if direction == "long" and target_price <= entry_price:  # Reject an unfavourable long target.
            raise ValueError(  # Construct the original error.
                "For a long position, the target price must "  # First part of the message.
                "be above the entry price."  # Finish the message.
            )  # Close the error constructor.
        if direction == "short" and target_price >= entry_price:  # Reject an unfavourable short target.
            raise ValueError(  # Construct the original error.
                "For a short position, the target price must "  # First part of the message.
                "be below the entry price."  # Finish the message.
            )  # Close the error constructor.
        if direction == "long":  # Choose the long reward formula.
            reward_per_unit = target_price - entry_price  # Calculate the upward target distance.
        else:  # Choose the short reward formula.
            reward_per_unit = entry_price - target_price  # Calculate the downward target distance.
        potential_reward = reward_per_unit * quantity  # Calculate total reward for the final quantity.
        if planned_loss > 0:  # Avoid dividing by zero when quantity produces no planned loss.
            reward_risk_ratio = potential_reward / planned_loss  # Calculate total potential reward divided by planned loss.

    # ========================================================
    # 20. STOP DISTANCE RELATIVE TO ATR
    # ========================================================
    stop_atr_multiple = None  # Initialise the ATR relationship as unavailable.
    if atr is not None:  # Check whether any ATR value was supplied.
        atr_value = float(atr)  # Convert it to float.
        if atr_value > 0:  # Only divide by positive ATR.
            stop_atr_multiple = risk_per_unit / atr_value  # Express the stop distance in ATR units.

    # ========================================================
    # 21. POSITION STATUS
    # ========================================================
    if quantity <= 0:  # Check whether the plan allows no whole units.
        position_status = (  # Assign the original explanatory text.
            "The selected risk budget and stop distance do not "  # First part of the message.
            "allow the purchase of one whole unit."  # Finish the message.
        )  # Close the string expression.
    elif capital_cap_applied:  # Otherwise check whether capital is the stricter constraint.
        position_status = (  # Assign the original capital-limit explanation.
            "Available trading capital is the limiting factor "  # First part of the message.
            "for this position size."  # Finish the message.
        )  # Close the string expression.
    else:  # Remaining branch: risk budget limits quantity, or both limits are equal.
        position_status = (  # Assign the original risk-limit explanation.
            "The position size is constrained by the selected "  # First part of the message.
            "maximum risk budget."  # Finish the message.
        )  # Close the string expression.

    # ========================================================
    # 22. REWARD / RISK INTERPRETATION
    # ========================================================
    reward_risk_status = None  # Initialise interpretation as unavailable.
    if reward_risk_ratio is not None:  # Interpret only an available ratio.
        if reward_risk_ratio >= 2:  # Check the highest interpretation threshold first.
            reward_risk_status = (  # Assign the original at-least-two interpretation.
                "The potential reward is at least twice the "  # First part of the message.
                "planned risk in this simulation."  # Finish the message.
            )  # Close the string expression.
        elif reward_risk_ratio >= 1:  # This branch includes exactly 1:1 and values below 2:1.
            reward_risk_status = (  # Preserve the original wording, including its use of exceeds.
                "Potential reward exceeds planned risk, but "  # First part of the original message.
                "the margin is below 2:1."  # Finish the message.
            )  # Close the string expression.
        else:  # Remaining branch: the available ratio is below one.
            reward_risk_status = (  # Assign the original below-one interpretation.
                "Potential reward is smaller than the planned "  # First part of the message.
                "risk based on the selected target and stop."  # Finish the message.
            )  # Close the string expression.

    # ========================================================
    # 23. RETURN THE COMPLETE PLAN
    # ========================================================
    return {  # Dictionary: package calculated values under named keys.
        "maximum_risk_amount": round(maximum_risk_amount, 2),  # Return the requested monetary risk budget.
        "requested_risk_percentage": round(risk_percentage, 2),  # Return the requested human-readable percentage.
        "actual_risk_percentage": round(actual_risk_percentage, 2),  # Return the planned-loss percentage after quantity limits.
        "entry_price": round(entry_price, 4),  # Return the rounded entry price.
        "stop_price": round(stop_price, 4),  # Return the rounded stop price.
        "stop_distance_amount": round(stop_distance_amount, 4),  # Return the monetary stop distance.
        "stop_distance_percentage": round(stop_distance_percentage, 2),  # Return the percentage stop distance.
        "stop_method": stop_method,  # Return the selected method code.
        "direction": direction,  # Return the normalised trade direction.
        "risk_per_unit": round(risk_per_unit, 4),  # Return the planned risk per unit.
        "risk_based_quantity": risk_based_quantity,  # Return the quantity allowed by the risk budget.
        "capital_limited_quantity": capital_limited_quantity,  # Return the quantity allowed by the capital cap.
        "quantity": quantity,  # Return the final whole-unit quantity.
        "position_value": round(position_value, 2),  # Return total entry-price position value.
        "capital_allocation_pct": round(capital_allocation_pct, 2),  # Return the allocated capital percentage.
        "planned_loss": round(planned_loss, 2),  # Return the calculated loss at the assumed stop.
        "target_price": round(target_price, 4) if target_price is not None else None,  # Return the target when supplied.
        "reward_per_unit": round(reward_per_unit, 4) if reward_per_unit is not None else None,  # Return unit reward when calculated.
        "potential_reward": round(potential_reward, 2) if potential_reward is not None else None,  # Return total reward when calculated.
        "reward_risk_ratio": round(reward_risk_ratio, 2) if reward_risk_ratio is not None else None,  # Return the rounded ratio when available.
        "reward_risk_status": reward_risk_status,  # Return the original ratio interpretation.
        "capital_cap_applied": capital_cap_applied,  # Return the Boolean capital-limit flag.
        "position_status": position_status,  # Return the quantity-limit explanation.
        "stop_atr_multiple": round(stop_atr_multiple, 2) if stop_atr_multiple is not None else None,  # Return the ATR relationship when available.
    }  # Close the returned plan dictionary.

# ============================================================
# 24. SIMPLE POSITION STRESS IMPACT
# ============================================================
def calculate_position_stress_impact(  # Define the simple downward-shock calculation.
    position_value,  # Parameter: the position's starting value.
    trading_capital,  # Parameter: total simulated capital.
    shock_percentage,  # Parameter: human-readable downward-shock percentage.
):  # Finish the signature.
    """Calculate a simple position-value reduction and its capital impact."""  # Function documentation.
    position_value = float(position_value)  # Convert position value to float.
    trading_capital = float(trading_capital)  # Convert capital to float.
    shock_percentage = float(shock_percentage)  # Convert the shock percentage to float.

    # --------------------------------------------------------
    # 24.1 VALIDATE INPUTS
    # --------------------------------------------------------
    if position_value < 0:  # Reject negative position value.
        raise ValueError("Position value cannot be negative.")  # Raise the original error.
    if trading_capital <= 0:  # Require positive capital.
        raise ValueError("Trading capital must be greater than zero.")  # Raise the original error.
    if shock_percentage < 0:  # Reject negative shocks.
        raise ValueError("Shock percentage cannot be negative.")  # Raise the original error.
    if shock_percentage > 100:  # Reject shocks above 100%.
        raise ValueError("Shock percentage cannot exceed 100%.")  # Raise the original error.

    # --------------------------------------------------------
    # 24.2 CALCULATE IMPACT
    # --------------------------------------------------------
    estimated_loss = position_value * (shock_percentage / 100)  # Apply the percentage reduction to position value.
    stressed_position_value = max(position_value - estimated_loss, 0)  # Subtract the loss and keep the result non-negative.
    portfolio_impact_pct = estimated_loss / trading_capital * 100  # Express the loss as a percentage of total capital.

    # --------------------------------------------------------
    # 24.3 RETURN THE SUMMARY
    # --------------------------------------------------------
    return {  # Return a dictionary of rounded summary values.
        "shock_percentage": round(shock_percentage, 2),  # Return the supplied shock percentage.
        "position_value": round(position_value, 2),  # Return the starting position value.
        "stressed_position_value": round(stressed_position_value, 2),  # Return the reduced position value.
        "estimated_loss": round(estimated_loss, 2),  # Return the estimated monetary loss.
        "portfolio_impact_pct": round(portfolio_impact_pct, 2),  # Return the loss as a percentage of capital.
    }  # Close the stress-impact dictionary.