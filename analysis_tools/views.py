"""============================================================ ANALYSIS VIEWS: user strategies → analyzers.py → result templates. ============================================================"""  # Module docstring: briefly explains the purpose and data flow of this Python file.

# ============================================================
# 1. FRAMEWORK + FILE PURPOSE
# ============================================================
# DJANGO FRAMEWORK:
# Browser / User
#     ↓
# analysis_tools/urls.py
#     ↓
# analysis_tools/views.py
#     ↓
# analysis_tools/analyzers.py
#     ↓
# analysis_tools/models.py / core.models
#     ↓
# PostgreSQL
#     ↓
# Django Template
#     ↓
# Browser / User
#
# THIS FILE IS RESPONSIBLE FOR:
# 1. Receiving HTTP requests from the user.
# 2. Checking that the user is logged in.
# 3. Reading form data sent with POST requests.
# 4. Reading Strategy objects from the database.
# 5. Sending data to analyzers.py for calculations.
# 6. Reading analysis results from database models.
# 7. Sending results to Django templates.
# 8. Redirecting the user to result pages when required.
#
# PROGRAMMING LANGUAGE CONCEPTS USED:
# Imports / Modules       → reuse code from Python, Django and this project.
# Functions               → overfitting(), regime(), stress(), etc.
# Decorators              → @login_required adds authentication behaviour.
# Variables               → strategies, symbol, result, suggestion, etc.
# Objects                 → Strategy, MarketRegime, StressTest instances.
# Conditionals            → if statements choose which code should execute.
# Dictionaries            → params and suggestion store key/value pairs.
# Exceptions              → try / except handles errors safely.
# Function calls          → detect_overfitting(), identify_market_regime(), etc.
# Methods                 → .filter(), .get(), .strip(), .upper(), etc.
# Type conversion         → float() converts text input into decimal numbers.
# Return statements       → send a response back to Django.
# Django ORM              → Python communicates with the database through models.

# ============================================================
# 2. PYTHON STANDARD LIBRARY IMPORTS
# ============================================================
from datetime import date,timedelta  # Import date for today's date and timedelta for calculating date ranges.

# ============================================================
# 3. DJANGO FRAMEWORK IMPORTS
# ============================================================
from django.contrib import messages  # Import Django messages so success/error information can be displayed to the user.
from django.contrib.auth.decorators import login_required  # Import the login_required decorator so only authenticated users can access these views.
from django.shortcuts import render,redirect,get_object_or_404  # Import shortcuts for rendering HTML, redirecting pages, and safely retrieving database objects.

# ============================================================
# 4. PROJECT MODEL IMPORTS
# ============================================================
from core.models import Strategy  # Import the Strategy model from the core application so this file can work with the user's strategies.
from .models import OverfittingTest,MarketRegime,StressTest  # Import analysis result models from this application's models.py file.

# ============================================================
# 5. ANALYSIS FUNCTION IMPORTS
# ============================================================
from .analyzers import detect_overfitting,identify_market_regime,run_stress_test  # Import the calculation functions that perform the actual quantitative analysis.

# ============================================================
# 6. OVERFITTING ANALYSIS VIEW
# ============================================================
# FRAMEWORK FLOW:
# User → overfitting.html → POST → overfitting()
#      → Strategy → detect_overfitting()
#      → OverfittingTest → PostgreSQL
#      → overfitting_results()
#      → overfitting_results.html

@login_required  # Decorator concept: Django checks that the user is logged in before running this function.
def overfitting(request):  # Function definition: handles the page used to run an overfitting analysis.
    strategies=Strategy.objects.filter(user=request.user)  # Variable + ORM query: retrieve only Strategy objects belonging to the logged-in user.
    if request.method=='POST':  # Conditional statement: run the analysis only when the form has been submitted using HTTP POST.
        s=get_object_or_404(Strategy,pk=request.POST.get('strategy'),user=request.user); symbol=request.POST.get('symbol','').strip().upper(); end=date.today(); periods=[(end-timedelta(days=730),end-timedelta(days=550)),(end-timedelta(days=545),end-timedelta(days=365)),(end-timedelta(days=360),end-timedelta(days=180)),(end-timedelta(days=175),end)]  # Variables + method calls + list: get the selected Strategy, clean the ticker symbol, get today's date, and create four historical testing periods.
        try:detect_overfitting(s,symbol,periods); return redirect('analysis_tools:overfitting_results')  # Exception handling + function call: run the analyzer and redirect to the result page when successful.
        except Exception as e:messages.error(request,str(e))  # Exception handling: catch an error, convert it to text, and display it through Django messages.
    return render(request,'analysis_tools/overfitting.html',{'strategies':strategies})  # Return statement + dictionary: render the form template and give it the user's strategies.

