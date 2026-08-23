# Import necessary libraries for financial data handling
import yfinance as yf  # Yahoo Finance API library for downloading market data
import pandas as pd  # Data manipulation library for working with structured data
from datetime import datetime  # For handling date and time operations
from core.models import MarketData  # Import our Django model for storing market data


def import_yahoo_finance_data(symbol, start_date, end_date):
    """ Import market data from Yahoo Finance API and store it in our database
    This function connects to Yahoo Finance, downloads historical price data for a
    specific stock symbol within a date range, and saves it to our MarketData model.
    Args:
        symbol (str): Stock ticker symbol (e.g., 'AAPL' for Apple)
        start_date (datetime or str): Start date for data retrieval
        end_date (datetime or str): End date for data retrieval
    Returns:
        int: Number of records successfully imported to the database 
    Raises:
        Exception: If data cannot be retrieved or saved to database  """
    try:
        # Step 1: Create a Ticker object for the requested symbol
        # The Ticker class from yfinance represents a financial instrument
        # that we can query for historical data, company info, etc.
        ticker = yf.Ticker(symbol)
        # Step 2: Download historical data using the history() method
        # This returns a pandas DataFrame with columns like Open, High, Low, Close, Volume
        # The index of the DataFrame contains the dates
        data = ticker.history(start=start_date, end=end_date)
        # Step 3: Check if we received any data
        # If the DataFrame is empty, it means Yahoo Finance has no data for this symbol
        # or the date range is invalid
        
        if data.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        # Step 4: Initialize a counter to track how many records we import
        records_imported = 0
        
        # Step 5: Process each row of data and save to our database
        # The iterrows() method allows us to loop through each row of the DataFrame
        # Each row contains all the price data for a specific day
        for date, row in data.iterrows():
            # Step 5a: Use Django's update_or_create method to save the data
            # This method is perfect for our use case because:
            # - If the record (symbol + date) already exists, it updates it
            # - If the record doesn't exist, it creates a new one
            # - This prevents duplicate entries and handles data updates gracefully
            MarketData.objects.update_or_create(
                # These fields are used to identify if a record already exists
                symbol=symbol,
                date=date,
                # These fields contain the data to be updated or created
                defaults={
                    # Round prices to 4 decimal places for consistency
                    # The row['Open'] syntax accesses the 'Open' column of the current row
                    'open_price': round(row['Open'], 4),
                    'high_price': round(row['High'], 4),
                    'low_price': round(row['Low'], 4),
                    'close_price': round(row['Close'], 4),
                    # Convert volume to integer (it might be a float in some cases)
                    'volume': int(row['Volume'])
                }
            )
            # Step 5b: Increment our counter for each record processed
            records_imported += 1
        
        # Step 6: Return the total number of records we imported
        return records_imported
    except Exception as e:
        # Step 7: Handle any errors that occur during the process
        # We wrap the original error in a more descriptive exception message
        # This makes debugging easier and provides better error feedback
        raise Exception(f"Error importing data: {str(e)}")


def get_latest_data(symbol, period='1mo'):
    """ Retrieve the most recent market data for a symbol from Yahoo Finance
    This function fetches recent price data and formats it for display in templates.
    Unlike the import function, this doesn't save to the database - it just returns
    the data in a format that's easy to use in web templates.
    Args:
        symbol (str): Stock ticker symbol (e.g., 'AAPL' for Apple)
        period (str): Time period for data retrieval (default: '1mo' for one month)
                      Other options: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
    Returns:
        list: List of dictionaries containing price data, or None if no data found
              Each dictionary has keys: date, open, high, low, close, volume
    Raises:
        Exception: If data cannot be retrieved from Yahoo Finance   """
    try:
        # Step 1: Create a Ticker object for the requested symbol
        ticker = yf.Ticker(symbol)
        # Step 2: Download historical data for the specified period
        # Unlike the import function, we're using a period string instead of specific dates
        # This gives us the most recent data for the requested time frame
        data = ticker.history(period=period)
        
        # Step 3: Check if we received any data
        if data.empty:
            return None
        
        # Step 4: Convert the DataFrame to a list of dictionaries
        # This format is much easier to work with in Django templates
        # Template code can access data like {{ data.0.date }} or {{ data.0.close }}
        result = []
        
        # Step 5: Process each row and create a dictionary for each day's data
        for date, row in data.iterrows():
            # Step 5a: Create a dictionary with the data we need
            # We're formatting the date as a string (YYYY-MM-DD) for easier display
            # and rounding the price values for consistency
            result.append({
                'date': date.strftime('%Y-%m-%d'),  # Format date as string
                'open': round(row['Open'], 4),
                'high': round(row['High'], 4),
                'low': round(row['Low'], 4),
                'close': round(row['Close'], 4),
                'volume': int(row['Volume'])
            })
        
        # Step 6: Return the list of dictionaries
        return result
        
    except Exception as e:
        # Step 7: Handle any errors that occur during the process
        raise Exception(f"Error fetching data: {str(e)}")