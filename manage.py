#!/usr/bin/env python

"""Django's command-line utility for administrative tasks."""
# STUDENT NOTE: We import the 'os' module first. This module allows us to interact with the operating system,
# like accessing environment variables. In Django, environment variables are often used to store configuration
# settings like database credentials, secret keys, etc.
import os
# STUDENT NOTE: We import the 'sys' module next. This module provides access to system-specific parameters
# and functions. The most important part for us is 'sys.argv', which is a list that contains command-line
# arguments passed to the script. For example, when you run "python manage.py runserver", sys.argv will be
# ['manage.py', 'runserver']
import sys





def main():
    """
    STUDENT NOTE: This is the main function that gets called when we run the manage.py script.
    Its job is to set up the Django environment and then execute the appropriate management command.
    """
    
    # STUDENT NOTE: This is a crucial line! It tells Django which settings file to use.
    # 'DJANGO_SETTINGS_MODULE' is an environment variable that Django looks for to find its configuration.
    # We're setting it to 'marketpulse.settings', which means Django will look for a file called
    # settings.py inside the marketpulse directory. This is how Django knows all our project settings
    # like database connection, installed apps, etc.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketpulse.settings')
    
    # STUDENT NOTE: Now we try to import Django's management utility. This is wrapped in a try-except block
    # to provide a helpful error message if Django isn't properly installed.
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # STUDENT NOTE: If Django isn't installed or not accessible in the current Python environment,
        # we raise a more helpful ImportError with suggestions on what might be wrong.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # STUDENT NOTE: This is where the magic happens! We call Django's execute_from_command_line function
    # and pass it the command-line arguments (sys.argv). This function reads the arguments and executes
    # the appropriate Django management command. For example:
    # - "python manage.py runserver" starts the development server
    # - "python manage.py migrate" runs database migrations
    # - "python manage.py createsuperuser" creates an admin user
    # Django has many built-in management commands, and we can create custom ones too.
    execute_from_command_line(sys.argv)





# STUDENT NOTE: This is a standard Python construct. The code inside this if block will only run
# when the script is executed directly (not when imported as a module). When you run
# "python manage.py ..." from the command line, this condition is True and the main() function gets called.
if __name__ == '__main__':
    main()