# ============================================================
# 7. OVERFITTING RESULTS VIEW
# ============================================================
# FRAMEWORK FLOW:
# OverfittingTest database records
#     ↓
# overfitting_results()
#     ↓
# tests template variable
#     ↓
# overfitting_results.html

@login_required  # Decorator concept: prevent unauthenticated users from opening the results page.
def overfitting_results(request):return render(request,'analysis_tools/overfitting_results.html',{'tests':OverfittingTest.objects.filter(user=request.user).select_related('strategy').order_by('-created_at')})  # Function + ORM + dictionary: retrieve this user's tests, include related Strategy data efficiently, order newest first, and render the results template.

# ============================================================
# 8. MARKET REGIME ANALYSIS VIEW
# ============================================================
# FRAMEWORK FLOW:
# User enters ticker
#     ↓
# regime()
#     ↓
# identify_market_regime()
#     ↓
# MarketRegime
#     ↓
# suggestion dictionary
#     ↓
# regime.html

@login_required  # Decorator concept: require the user to be authenticated before market-regime analysis can be accessed.
def regime(request):  # Function definition: handles market-condition / market-regime analysis.
    result=None  # Variable assignment: start with no analysis result because the user may not have submitted the form yet.
    if request.method=='POST':result=identify_market_regime(request.POST.get('symbol','').strip().upper()); messages.success(request,'Regime analysis complete.') if result else messages.error(request,'Import at least 60 sessions first.')  # Conditional + function call + conditional expression: clean the ticker, analyze it, then display either success or error feedback.
    suggestion=None  # Variable assignment: begin with no strategy suggestion until an analysis result exists.
    if result:  # Conditional statement: only create a suggestion when identify_market_regime() returned a result.
        suggestion={'bull':'Trend-following rules may be more suitable; keep risk limits in place.','bear':'Reduce directional exposure and review stop-loss settings.','sideways':'Consider tighter rules and avoid assuming a strong trend.','volatile':'Reduce position risk and widen validation/stress testing.'}.get(result.regime)  # Dictionary + .get() method: use the detected regime as a key to select the matching educational suggestion.
    return render(request,'analysis_tools/regime.html',{'regime':result,'recent':MarketRegime.objects.all()[:20],'suggestion':suggestion})  # Return + ORM + dictionary: send the result, latest 20 stored regimes, and suggestion to the regime HTML template.

# ============================================================
# 9. STRESS TEST VIEW
# ============================================================
# FRAMEWORK FLOW:
# User selects Strategy + Symbol + Stress Scenario
#     ↓
# stress()
#     ↓
# params dictionary
#     ↓
# run_stress_test()
#     ↓
# StressTest
#     ↓
# PostgreSQL
#     ↓
# stress_results()

@login_required  # Decorator concept: require authentication before allowing a strategy stress test.
def stress(request):  # Function definition: handles the strategy stress-testing page.
    strategies=Strategy.objects.filter(user=request.user)  # Variable + ORM query: retrieve strategies belonging only to the logged-in user.
    if request.method=='POST':  # Conditional statement: process the stress test only after the user submits the form.
        s=get_object_or_404(Strategy,pk=request.POST.get('strategy'),user=request.user); symbol=request.POST.get('symbol','').strip().upper(); typ=request.POST.get('test_type'); params={'crash_magnitude':float(request.POST.get('crash_magnitude',.3)),'spike_magnitude':float(request.POST.get('spike_magnitude',3)),'volume_reduction':float(request.POST.get('volume_reduction',.7)),'new_trend':float(request.POST.get('new_trend',-.01))}; result=run_stress_test(s,symbol,typ,params)  # Variables + dictionary + type conversion + function call: get the selected strategy and symbol, read the test type, convert parameters to floats, and execute the stress-test analyzer.
        if result:return redirect('analysis_tools:stress_results')  # Conditional + return: if the analyzer produced a result, redirect the browser to the results page.
        messages.error(request,'Import at least 100 observations first.')  # Function call: display an error message when there is not enough stored market data for the calculation.
    return render(request,'analysis_tools/stress.html',{'strategies':strategies})  # Return + dictionary: render the stress-test page and provide the user's Strategy objects to the template.

# ============================================================
# 10. STRESS TEST RESULTS VIEW
# ============================================================
# FRAMEWORK FLOW:
# StressTest database records
#     ↓
# stress_results()
#     ↓
# tests
#     ↓
# stress_results.html

@login_required  # Decorator concept: protect the user's stress-test results behind authentication.
def stress_results(request):return render(request,'analysis_tools/stress_results.html',{'tests':StressTest.objects.filter(user=request.user).select_related('strategy').order_by('-created_at')})  # Function + ORM + dictionary: retrieve the user's stress tests, include Strategy information, order newest first, and send them to the results template.