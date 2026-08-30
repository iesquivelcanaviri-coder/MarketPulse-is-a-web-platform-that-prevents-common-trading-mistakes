"""
============================================================
YFINANCE DATA SERVICE
============================================================
Framework mapping: views/tasks call yfinance here; results are normalised into core.MarketData.
"""
from decimal import Decimal
import yfinance as yf
from core.models import MarketData
def import_yahoo_finance_data(symbol,start_date,end_date):
    symbol=symbol.strip().upper(); data=yf.Ticker(symbol).history(start=start_date,end=end_date,auto_adjust=False)
    if data.empty: raise ValueError(f'No market data returned for {symbol}.')
    count=0
    for ts,row in data.iterrows():
        MarketData.objects.update_or_create(symbol=symbol,date=ts.date(),defaults={'open_price':Decimal(str(round(float(row['Open']),4))),'high_price':Decimal(str(round(float(row['High']),4))),'low_price':Decimal(str(round(float(row['Low']),4))),'close_price':Decimal(str(round(float(row['Close']),4))),'volume':int(row.get('Volume',0) or 0)}); count+=1
    return count
def get_latest_data(symbol,period='1mo'):
    data=yf.Ticker(symbol.strip().upper()).history(period=period,auto_adjust=False)
    return [{'date':ts.strftime('%Y-%m-%d'),'open':float(r['Open']),'high':float(r['High']),'low':float(r['Low']),'close':float(r['Close']),'volume':int(r.get('Volume',0) or 0)} for ts,r in data.iterrows()] if not data.empty else []
