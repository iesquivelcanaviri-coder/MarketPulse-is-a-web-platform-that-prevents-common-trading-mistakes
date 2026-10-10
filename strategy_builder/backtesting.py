"""
============================================================
REALISTIC EDUCATIONAL BACKTEST ENGINE
============================================================
Framework mapping: views → this engine → core.MarketData → core.Backtest + BacktestTrade.
Execution model: signal from completed close; execute next session open; apply overnight gap,
commission, slippage, market-session-only execution, volume capacity and partial fills.
"""

# ============================================================
# 1. IMPORTS AND DECIMAL CONVERSION
# ============================================================
from decimal import Decimal  # Import: I use Decimal when preparing values for database storage.
import math, numpy as np, pandas as pd  # Imports and aliases: I use maths helpers, NumPy arrays and pandas tables.
from core.models import Backtest, MarketData  # Model imports: I access saved backtests and historical market data.
from .models import BacktestTrade  # Relative import: I access this application's simulated-trade model.
D = lambda x: Decimal(str(x))  # Lambda and conversion: I convert a value through its string representation into Decimal.

# ============================================================
# 2. MOVING-AVERAGE CROSSOVER SIGNAL
# ============================================================
def _signal(close, fast, slow, i):  # Function and parameters: I receive closing prices, periods and the current row index.
    if i < slow + 1:  # Conditional: I check whether enough earlier observations are available.
        return None  # Early return: I report no signal when the history is too short.
    f = close.rolling(fast).mean()  # Method chaining: I calculate the fast rolling moving average.
    s = close.rolling(slow).mean()  # Method chaining: I calculate the slow rolling moving average.
    pf, ps = f.iloc[i - 2], s.iloc[i - 2]  # Tuple unpacking and positional indexing: I read the earlier pair of averages.
    cf, cs = f.iloc[i - 1], s.iloc[i - 1]  # Positional indexing: I read the latest completed row's averages.
    if any(pd.isna(x) for x in [pf, ps, cf, cs]):  # Generator expression and any: I check whether any required average is missing.
        return None  # Early return: I avoid producing a signal from missing values.
    if pf <= ps and cf > cs:  # Comparisons and logical AND: I detect the fast average crossing above the slow average.
        return 'buy'  # String return: I identify a buy signal.
    if pf >= ps and cf < cs:  # Comparisons and logical AND: I detect the fast average crossing below the slow average.
        return 'sell'  # String return: I identify a sell signal.
    return None  # Default return: I report no crossover.

