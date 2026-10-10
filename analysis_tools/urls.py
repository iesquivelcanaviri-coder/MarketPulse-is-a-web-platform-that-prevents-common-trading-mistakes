"""============================================================ ANALYSIS URLS: `/analysis/` → overfitting/regime/stress. ============================================================"""  # Module docstring: briefly explains that this file controls the URLs for the Analysis Tools area.

# ============================================================
# 1. DJANGO FRAMEWORK IMPORT
# ============================================================

from django.urls import path  # Import: brings Django's path() function into this Python module so URL routes can be created.

# ============================================================
# 2. LOCAL APPLICATION IMPORT
# ============================================================

from . import views  # Relative import: imports analysis_tools/views.py so these URLs can call the application's view functions.

# ============================================================
# 3. APPLICATION URL NAMESPACE
# ============================================================

app_name='analysis_tools'  # Variable assignment + string: gives this app a URL namespace such as analysis_tools:regime.

# ============================================================
# 4. ANALYSIS URL PATTERNS
# ============================================================

urlpatterns=[  # Variable + list: Django expects urlpatterns to contain the URL routes available inside this application.
    path('overfitting/',views.overfitting,name='overfitting'),  # Function call: /analysis/overfitting/ is routed to the overfitting() view.
    path('overfitting/results/',views.overfitting_results,name='overfitting_results'),  # Function call: routes the overfitting results URL to overfitting_results().
    path('regime/',views.regime,name='regime'),  # Function call: /analysis/regime/ is routed to the regime() view for market-regime analysis.
    path('stress/',views.stress,name='stress'),  # Function call: /analysis/stress/ is routed to the stress() view for stress testing.
    path('stress/results/',views.stress_results,name='stress_results')  # Function call: routes the stress-test results URL to stress_results().
]  # List closing bracket: finishes the collection of URL patterns used by Django.