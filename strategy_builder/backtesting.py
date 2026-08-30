"""
============================================================
REALISTIC EDUCATIONAL BACKTEST ENGINE
============================================================
Framework mapping: views → this engine → core.MarketData → core.Backtest + BacktestTrade.
Execution model: signal from completed close; execute next session open; apply overnight gap,
commission, slippage, market-session-only execution, volume capacity and partial fills.
"""
from decimal import Decimal
import math,numpy as np,pandas as pd
from core.models import Backtest,MarketData
from .models import BacktestTrade
D=lambda x:Decimal(str(x))
def _signal(close,fast,slow,i):
    if i<slow+1:return None
    f=close.rolling(fast).mean(); s=close.rolling(slow).mean(); pf,ps=f.iloc[i-2],s.iloc[i-2]; cf,cs=f.iloc[i-1],s.iloc[i-1]
    if any(pd.isna(x) for x in [pf,ps,cf,cs]):return None
    if pf<=ps and cf>cs:return 'buy'
    if pf>=ps and cf<cs:return 'sell'
    return None
def run_backtest(strategy,start_date,end_date,initial_capital=10000):
    rules=list(strategy.rules.filter(is_active=True))
    if not rules:raise ValueError('Strategy has no active rules.')
    symbol=rules[0].symbol.upper(); params=rules[0].parameters; fast=int(params.get('fast_period',10)); slow=int(params.get('slow_period',30))
    rows=list(MarketData.objects.filter(symbol=symbol,date__gte=start_date,date__lte=end_date).order_by('date').values('date','open_price','close_price','volume'))
    if len(rows)<slow+5:raise ValueError(f'Not enough {symbol} data. Import a longer period first.')
    df=pd.DataFrame(rows); df['open_price']=df['open_price'].astype(float); df['close_price']=df['close_price'].astype(float)
    cfg=strategy.rule_config or {}; risk=float(cfg.get('risk_per_trade',.01)); stop=float(cfg.get('stop_loss_pct',.05)); commission=float(cfg.get('commission_pct',.001)); slip=float(cfg.get('slippage_pct',.0005)); volcap=float(cfg.get('max_volume_pct',.02)); daily_limit=float(cfg.get('max_daily_loss_pct',.03))
    cash=float(initial_capital); qty=0; entry=None; trade=None; costs=0.; curve=[]; pause_next_buy=False
    bt=Backtest.objects.create(strategy=strategy,symbol=symbol,start_date=start_date,end_date=end_date,initial_capital=D(initial_capital),final_capital=D(initial_capital))
    for i in range(slow+1,len(df)):
        row=df.iloc[i]; sig=_signal(df['close_price'],fast,slow,i); op=float(row.open_price); volume=max(0,int(row.volume))
        if sig=='buy' and qty==0 and not pause_next_buy:
            px=op*(1+slip); requested=max(0,math.floor((cash*risk)/max(px*stop,.01))); cash_cap=max(0,math.floor(cash/max(px*(1+commission),.01))); volume_cap=max(1,math.floor(volume*volcap)) if volume else requested; fill=min(requested,cash_cap,volume_cap)
            if fill>0:
                cost=fill*px*commission; cash-=fill*px+cost; qty=fill; entry=px; costs+=cost; trade=BacktestTrade.objects.create(backtest=bt,symbol=symbol,entry_date=row.date,entry_price=D(px),requested_quantity=requested,quantity=fill,partial_fill=fill<requested,transaction_cost=D(cost))
        elif sig=='sell' and qty>0:
            px=op*(1-slip); cost=qty*px*commission; cash+=qty*px-cost; costs+=cost; pnl=(px-entry)*qty-float(trade.transaction_cost)-cost; trade.exit_date=row.date; trade.exit_price=D(px); trade.transaction_cost=D(float(trade.transaction_cost)+cost); trade.profit_loss=D(pnl); trade.status='closed'; trade.save(); qty=0; entry=None; trade=None
        equity=round(cash+qty*float(row.close_price),2); curve.append({'date':str(row.date),'value':equity});
        if len(curve)>1:
            previous=curve[-2]['value']; pause_next_buy=((previous-equity)/previous)>daily_limit if previous>0 else False
        else: pause_next_buy=False
    if qty>0:
        row=df.iloc[-1]; px=float(row.close_price)*(1-slip); cost=qty*px*commission; cash+=qty*px-cost; costs+=cost; pnl=(px-entry)*qty-float(trade.transaction_cost)-cost; trade.exit_date=row.date; trade.exit_price=D(px); trade.transaction_cost=D(float(trade.transaction_cost)+cost); trade.profit_loss=D(pnl); trade.status='closed'; trade.save()
    values=np.array([x['value'] for x in curve] or [float(initial_capital)]); peaks=np.maximum.accumulate(values); dd=np.where(peaks>0,(peaks-values)/peaks,0); rets=np.diff(values)/values[:-1] if len(values)>1 else np.array([]); sharpe=float(np.sqrt(252)*rets.mean()/rets.std()) if len(rets)>1 and rets.std()>0 else 0
    closed=bt.trades.filter(status='closed'); total=closed.count(); wins=closed.filter(profit_loss__gt=0).count(); final=cash
    bt.final_capital=D(final); bt.total_return=D((final-float(initial_capital))/float(initial_capital)); bt.max_drawdown=D(float(dd.max()) if len(dd) else 0); bt.sharpe_ratio=D(sharpe); bt.win_rate=D(wins/total if total else 0); bt.total_trades=total; bt.transaction_costs=D(costs); bt.results={'equity_curve':curve,'execution_model':{'signal':'prior close','execution':'next session open','overnight_gap_modelled':True,'after_hours':False,'commission_pct':commission,'slippage_pct':slip,'max_volume_pct':volcap,'max_daily_loss_pct':daily_limit,'daily_loss_discipline_enforced':True}}; bt.save(); return bt