# ============================================================
# 3. BACKTEST INPUTS AND HISTORICAL DATA
# ============================================================
def run_backtest(strategy, start_date, end_date, initial_capital=10000):  # Function and default argument: I define the historical simulation.
    rules = list(strategy.rules.filter(is_active=True))  # ORM query and list conversion: I load the strategy's active rules.
    if not rules:  # Conditional and logical NOT: I check for an empty rule list.
        raise ValueError('Strategy has no active rules.')  # Exception: I stop when there are no active rules.
    symbol = rules[0].symbol.upper()  # Indexing and string method: I use the first active rule's uppercase symbol.
    params = rules[0].parameters  # Attribute access: I use the first active rule's parameter dictionary.
    fast = int(params.get('fast_period', 10))  # Dictionary lookup and conversion: I read the fast period, defaulting to ten.
    slow = int(params.get('slow_period', 30))  # Dictionary lookup and conversion: I read the slow period, defaulting to thirty.
    rows = list(  # List conversion: I evaluate the historical-data query.
        MarketData.objects.filter(  # ORM filtering: I select the requested asset and inclusive date range.
            symbol=symbol,  # Keyword argument: I match the selected symbol.
            date__gte=start_date,  # Lookup suffix: I include dates greater than or equal to the start date.
            date__lte=end_date,  # Lookup suffix: I include dates less than or equal to the end date.
        ).order_by('date').values('date', 'open_price', 'close_price', 'volume')  # Method chaining: I sort oldest first and retrieve dictionaries of selected fields.
    )  # Closing parenthesis: I finish loading the historical rows.
    if len(rows) < slow + 5:  # Length and comparison: I enforce the engine's minimum observation count.
        raise ValueError(f'Not enough {symbol} data. Import a longer period first.')  # Exception and formatted string: I explain why the test cannot run.
    df = pd.DataFrame(rows)  # Object construction: I organise the historical records into a pandas table.
    df['open_price'] = df['open_price'].astype(float)  # Column assignment and conversion: I prepare opening prices for floating-point calculations.
    df['close_price'] = df['close_price'].astype(float)  # Column assignment: I prepare closing prices in the same way.

    # --------------------------------------------------------
    # 3.1 RISK AND EXECUTION CONFIGURATION
    # --------------------------------------------------------
    cfg = strategy.rule_config or {}  # Fallback expression: I use an empty dictionary when configuration is falsey.
    risk = float(cfg.get('risk_per_trade', .01))  # Lookup and conversion: I read the position-sizing risk fraction.
    stop = float(cfg.get('stop_loss_pct', .05))  # Lookup: I read the stop fraction used in position sizing.
    commission = float(cfg.get('commission_pct', .001))  # Lookup: I read the simulated commission rate.
    slip = float(cfg.get('slippage_pct', .0005))  # Lookup: I read the simulated slippage rate.
    volcap = float(cfg.get('max_volume_pct', .02))  # Lookup: I read the entry-volume capacity fraction.
    daily_limit = float(cfg.get('max_daily_loss_pct', .03))  # Lookup: I read the equity-loss threshold for pausing purchases.

    # --------------------------------------------------------
    # 3.2 INITIAL SIMULATION STATE
    # --------------------------------------------------------
    cash = float(initial_capital)  # Variable assignment: I initialise available cash.
    qty = 0  # Integer state: I begin without an open position.
    entry = None  # None value: I begin without an entry price.
    trade = None  # None value: I begin without a current trade record.
    costs = 0.  # Float state: I initialise accumulated commission costs.
    curve = []  # List: I prepare a collection of dated equity values.
    pause_next_buy = False  # Boolean state: I initially allow purchases.
    bt = Backtest.objects.create(  # ORM method: I create and save the parent backtest record.
        strategy=strategy,  # Relationship: I link the backtest to its strategy.
        symbol=symbol,  # Keyword argument: I record the tested asset.
        start_date=start_date,  # Keyword argument: I record the requested starting date.
        end_date=end_date,  # Keyword argument: I record the requested ending date.
        initial_capital=D(initial_capital),  # Helper call: I store starting capital as Decimal.
        final_capital=D(initial_capital),  # Initial placeholder: I begin final capital at the starting value.
    )  # Closing call: I finish creating the backtest.

