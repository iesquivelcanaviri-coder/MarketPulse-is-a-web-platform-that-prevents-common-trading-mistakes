"""
============================================================
ANALYSIS SERVICES
============================================================
Framework mapping: views call these transparent educational heuristics; functions read MarketData
and persist OverfittingTest, MarketRegime and StressTest records.
"""
from decimal import Decimal
from datetime import date,timedelta
import numpy as np,pandas as pd
from core.models import MarketData
from .models import OverfittingTest,MarketRegime,StressTest
D=lambda x:Decimal(str(x))
def _frame(symbol,start,end):
    rows=list(MarketData.objects.filter(symbol=symbol.upper(),date__gte=start,date__lte=end).order_by('date').values('date','open_price','high_price','low_price','close_price','volume'))
    if not rows:return pd.DataFrame()
    df=pd.DataFrame(rows)
    for c in ['open_price','high_price','low_price','close_price']:df[c]=df[c].astype(float)
    return df
def _ma_return(df,fast=10,slow=30):
    if len(df)<slow+2:return 0.
    c=df.close_price; sig=(c.rolling(fast).mean()>c.rolling(slow).mean()).astype(int); r=c.pct_change().fillna(0); return float((1+r*sig.shift(1).fillna(0)).prod()-1)
def detect_overfitting(strategy,symbol,periods):
    r=strategy.rules.first(); p=r.parameters if r else {}; fast=int(p.get('fast_period',10)); slow=int(p.get('slow_period',30)); out=[]
    for a,b in periods:
        split=a+(b-a)*.7; ins=_ma_return(_frame(symbol,a,split),fast,slow); outs=_ma_return(_frame(symbol,split+timedelta(days=1),b),fast,slow); score=max(0,min(1,(ins-outs)/max(abs(ins),.01))) if ins>outs else 0; bad=score>.3; rec='Stable across this window.' if not bad else 'Large out-of-sample deterioration: simplify rules, reduce tuning and test more unseen data.'; out.append(OverfittingTest.objects.create(user=strategy.user,strategy=strategy,symbol=symbol.upper(),test_period=f'{a} to {b}',in_sample_return=D(ins),out_sample_return=D(outs),overfitting_score=D(score),is_overfitted=bad,recommendations=rec))
    return out
def identify_market_regime(symbol):
    end=date.today(); df=_frame(symbol,end-timedelta(days=300),end)
    if len(df)<60:return None
    c=df.close_price; vol=float(c.pct_change().dropna().std()*np.sqrt(252)); ma20=float(c.rolling(20).mean().iloc[-1]); ma60=float(c.rolling(60).mean().iloc[-1]); cur=float(c.iloc[-1]); trend=(ma20/ma60-1) if ma60 else 0
    regime='volatile' if vol>.4 else 'bull' if cur>ma20>ma60 and trend>.01 else 'bear' if cur<ma20<ma60 and trend<-.01 else 'sideways'; conf=min(1,abs(trend)*10+min(vol,.5)); obj,_=MarketRegime.objects.update_or_create(symbol=symbol.upper(),date=end,defaults={'regime':regime,'confidence':D(conf),'volatility':D(vol),'trend_strength':D(trend)}); return obj
def run_stress_test(strategy,symbol,test_type,params):
    end=date.today(); df=_frame(symbol,end-timedelta(days=730),end).reset_index(drop=True)
    if len(df)<100:return None
    n=len(df)
    if test_type=='crash':start=int(n*.7); df.loc[start:,['open_price','high_price','low_price','close_price']]*=(1-float(params.get('crash_magnitude',.3)))
    elif test_type=='volatility_spike':
        rng=np.random.default_rng(42); start=int(n*.5); dur=max(1,int(n*.1)); base=df.close_price.pct_change().std() or .01
        for i in range(start,min(start+dur,n)):df.loc[i,'close_price']*=max(.05,1+rng.normal(0,base*float(params.get('spike_magnitude',3))))
    elif test_type=='liquidity_crisis':start=int(n*.6); dur=max(1,int(n*.2)); df.loc[start:start+dur,'volume']*=(1-float(params.get('volume_reduction',.7)))
    elif test_type=='regime_change':
        start=int(n*.5); trend=float(params.get('new_trend',-.01))
        for i in range(start,n):df.loc[i,['open_price','high_price','low_price','close_price']]*=max(.05,1+trend)
    r=df.close_price.pct_change().fillna(0); cum=(1+r).cumprod(); peak=cum.cummax(); dd=(peak-cum)/peak.replace(0,np.nan); m=float(dd.max() or 0); trough=int(dd.idxmax()) if len(dd) else 0; recovery=len(cum)-trough
    score=max(0,min(1,1-m*1.5-min(recovery,180)/360)); passed=score>=.5; notes=f'Max drawdown {m:.2%}; estimated recovery {recovery} sessions. '+('Passed.' if passed else 'Review position sizing and rule complexity.')
    return StressTest.objects.create(user=strategy.user,strategy=strategy,symbol=symbol.upper(),test_type=test_type,test_parameters=params,max_drawdown=D(m),recovery_time=recovery,robustness_score=D(score),passed_test=passed,notes=notes)
