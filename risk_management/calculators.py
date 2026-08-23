# Import necessary libraries for mathematical operations and data handling
import numpy as np  # NumPy is used for numerical operations, especially for financial calculations
import pandas as pd  # Pandas is used for data manipulation and analysis, particularly with time-series data
from decimal import Decimal  # Decimal is used for precise financial calculations to avoid floating-point errors
from core.models import MarketData  # Import our MarketData model to access historical price data

def calculate_position_size(account_balance, risk_percentage, stop_loss_pct, entry_price):
    """ Calculate position size based on risk management rules
    This function is one of the most important risk management tools. It determines how many
    shares or contracts you should buy/sell based on how much risk you're willing to take.
    Args:
        account_balance: Total account balance (e.g., $10,000)
        risk_percentage: Percentage of account to risk on this trade (e.g., 0.01 for 1%)
        stop_loss_pct: Stop loss percentage (e.g., 0.05 for 5%)
        entry_price: Entry price of the trade (e.g., $50.00)
    Returns:
        Position size (number of shares/contracts) """
    # Step 1: Calculate the dollar amount you're willing to risk on this trade
    # If you have $10,000 and risk 1%, you're willing to lose $100 on this trade
    risk_amount = account_balance * risk_percentage
    # Step 2: Calculate the stop loss price
    # If entry price is $50 and stop loss is 5%, your stop loss would be at $47.50
    stop_loss_price = entry_price * (1 - stop_loss_pct)
    # Step 3: Calculate how much you'll lose per share if the stop loss is hit
    # In our example: $50 - $47.50 = $2.50 per share
    price_risk_per_share = entry_price - stop_loss_price
    # Step 4: Calculate how many shares you can buy
    # If you're risking $100 and each share has $2.50 of risk, you can buy 40 shares
    position_size = risk_amount / price_risk_per_share
    
    return position_size

def calculate_stop_loss(entry_price, method='percentage', value=0.05):
    """Calculate stop loss price
    This function determines where to place a stop loss order to limit potential losses.
    Different methods can be used to calculate the optimal stop loss level.
    Args:
        entry_price: Entry price of the trade (e.g., $50.00)
        method: Method for calculating stop loss ('percentage', 'atr', 'support')
        value: Value for the method (percentage, ATR multiplier, etc.)
    Returns:
        Stop loss price   """
    # Currently, we only implement the percentage method
    if method == 'percentage':
        # For a 5% stop loss on a $50 stock: $50 * (1 - 0.05) = $47.50
        return entry_price * (1 - value)
    
    # Future implementations could include:
    # - ATR (Average True Range) method: Uses volatility to set stop loss
    # - Support method: Places stop loss below recent support levels
    # - Moving average method: Places stop loss below a moving average
    
    # Default fallback: 5% stop loss
    return entry_price * (1 - 0.05)

def calculate_risk_reward_ratio(entry_price, stop_loss, target_price):
    """Calculate risk/reward ratio
    This function helps traders evaluate whether a trade is worth taking by comparing
    the potential profit to the potential loss. A good risk/reward ratio is typically
    1:2 or higher (meaning you risk $1 to make $2).
    Args:
        entry_price: Entry price of the trade (e.g., $50.00)
        stop_loss: Stop loss price (e.g., $47.50)
        target_price: Target price for profit (e.g., $55.00)
    Returns:
        Risk/reward ratio """
    # Calculate the risk per share (difference between entry and stop loss)
    # In our example: $50 - $47.50 = $2.50 risk per share
    risk = abs(entry_price - stop_loss)
    # Calculate the potential reward per share (difference between target and entry)
    # In our example: $55 - $50 = $5.00 reward per share
    reward = abs(target_price - entry_price)

    # Calculate the ratio (reward divided by risk)
    # In our example: $5.00 / $2.50 = 2.0 (or 2:1 risk/reward ratio)
    return reward / risk if risk > 0 else 0

