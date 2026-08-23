# Import necessary libraries for data manipulation and numerical operations
# pandas is used for working with dataframes (tables of data)
# numpy is used for mathematical operations
# datetime and timedelta are used for handling dates and time periods
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
# Import our Django models that we need to interact with
# MarketData: Stores historical price data for stocks
# Backtest: Stores results of a backtest
# BacktestTrade: Stores individual trades made during a backtest
from core.models import MarketData, Backtest, BacktestTrade
# Import the StrategyRule model from the current app
# StrategyRule: Defines the rules that make up a trading strategy
from .models import StrategyRule


def run_backtest(strategy, start_date, end_date, initial_capital=10000):
    """Run a backtest for a given strategy
    Args:
        strategy: The Strategy object to test
        start_date: Start date for the backtest
        end_date: End date for the backtest
        initial_capital: Starting capital for the portfolio (default: $10,000)
    Returns:
        Backtest: The completed backtest with results """
    # STEP 1: EXTRACT SYMBOLS FROM STRATEGY RULES
    # Create an empty set to store all symbols used in the strategy
    # A set is used to automatically handle duplicates
    symbols = set()
    # Loop through all rules in the strategy
    # strategy.rules.all() gets all related StrategyRule objects
    for rule in strategy.rules.all():
        # Extract symbols from rule parameters (simplified approach)
        # In a real implementation, you might parse the condition string
        if 'symbol' in rule.parameters:
            symbols.add(rule.parameters['symbol'])
    
    # Check if we found any symbols
    if not symbols:
        raise ValueError("No symbols found in strategy rules")
    
    # STEP 2: FETCH MARKET DATA FOR THE BACKTEST PERIOD
    # Create a dictionary to hold market data for each symbol
    market_data = {}
    # Loop through each symbol and fetch its data
    for symbol in symbols:
        # Query the MarketData model for the symbol's price data
        # We filter by symbol and date range, then order by date
        data = MarketData.objects.filter(
            symbol=symbol,
            date__gte=start_date,  # __gte means "greater than or equal to"
            date__lte=end_date    # __lte means "less than or equal to"
        ).order_by('date')
        
        # Check if we found any data for this symbol
        if not data:
            raise ValueError(f"No market data found for {symbol}")
        
        # Convert the Django queryset to a pandas DataFrame for easier manipulation
        # A DataFrame is like a spreadsheet in memory - very useful for financial data
        df = pd.DataFrame(list(data.values()))
        # Convert the date column to datetime objects
        df['date'] = pd.to_datetime(df['date'])
        # Set the date column as the index (row labels) of the DataFrame
        # This makes it easier to select data by date
        df.set_index('date', inplace=True)
        # Store the DataFrame in our market_data dictionary
        market_data[symbol] = df
    
    # STEP 3: INITIALIZE BACKTEST VARIABLES
    # These variables track the state of our portfolio during the backtest
    portfolio_value = initial_capital  # Total value of portfolio (cash + positions)
    cash = initial_capital              # Available cash for new trades
    positions = {}                      # Dictionary to track current positions (symbol: quantity)
    trades = []                         # List to track all trades made
    
    # Create a Backtest record in the database to store our results
    # This is how we save the backtest results for later viewing
    backtest = Backtest.objects.create(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital
    )
    
    # STEP 4: RUN THE BACKTEST DAY BY DAY
    # Get all unique dates from all symbols' data
    # We use set().union() to combine all date indexes and remove duplicates
    all_dates = sorted(set().union(*[df.index for df in market_data.values()]))
    
    # Loop through each day in our backtest period
    for date in all_dates:
        # Get current prices for all symbols on this date
        current_prices = {}
        for symbol, df in market_data.items():
            # Check if this date exists in this symbol's data
            if date in df.index:
                # Get the closing price for this symbol on this date
                current_prices[symbol] = df.loc[date, 'close_price']
        
        # STEP 5: CHECK STRATEGY RULES AND EXECUTE TRADES
        # Loop through all active rules in the strategy
        for rule in strategy.rules.filter(is_active=True):
            # Evaluate if this rule is triggered on this date
            # The evaluate_rule function is defined below
            if not evaluate_rule(rule, market_data, date, current_prices):
                continue  # If rule is not triggered, skip to next rule
            
            # EXECUTE TRADE BASED ON RULE ACTION
            if rule.action == 'buy':
                # Get the symbol from the rule parameters
                symbol = rule.parameters.get('symbol')
                # Check if we have price data for this symbol
                if symbol and symbol in current_prices:
                    price = current_prices[symbol]
                    # Calculate position size using simple risk management
                    # Here we risk 1% of our portfolio per trade
                    position_size = portfolio_value * 0.01 / price
                    cost = position_size * price

                    # Check if we have enough cash to make this trade
                    if cash >= cost:
                        # Update our cash and positions
                        cash -= cost
                        positions[symbol] = positions.get(symbol, 0) + position_size
                        
                        # Record this trade in the database
                        trade = BacktestTrade.objects.create(
                            backtest=backtest,
                            symbol=symbol,
                            entry_date=date.date(),
                            entry_price=price,
                            quantity=int(position_size),  # Convert to integer
                            trade_type='long'  # This is a long (buy) position
                        )
                        trades.append(trade)
            
            elif rule.action == 'sell':
                # Get the symbol from the rule parameters
                symbol = rule.parameters.get('symbol')
                # Check if we have price data and an open position for this symbol
                if symbol and symbol in current_prices and symbol in positions:
                    price = current_prices[symbol]
                    quantity = positions[symbol]
                    proceeds = quantity * price
                    # Update our cash and positions
                    cash += proceeds
                    del positions[symbol]  # Remove this position
                    
                    # Find and update the corresponding open trade record
                    open_trades = BacktestTrade.objects.filter(
                        backtest=backtest,
                        symbol=symbol,
                        status='open'
                    ).order_by('entry_date')
                    
                    if open_trades.exists():
                        # Get the first (and likely only) open trade for this symbol
                        trade = open_trades.first()
                        # Update the trade with exit information
                        trade.exit_date = date.date()
                        trade.exit_price = price
                        # Calculate profit/loss for this trade
                        trade.profit_loss = proceeds - (trade.quantity * trade.entry_price)
                        # Mark the trade as closed
                        trade.status = 'closed'
                        trade.save()
        
        # STEP 6: UPDATE PORTFOLIO VALUE
        # Calculate the total value of our portfolio (cash + positions)
        portfolio_value = cash
        for symbol, quantity in positions.items():
            if symbol in current_prices:
                portfolio_value += quantity * current_prices[symbol]
    
    # STEP 7: CALCULATE FINAL PORTFOLIO VALUE
    # This handles any positions that are still open at the end of the backtest
    for symbol, quantity in positions.items():
        if symbol in current_prices:
            portfolio_value += quantity * current_prices[symbol]
    
    # STEP 8: CALCULATE PERFORMANCE METRICS
    # Calculate total return as a percentage
    total_return = (portfolio_value - initial_capital) / initial_capital
    
    # Calculate maximum drawdown (largest peak-to-trough decline)
    # This is simplified - in a real implementation, you would track
    # portfolio values throughout the backtest to calculate this accurately
    portfolio_values = [initial_capital]  # This would be populated during the backtest
    max_drawdown = 0
    peak = portfolio_values[0]
    
    for value in portfolio_values:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Calculate Sharpe ratio (risk-adjusted return)
    # This is simplified - in a real implementation, you would use
    # actual portfolio values throughout the backtest
    returns = np.diff(portfolio_values) / portfolio_values[:-1]
    sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
    
    # Calculate win rate (percentage of profitable trades)
    winning_trades = BacktestTrade.objects.filter(
        backtest=backtest,
        status='closed',
        profit_loss__gt=0  # __gt means "greater than"
    ).count()
    
    total_trades = BacktestTrade.objects.filter(
        backtest=backtest,
        status='closed'
    ).count()
    
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # STEP 9: UPDATE BACKTEST RECORD WITH RESULTS
    # Save all calculated metrics to the Backtest object
    backtest.final_capital = portfolio_value
    backtest.total_return = total_return
    backtest.max_drawdown = max_drawdown
    backtest.sharpe_ratio = sharpe_ratio
    backtest.win_rate = win_rate
    backtest.total_trades = total_trades
    backtest.save()
    
    # Return the completed backtest object
    return backtest


