"""============================================================ RISK FORM: browser inputs → calculators.py. ============================================================"""
from django import forms
class RiskCalculatorForm(forms.Form):
    symbol=forms.CharField(max_length=20,initial='AAPL',required=False); account_balance=forms.DecimalField(min_value=100,initial=10000); risk_percentage=forms.DecimalField(min_value=.1,max_value=10,initial=1,help_text='1 means 1%'); entry_price=forms.DecimalField(min_value=.01,initial=100); stop_loss_percentage=forms.DecimalField(min_value=.1,max_value=50,initial=5,help_text='5 means 5%'); target_price=forms.DecimalField(min_value=.01,required=False)
    def clean_symbol(self):return self.cleaned_data['symbol'].strip().upper()
