"""============================================================ ANALYSIS VIEWS: user strategies → analyzers.py → result templates. ============================================================"""
from datetime import date,timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from core.models import Strategy
from .models import OverfittingTest,MarketRegime,StressTest
from .analyzers import detect_overfitting,identify_market_regime,run_stress_test
@login_required
def overfitting(request):
    strategies=Strategy.objects.filter(user=request.user)
    if request.method=='POST':
        s=get_object_or_404(Strategy,pk=request.POST.get('strategy'),user=request.user); symbol=request.POST.get('symbol','').strip().upper(); end=date.today(); periods=[(end-timedelta(days=730),end-timedelta(days=550)),(end-timedelta(days=545),end-timedelta(days=365)),(end-timedelta(days=360),end-timedelta(days=180)),(end-timedelta(days=175),end)]
        try:detect_overfitting(s,symbol,periods); return redirect('analysis_tools:overfitting_results')
        except Exception as e:messages.error(request,str(e))
    return render(request,'analysis_tools/overfitting.html',{'strategies':strategies})
@login_required
def overfitting_results(request):return render(request,'analysis_tools/overfitting_results.html',{'tests':OverfittingTest.objects.filter(user=request.user).select_related('strategy').order_by('-created_at')})
@login_required
def regime(request):
    result=None
    if request.method=='POST':result=identify_market_regime(request.POST.get('symbol','').strip().upper()); messages.success(request,'Regime analysis complete.') if result else messages.error(request,'Import at least 60 sessions first.')
    suggestion=None
    if result:
        suggestion={'bull':'Trend-following rules may be more suitable; keep risk limits in place.','bear':'Reduce directional exposure and review stop-loss settings.','sideways':'Consider tighter rules and avoid assuming a strong trend.','volatile':'Reduce position risk and widen validation/stress testing.'}.get(result.regime)
    return render(request,'analysis_tools/regime.html',{'regime':result,'recent':MarketRegime.objects.all()[:20],'suggestion':suggestion})
@login_required
def stress(request):
    strategies=Strategy.objects.filter(user=request.user)
    if request.method=='POST':
        s=get_object_or_404(Strategy,pk=request.POST.get('strategy'),user=request.user); symbol=request.POST.get('symbol','').strip().upper(); typ=request.POST.get('test_type'); params={'crash_magnitude':float(request.POST.get('crash_magnitude',.3)),'spike_magnitude':float(request.POST.get('spike_magnitude',3)),'volume_reduction':float(request.POST.get('volume_reduction',.7)),'new_trend':float(request.POST.get('new_trend',-.01))}; result=run_stress_test(s,symbol,typ,params)
        if result:return redirect('analysis_tools:stress_results')
        messages.error(request,'Import at least 100 observations first.')
    return render(request,'analysis_tools/stress.html',{'strategies':strategies})
@login_required
def stress_results(request):return render(request,'analysis_tools/stress_results.html',{'tests':StressTest.objects.filter(user=request.user).select_related('strategy').order_by('-created_at')})