def evaluate_rule(rule, market_data, date, current_prices):
    """Evaluate if a strategy rule is triggered on a given date
    Args:
        rule: The StrategyRule to evaluate
        market_data: Dictionary of DataFrames with market data
        date: The current date being evaluated
        current_prices: Dictionary of current prices for all symbols
    Returns:
        bool: True if the rule is triggered, False otherwise"""
    # This is a simplified version - in a real implementation, you'd need
    # to parse and evaluate the condition more carefully
    
    # Get the condition string and parameters from the rule
    condition = rule.condition
    parameters = rule.parameters
    
    # EXAMPLE CONDITION: "price > moving_average"
    # This checks if the current price is above a moving average
    if 'price' in condition and 'moving_average' in condition:
        # Get the symbol and moving average period from the rule parameters
        symbol = parameters.get('symbol')
        period = parameters.get('period', 20)  # Default to 20 days if not specified
        
        # Check if we have data for this symbol
        if symbol not in market_data or date not in market_data[symbol].index:
            return False
        
        # Get the current price for this symbol
        current_price = market_data[symbol].loc[date, 'close_price']
        
        # Calculate the moving average
        # First, get all data up to the current date
        df = market_data[symbol].loc[:date]
        # Check if we have enough data to calculate the moving average
        if len(df) < period:
            return False
        
        # Calculate the moving average using pandas' rolling function
        ma = df['close_price'].rolling(window=period).mean().iloc[-1]
        
        # Return True if current price is above the moving average
        return current_price > ma
    
    # Add more condition evaluations as needed
    # For example, you could add conditions for RSI, MACD, etc.
    return False