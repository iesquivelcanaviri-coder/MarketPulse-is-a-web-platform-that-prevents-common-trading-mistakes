"""============================================================ RISK VIEWS: form → calculators → RiskSnapshot → templates. ============================================================"""
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .forms import RiskCalculatorForm
from .models import RiskSnapshot
from .calculators import *
@login_required
def calculator(request):
    f=RiskCalculatorForm(request.POST or None); result=None
    if request.method=='POST' and f.is_valid():
        d=f.cleaned_data; base=float(d['risk_percentage'])/100; stop=float(d['stop_loss_percentage'])/100; vol=calculate_volatility(d['symbol']) if d['symbol'] else 0; adj=volatility_adjusted_risk(base,vol); size=calculate_position_size(d['account_balance'],adj,stop,d['entry_price']); sl=calculate_stop_loss(d['entry_price'],stop); rr=calculate_risk_reward_ratio(d['entry_price'],sl,d['target_price']) if d.get('target_price') else None; result={'position_size':size,'stop_loss':sl,'volatility':vol,'adjusted_risk_pct':adj*100,'risk_reward':rr}; RiskSnapshot.objects.create(user=request.user,symbol=d['symbol'],account_balance=d['account_balance'],risk_percentage=Decimal(str(adj)),volatility=Decimal(str(vol)),recommended_position_size=Decimal(str(size)),stop_loss_price=Decimal(str(sl)))
    return render(request,'risk_management/calculator.html',{'form':f,'result':result})
@login_required
def dashboard(request):return render(request,'risk_management/dashboard.html',{'snapshots':RiskSnapshot.objects.filter(user=request.user).order_by('-created_at')[:20],'profile':getattr(request.user,'profile',None)})
