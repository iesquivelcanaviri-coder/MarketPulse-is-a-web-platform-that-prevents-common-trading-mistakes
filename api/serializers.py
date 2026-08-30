"""
============================================================
API SERIALIZERS
============================================================
Framework mapping: Django models → JSON structures returned to React.
"""
from rest_framework import serializers
from core.models import MarketData,Strategy,Backtest
class MarketDataSerializer(serializers.ModelSerializer):
    class Meta: model=MarketData; fields=('symbol','date','open_price','high_price','low_price','close_price','volume')
class StrategySerializer(serializers.ModelSerializer):
    class Meta: model=Strategy; fields=('id','name','description','is_active','rule_config','created_at'); read_only_fields=('id','created_at')
class BacktestSerializer(serializers.ModelSerializer):
    strategy_name=serializers.CharField(source='strategy.name',read_only=True)
    class Meta: model=Backtest; fields=('id','strategy','strategy_name','symbol','start_date','end_date','initial_capital','final_capital','total_return','max_drawdown','sharpe_ratio','win_rate','total_trades','transaction_costs','results')
