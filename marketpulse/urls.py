"""
URL configuration for marketpulse project.

This file is the main URL router for the entire MarketPulse application.
It defines how incoming URL requests are mapped to specific views or
other URL configuration modules.

Django processes URLs in the order they're listed in urlpatterns.
The first matching pattern is used, so order matters!

Each path() function takes:
1. A route pattern (string)
2. A view function or include() directive
3. Optional name parameter for reverse URL lookup
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

# urlpatterns is a list that contains all the URL patterns for our project
# Django checks each pattern in order when processing a request
urlpatterns = [
    # Admin interface route
    # This maps to Django's built-in admin site where you can manage database records
    # Accessible at http://127.0.0.1:8000/admin/
    path('admin/', admin.site.urls),
    
    # Home page route
    # Uses TemplateView to render a simple template without custom logic
    # This is our landing page that introduces MarketPulse to visitors
    # The 'name' parameter lets us reference this URL in templates as {% url 'home' %}
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Dashboard route
    # This is the main interface for authenticated users
    # Shows portfolio overview, active strategies, and recent alerts
    # Protected by login requirements in the template or view
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    
    # Accounts app routes
    # include() tells Django to look for additional URL patterns in accounts/urls.py
    # This handles user registration, login, logout, and profile management
    # All URLs starting with 'accounts/' will be passed to the accounts app for processing
    # Examples: /accounts/login/, /accounts/register/, /accounts/profile/
    path('accounts/', include('accounts.urls')),
    
    # Data management app routes
    # Handles importing and managing market data from sources like Yahoo Finance
    # Includes data import history, validation, and source management
    # Examples: /data/import/, /data/history/, /data/sources/
    path('data/', include('data_management.urls')),
    
    # Strategy builder app routes
    # Manages trading strategy creation, backtesting, and performance analysis
    # Users can create, test, and optimize trading strategies here
    # Examples: /strategy/create/, /strategy/backtest/, /strategy/results/
    path('strategy/', include('strategy_builder.urls')),
    
    # Risk management app routes
    # Provides tools for position sizing, stop-loss calculation, and risk assessment
    # Helps users manage and monitor their trading risk
    # Examples: /risk/calculator/, /risk/limits/, /risk/portfolio/
    path('risk/', include('risk_management.urls')),
    
    # Analysis tools app routes
    # Contains advanced analysis features like overfitting detection and market regime analysis
    # These tools help users validate their strategies and understand market conditions
    # Examples: /analysis/overfitting/, /analysis/regime/, /analysis/stress-test/
    path('analysis/', include('analysis_tools.urls')),
]

"""
How URL routing works in Django:

1. When a request comes in (e.g., http://127.0.0.1:8000/accounts/login/):
   - Django strips the domain and looks at the path: /accounts/login/
   - It checks each pattern in urlpatterns in order

2. It finds a match with path('accounts/', include('accounts.urls')):
   - The 'accounts/' part matches the beginning of the URL
   - The remaining 'login/' part is passed to the accounts.urls.py file

3. In accounts/urls.py, Django looks for a pattern matching 'login/':
   - It would find something like path('login/', views.login_view, name='login')
   - This maps to the login_view function in accounts/views.py

4. The view function processes the request and returns a response

The include() function is crucial for modular applications:
- It allows each app to manage its own URL patterns
- Keeps the main urls.py file clean and organized
- Enables app reuse across different projects

The name parameter is used for reverse URL lookup:
- In templates: {% url 'home' %} generates the URL for the home page
- In views: redirect('home') redirects to the home page
- This makes URLs maintainable - you can change the URL pattern in one place
"""