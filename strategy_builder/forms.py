"""
============================================================
STRATEGY BUILDER - FORMS
============================================================
Framework mapping: create form writes core.Strategy + two IF/THEN StrategyRule rows;
backtest form supplies dates/capital to backtesting.py.
"""
from django import forms
from core.models import Strategy
from .models import StrategyRule
class StrategyCreateForm(forms.Form):
    name=forms.CharField(max_length=120); description=forms.CharField(widget=forms.Textarea(attrs={'rows':3}),required=False); symbol=forms.CharField(max_length=20,initial='AAPL'); fast_period=forms.IntegerField(min_value=2,initial=10); slow_period=forms.IntegerField(min_value=3,initial=30); risk_per_trade=forms.DecimalField(min_value=.001,max_value=.10,initial=.01,decimal_places=3); stop_loss_pct=forms.DecimalField(min_value=.005,max_value=.5,initial=.05,decimal_places=3); commission_pct=forms.DecimalField(min_value=0,max_value=.05,initial=.001,decimal_places=4); slippage_pct=forms.DecimalField(min_value=0,max_value=.05,initial=.0005,decimal_places=4); max_volume_pct=forms.DecimalField(min_value=.0001,max_value=.10,initial=.02,decimal_places=4); max_daily_loss_pct=forms.DecimalField(min_value=.001,max_value=.20,initial=.03,decimal_places=3,help_text='Backtest discipline limit; 0.03 means 3%')
    def clean(self):
        d=super().clean()
        if d.get('fast_period') and d.get('slow_period') and d['fast_period']>=d['slow_period']: raise forms.ValidationError('Fast period must be smaller than slow period.')
        return d
    def save(self,user):
        symbol=self.cleaned_data['symbol'].strip().upper(); cfg={k:float(self.cleaned_data[k]) for k in ['risk_per_trade','stop_loss_pct','commission_pct','slippage_pct','max_volume_pct','max_daily_loss_pct']}
        s=Strategy.objects.create(user=user,name=self.cleaned_data['name'],description=self.cleaned_data['description'],rule_config=cfg); p={'fast_period':self.cleaned_data['fast_period'],'slow_period':self.cleaned_data['slow_period']}
        StrategyRule.objects.create(strategy=s,name='IF fast MA crosses above slow MA THEN buy',symbol=symbol,condition_type='ma_cross_up',action='buy',parameters=p)
        StrategyRule.objects.create(strategy=s,name='IF fast MA crosses below slow MA THEN sell',symbol=symbol,condition_type='ma_cross_down',action='sell',parameters=p)
        return s
class BacktestForm(forms.Form):
    start_date=forms.DateField(widget=forms.DateInput(attrs={'type':'date'})); end_date=forms.DateField(widget=forms.DateInput(attrs={'type':'date'})); initial_capital=forms.DecimalField(min_value=100,initial=10000)
    def clean(self):
        d=super().clean()
        if d.get('start_date') and d.get('end_date') and d['start_date']>=d['end_date']: raise forms.ValidationError('End date must be after start date.')
        return d