# ============================================================
# 4. PROCESS EACH HISTORICAL OBSERVATION
# ============================================================
    for i in range(slow + 1, len(df)):  # Loop and range: I iterate after the moving-average warm-up period.
        row = df.iloc[i]  # Positional indexing: I retrieve the current historical row.
        sig = _signal(df['close_price'], fast, slow, i)  # Function call: I calculate a signal from preceding closing prices.
        op = float(row.open_price)  # Attribute access and conversion: I read the current row's opening price.
        volume = max(0, int(row.volume))  # Conversion and maximum: I prevent a negative volume value.

        # ----------------------------------------------------
        # 4.1 BUY SIGNAL AND POSITION SIZING
        # ----------------------------------------------------
        if sig == 'buy' and qty == 0 and not pause_next_buy:  # Combined condition: I buy only when flat and purchases are allowed.
            px = op * (1 + slip)  # Arithmetic: I increase the opening price to simulate adverse buy slippage.
            requested = max(0, math.floor((cash * risk) / max(px * stop, .01)))  # Position sizing: I divide the risk budget by estimated risk per unit.
            cash_cap = max(0, math.floor(cash / max(px * (1 + commission), .01)))  # Capacity calculation: I estimate affordable units including entry commission.
            volume_cap = max(1, math.floor(volume * volcap)) if volume else requested  # Conditional expression: I calculate entry capacity, or use requested quantity when volume is zero.
            fill = min(requested, cash_cap, volume_cap)  # Minimum: I restrict the entry to the smallest quantity limit.
            if fill > 0:  # Conditional: I create a position only when at least one unit can be filled.
                cost = fill * px * commission  # Arithmetic: I calculate entry commission.
                cash -= fill * px + cost  # Augmented assignment: I deduct the purchase value and commission.
                qty = fill  # State assignment: I record the filled position size.
                entry = px  # State assignment: I remember the simulated entry price.
                costs += cost  # Accumulation: I add entry commission to total costs.
                trade = BacktestTrade.objects.create(  # ORM method: I create and save the simulated trade.
                    backtest=bt,  # Relationship: I link the trade to its parent backtest.
                    symbol=symbol,  # Keyword argument: I record the asset symbol.
                    entry_date=row.date,  # Attribute access: I record the current row's date.
                    entry_price=D(px),  # Helper call: I store the simulated entry price as Decimal.
                    requested_quantity=requested,  # Keyword argument: I preserve the original requested quantity.
                    quantity=fill,  # Keyword argument: I record the actual simulated fill.
                    partial_fill=fill < requested,  # Boolean comparison: I mark whether fewer units were filled than requested.
                    transaction_cost=D(cost),  # Helper call: I store entry commission.
                )  # Closing call: I finish creating the trade.

        # ----------------------------------------------------
        # 4.2 SELL SIGNAL AND POSITION CLOSURE
        # ----------------------------------------------------
        elif sig == 'sell' and qty > 0:  # Alternative branch: I sell when a sell signal exists and a position is open.
            px = op * (1 - slip)  # Arithmetic: I reduce the opening price for adverse sell slippage.
            cost = qty * px * commission  # Arithmetic: I calculate exit commission.
            cash += qty * px - cost  # Augmented assignment: I add sale proceeds after commission.
            costs += cost  # Accumulation: I add exit commission to total costs.
            pnl = (px - entry) * qty - float(trade.transaction_cost) - cost  # Arithmetic: I calculate profit or loss after both commissions.
            trade.exit_date = row.date  # Attribute assignment: I record the exit date.
            trade.exit_price = D(px)  # Attribute assignment: I record the simulated exit price.
            trade.transaction_cost = D(float(trade.transaction_cost) + cost)  # Accumulation: I combine entry and exit commission.
            trade.profit_loss = D(pnl)  # Attribute assignment: I store net simulated profit or loss.
            trade.status = 'closed'  # String assignment: I mark the trade closed.
            trade.save()  # ORM method: I persist the changed trade fields.
            qty = 0  # State reset: I clear the open position quantity.
            entry = None  # State reset: I clear the entry price.
            trade = None  # State reset: I clear the current trade reference.

        # ----------------------------------------------------
        # 4.3 EQUITY CURVE AND PURCHASE-PAUSE FLAG
        # ----------------------------------------------------
        equity = round(cash + qty * float(row.close_price), 2)  # Arithmetic and rounding: I value cash plus the open position at the current close.
        curve.append({'date': str(row.date), 'value': equity})  # List method and dictionary: I add a dated equity observation.
        if len(curve) > 1:  # Conditional: I compare equity only when an earlier observation exists.
            previous = curve[-2]['value']  # Negative indexing and dictionary lookup: I retrieve the preceding equity value.
            pause_next_buy = ((previous - equity) / previous) > daily_limit if previous > 0 else False  # Conditional expression: I pause purchases after a decline exceeding the limit.
        else:  # Alternative branch: I handle the first equity observation.
            pause_next_buy = False  # Boolean assignment: I leave purchases allowed when no comparison exists.

