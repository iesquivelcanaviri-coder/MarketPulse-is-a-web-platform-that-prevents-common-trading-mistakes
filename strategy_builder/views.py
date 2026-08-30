"""============================================================ STRATEGY VIEWS: forms → models/backtesting → templates. ============================================================"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from core.models import Strategy,Backtest
from .forms import StrategyCreateForm,BacktestForm
from .backtesting import run_backtest
@login_required
def strategy_list(request):return render(request,'strategy_builder/list.html',{'strategies':Strategy.objects.filter(user=request.user).prefetch_related('rules').order_by('-created_at')})
@login_required
def strategy_create(request):
    f=StrategyCreateForm(request.POST or None)
    if request.method=='POST' and f.is_valid():s=f.save(request.user); messages.success(request,'Strategy created.'); return redirect('strategy_builder:backtest',strategy_id=s.pk)
    return render(request,'strategy_builder/create.html',{'form':f})
@login_required
def backtest_strategy(request,strategy_id):
    s=get_object_or_404(Strategy,pk=strategy_id,user=request.user); f=BacktestForm(request.POST or None)
    if request.method=='POST' and f.is_valid():
        try:b=run_backtest(s,**f.cleaned_data); return redirect('strategy_builder:results',backtest_id=b.pk)
        except Exception as e:messages.error(request,str(e))
    return render(request,'strategy_builder/backtest_form.html',{'strategy':s,'form':f})
@login_required
def backtest_results(request,backtest_id):
    b=get_object_or_404(Backtest,pk=backtest_id,strategy__user=request.user); return render(request,'strategy_builder/backtest_results.html',{'backtest':b,'trades':b.trades.all()})
