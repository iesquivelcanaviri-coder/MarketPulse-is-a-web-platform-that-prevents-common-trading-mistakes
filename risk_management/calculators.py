"""
============================================================
RISK CALCULATORS
============================================================
Framework mapping: Django view + DRF API call these pure functions; volatility reads core.MarketData.
"""
import math,numpy as np
from core.models import MarketData
def calculate_position_size(account_balance,risk_percentage,stop_loss_pct,entry_price):
    a,r,s,p=map(float,[account_balance,risk_percentage,stop_loss_pct,entry_price])
    if min(a,r,s,p)<=0:raise ValueError('All values must be greater than zero.')
    return (a*r)/(p*s)
def calculate_stop_loss(entry_price,stop_loss_pct=.05):return float(entry_price)*(1-float(stop_loss_pct))
def calculate_risk_reward_ratio(entry,stop,target):
    risk=abs(float(entry)-float(stop)); return abs(float(target)-float(entry))/risk if risk else 0
def calculate_volatility(symbol,period=60):
    xs=list(MarketData.objects.filter(symbol=symbol.upper()).order_by('-date').values_list('close_price',flat=True)[:period+1])
    if len(xs)<3:return 0.
    p=np.array([float(x) for x in reversed(xs)]); r=np.diff(p)/p[:-1]; return float(np.std(r,ddof=1)*math.sqrt(252)) if len(r)>1 else 0.
def volatility_adjusted_risk(base,vol):
    base=float(base); vol=float(vol)
    return base*.5 if vol>=.5 else base*.7 if vol>=.3 else base*.85 if vol>=.2 else base