# ============================================================
# 5. CLOSE ANY POSITION REMAINING AT THE END
# ============================================================
    if qty > 0:  # Conditional: I check for a position still open after the loop.
        row = df.iloc[-1]  # Negative positional indexing: I retrieve the final historical row.
        px = float(row.close_price) * (1 - slip)  # Arithmetic: I simulate final liquidation at the last close with slippage.
        cost = qty * px * commission  # Arithmetic: I calculate the liquidation commission.
        cash += qty * px - cost  # Augmented assignment: I add net liquidation proceeds.
        costs += cost  # Accumulation: I include the final commission in total costs.
        pnl = (px - entry) * qty - float(trade.transaction_cost) - cost  # Arithmetic: I calculate the final trade's net profit or loss.
        trade.exit_date = row.date  # Attribute assignment: I record the final row's date as the exit date.
        trade.exit_price = D(px)  # Attribute assignment: I store the liquidation price.
        trade.transaction_cost = D(float(trade.transaction_cost) + cost)  # Accumulation: I combine entry and liquidation commissions.
        trade.profit_loss = D(pnl)  # Attribute assignment: I store net trade profit or loss.
        trade.status = 'closed'  # String assignment: I mark the final trade closed.
        trade.save()  # ORM method: I save the updated trade.

# ============================================================
# 6. PERFORMANCE CALCULATIONS
# ============================================================
    values = np.array([x['value'] for x in curve] or [float(initial_capital)])  # List comprehension and fallback: I build an equity array, using starting capital if empty.
    peaks = np.maximum.accumulate(values)  # NumPy accumulation: I calculate the running maximum equity.
    dd = np.where(peaks > 0, (peaks - values) / peaks, 0)  # Array calculation: I measure fractional declines from running peaks.
    rets = np.diff(values) / values[:-1] if len(values) > 1 else np.array([])  # Differences and slicing: I calculate consecutive equity returns when possible.
    sharpe = float(np.sqrt(252) * rets.mean() / rets.std()) if len(rets) > 1 and rets.std() > 0 else 0  # Conditional calculation: I annualise mean return divided by standard deviation using 252 periods.
    closed = bt.trades.filter(status='closed')  # Related-manager query: I select this backtest's closed trades.
    total = closed.count()  # ORM method: I count closed trades.
    wins = closed.filter(profit_loss__gt=0).count()  # Lookup and count: I count trades with positive net profit.
    final = cash  # Assignment: I use cash after all simulated positions have been closed.

# ============================================================
# 7. SAVE METRICS AND EXECUTION METADATA
# ============================================================
    bt.final_capital = D(final)  # Attribute assignment: I store ending capital.
    bt.total_return = D((final - float(initial_capital)) / float(initial_capital))  # Arithmetic: I store total return as a fraction.
    bt.max_drawdown = D(float(dd.max()) if len(dd) else 0)  # Conditional expression: I store the largest measured equity drawdown.
    bt.sharpe_ratio = D(sharpe)  # Attribute assignment: I store the calculated Sharpe-style ratio.
    bt.win_rate = D(wins / total if total else 0)  # Conditional expression: I store the winning-trade fraction without dividing by zero.
    bt.total_trades = total  # Attribute assignment: I store the closed-trade count.
    bt.transaction_costs = D(costs)  # Attribute assignment: I store accumulated commission costs.
    bt.results = {  # Dictionary assignment: I prepare structured result data.
        'equity_curve': curve,  # Key-value pair: I store the dated equity observations.
        'execution_model': {  # Nested dictionary: I describe the engine's execution assumptions.
            'signal': 'prior close',  # String metadata: I describe the signal timing.
            'execution': 'next session open',  # String metadata: I describe normal signal-based execution.
            'overnight_gap_modelled': True,  # Boolean metadata: I record that execution uses the following row's open.
            'after_hours': False,  # Boolean metadata: I record the intended session-only assumption.
            'commission_pct': commission,  # Numeric metadata: I record the commission rate used.
            'slippage_pct': slip,  # Numeric metadata: I record the slippage rate used.
            'max_volume_pct': volcap,  # Numeric metadata: I record the entry-volume capacity setting.
            'max_daily_loss_pct': daily_limit,  # Numeric metadata: I record the purchase-pause threshold.
            'daily_loss_discipline_enforced': True,  # Boolean metadata: I preserve the original flag describing the purchase-pause logic.
        },  # Closing brace: I finish the execution metadata.
    }  # Closing brace: I finish the results dictionary.
    bt.save()  # ORM method: I persist the completed backtest results.
    return bt  # Return statement: I give the calling view the saved Backtest instance.