def calculate_portfolio_risk(positions, account_balance):
    """ Calculate portfolio risk metrics
    This function analyzes the overall risk of your entire portfolio, not just individual
    trades. It helps ensure you're not taking too much risk across all your positions combined.
    Args:
        positions: List of position dictionaries with symbol, quantity, entry_price, current_price
        account_balance: Total account balance
    Returns:
        Dictionary with risk metrics """
    # Initialize variables to track total portfolio value and risk
    total_value = 0
    total_risk = 0
    
    # Process each position in the portfolio
    for position in positions:
        # Extract position details
        symbol = position['symbol']
        quantity = position['quantity']
        entry_price = position['entry_price']
        current_price = position['current_price']

        # Calculate the current value of this position
        # If you have 100 shares at $50 each, the position value is $5,000
        position_value = quantity * current_price
        total_value += position_value
        
        # Calculate the potential risk for this position
        # This is simplified - we assume a 10% stop loss for all positions
        # In reality, this would vary based on the specific stop loss for each position
        position_risk = position_value * 0.1
        total_risk += position_risk
    
    # Calculate the portfolio risk as a percentage of the total account balance
    # If your total risk is $1,000 and your account balance is $10,000, your risk is 10%
    portfolio_risk_pct = total_risk / account_balance if account_balance > 0 else 0    
    # Return a dictionary with all the calculated risk metrics
    return {
        'total_value': total_value,
        'total_risk': total_risk,
        'portfolio_risk_percentage': portfolio_risk_pct,
        'risk_per_position': total_risk / len(positions) if positions else 0
    }

def calculate_volatility(symbol, period=20):
    """   Calculate historical volatility for a symbol
    This function measures how much a stock's price has fluctuated in the past.
    Higher volatility means higher risk (and potentially higher returns).
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        period: Period for volatility calculation (default: 20 days)
    Returns:
        Annualized volatility percentage  """
    try:
        # Step 1: Get recent price data from our database
        # We need one more day than the period to calculate returns
        data = MarketData.objects.filter(
            symbol=symbol
        ).order_by('-date')[:period+1]
        
        # If we don't have enough data, return 0
        if len(data) < 2:
            return 0
        
        # Step 2: Convert the database data to a pandas DataFrame
        # DataFrames make it much easier to work with time-series data
        df = pd.DataFrame(list(data.values()))
        # Convert the date column to datetime format
        df['date'] = pd.to_datetime(df['date'])
        # Set the date as the index (this is standard for time-series data)
        df.set_index('date', inplace=True)
        # Sort by date to ensure we're working with chronological data
        df = df.sort_index()
        
        # Step 3: Calculate daily returns
        # Returns show the percentage change from one day to the next
        df['returns'] = df['close_price'].pct_change()
        # Step 4: Calculate volatility
        # First, calculate the standard deviation of daily returns
        # Then, annualize it by multiplying by the square root of 252 trading days
        volatility = df['returns'].std() * np.sqrt(252)  # Annualized
        
        return volatility
    except Exception:
        # If anything goes wrong, return 0
        return 0

def calculate_correlation(symbol1, symbol2, period=60):
    """     Calculate correlation between two symbols
    This function measures how two stocks move in relation to each other.
    A correlation of 1 means they move perfectly together, -1 means they move
    in opposite directions, and 0 means they're unrelated.
    Args:
        symbol1: First stock symbol (e.g., 'AAPL')
        symbol2: Second stock symbol (e.g., 'MSFT')
        period: Period for correlation calculation (default: 60 days)
    Returns:
        Correlation coefficient """
    try:
        # Step 1: Get data for both symbols
        data1 = MarketData.objects.filter(
            symbol=symbol1
        ).order_by('-date')[:period]
        
        data2 = MarketData.objects.filter(
            symbol=symbol2
        ).order_by('-date')[:period]
        
        # If we don't have enough data for either symbol, return 0
        if len(data1) < 2 or len(data2) < 2:
            return 0
        
        # Step 2: Convert both datasets to DataFrames
        df1 = pd.DataFrame(list(data1.values()))
        df1['date'] = pd.to_datetime(df1['date'])
        df1.set_index('date', inplace=True)
        df1 = df1.sort_index()
        # Rename the close_price column to price1 to avoid confusion later
        df1.rename(columns={'close_price': 'price1'}, inplace=True)
        
        df2 = pd.DataFrame(list(data2.values()))
        df2['date'] = pd.to_datetime(df2['date'])
        df2.set_index('date', inplace=True)
        df2 = df2.sort_index()
        # Rename the close_price column to price2
        df2.rename(columns={'close_price': 'price2'}, inplace=True)
        
        # Step 3: Merge the two DataFrames
        # This ensures we're only comparing prices on the same dates
        merged = pd.merge(df1, df2, left_index=True, right_index=True)
        # Step 4: Calculate the correlation between the two price series
        # The corr() method calculates the Pearson correlation coefficient
        correlation = merged['price1'].corr(merged['price2'])
        
        # Handle the case where correlation is NaN (Not a Number)
        return correlation if not np.isnan(correlation) else 0
    except Exception:
        # If anything goes wrong, return 0
        return 0