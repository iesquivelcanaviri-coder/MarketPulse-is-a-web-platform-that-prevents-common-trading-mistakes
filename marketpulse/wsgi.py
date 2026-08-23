"""
WSGI config for marketpulse project.

This file contains the WSGI (Web Server Gateway Interface) configuration for the MarketPulse project.
WSGI is a specification that describes how a web server communicates with Python web applications.
It acts as a bridge between your Django application and the web server (like Apache, Nginx, or Gunicorn).

When you deploy your Django application to a production environment, the web server uses this file
to run your Django application. For development, Django's built-in server (manage.py runserver) 
doesn't use this file, but production servers like Gunicorn, uWSGI, or mod_wsgi do.

The MarketPulse trading platform relies on this configuration to serve web requests in production,
ensuring that all trading data, user authentication, and analytical tools are properly served
to users through the web interface.
"""

import os  # Import the os module to interact with the operating system
from django.core.wsgi import get_wsgi_application  # Import Django's WSGI application factory function

# Set the DJANGO_SETTINGS_MODULE environment variable to point to our project's settings file
# This tells Django which settings file to use when the application starts
# 'marketpulse.settings' refers to the settings.py file in the marketpulse directory
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketpulse.settings')

# Create the WSGI application instance
# get_wsgi_application() returns a WSGI-compatible application object that the web server can use
# This application object handles incoming HTTP requests and routes them through Django's request-response cycle
# For MarketPulse, this means all requests for trading data, strategy management, and user authentication
# will be processed through this application object
application = get_wsgi_application()

# The 'application' object created here is what production web servers will use to serve the MarketPulse
# trading platform. When a user accesses the platform, the web server forwards the request to this
# application, which then processes it through Django's URL routing, views, and templates to
# generate the appropriate response (HTML pages, API responses, etc.).