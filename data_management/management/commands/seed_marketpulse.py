"""
============================================================
MARKETPULSE - SEED MARKET DATA SOURCES
============================================================

SHORT PURPOSE:

This file creates or updates the market-data provider records
required by MarketPulse.

When I run:

    python manage.py seed_marketpulse

Django automatically finds this management command and runs:

    Command.handle()

The command makes Alpaca the active MarketPulse market-data
provider and keeps any old Yahoo Finance record inactive.

No Alpaca API credentials are stored in this file or in the
DataSource database record.


============================================================
FRAMEWORK MAPPING
============================================================

Terminal
    ↓
python manage.py seed_marketpulse
    ↓
manage.py
    ↓
marketpulse/settings.py
    ↓
INSTALLED_APPS
    ↓
data_management
    ↓
management/commands/seed_marketpulse.py
    ↓
Command(BaseCommand)
    ↓
handle()
    ↓
DataSource.objects
    ↓
Django ORM
    ↓
PostgreSQL / Neon
    ↓
MarketPulse Data tab


============================================================
HOW THIS INTERACTS WITH THE PROJECT
============================================================

This command is not a normal browser view.

It is an administrator/developer command run from Terminal.

Its job is to prepare database configuration used later by:

data_management/forms.py
    ↓
data_management/views.py
    ↓
DataImport
    ↓
data_management/services/alpaca.py
    ↓
Alpaca API
    ↓
core.MarketData
    ↓
PostgreSQL
    ↓
Data tab


============================================================
ALPACA CONFIGURATION
============================================================

This command stores only general provider information such as:

    name
    url
    api_key_required
    is_active

Real credentials are NOT stored here.

The credentials follow this flow:

.env locally
or
Render Environment Variables
    ↓
marketpulse/settings.py
    ↓
ALPACA_API_KEY_ID
ALPACA_API_SECRET_KEY
    ↓
data_management/services/alpaca.py
    ↓
Alpaca API


============================================================
WHY YAHOO FINANCE IS NOT DELETED
============================================================

Older DataImport database records may still reference the
Yahoo Finance DataSource.

Deleting it could break those relationships.

Therefore MarketPulse keeps the old record but sets:

    is_active=False

This preserves historical database integrity while making
Alpaca the active provider.


============================================================
PROGRAMMING LANGUAGE CONCEPTS USED
============================================================

Import
    Reuses code from another Python module.

Class
    Groups related behaviour into an object definition.

Inheritance
    Command inherits Django behaviour from BaseCommand.

Method
    handle() defines what happens when the command runs.

Arguments
    *args and **options allow Django to supply command data.

Variable
    Stores a value so it can be reused.

Tuple unpacking
    Receives more than one value returned by update_or_create().

Dictionary
    Stores related key/value configuration data.

Boolean
    True and False represent yes/no program states.

Conditional
    if / else chooses which code executes.

ORM
    Django converts Python model queries into database queries.

Method chaining
    Multiple QuerySet methods are connected together.

String
    Stores text.

f-string
    Inserts a Python value inside text.

Object attribute
    alpaca_source.pk accesses data belonging to an object.

============================================================
"""


# ============================================================
# 1. DJANGO MANAGEMENT COMMAND IMPORT
# ============================================================

from django.core.management.base import BaseCommand  # IMPORT: reuse Django's BaseCommand class so this Python file becomes a Django management command.


# ============================================================
# 2. MARKETPULSE MODEL IMPORT
# ============================================================

from data_management.models import DataSource  # IMPORT: bring the DataSource Django model into this file so the command can read and update provider records.


# ============================================================
# 3. COMMAND CLASS
# ============================================================

class Command(BaseCommand):  # CLASS + INHERITANCE: create my Command class and inherit Django management-command behaviour from BaseCommand.

    # ========================================================
    # 3.1 COMMAND HELP TEXT
    # ========================================================

    help = (  # VARIABLE: Django reads this class variable when help information for the command is requested.
        "Creates or updates Alpaca as the primary MarketPulse "  # STRING: first part of the human-readable command description.
        "market-data source and deactivates the old Yahoo "  # STRING CONCATENATION: Python automatically joins adjacent strings inside parentheses.
        "Finance source."  # STRING: final part of the command description.
    )  # PARENTHESES: close the grouped multi-line string expression.

    # ========================================================
    # 4. COMMAND EXECUTION METHOD
    # ========================================================

    def handle(self, *args, **options):  # METHOD: Django automatically calls handle() when I run python manage.py seed_marketpulse.

        # ----------------------------------------------------
        # Programming concepts:
        #
        # self
        #     Refers to the current Command object.
        #
        # *args
        #     Collects extra positional arguments into a tuple.
        #
        # **options
        #     Collects command options into a dictionary.
        # ----------------------------------------------------

        # ====================================================
        # 4.1 CREATE OR UPDATE ALPACA
        # ====================================================

        alpaca_source, created = (  # TUPLE UNPACKING: update_or_create() returns the DataSource object and a True/False value showing whether it was newly created.
            DataSource.objects.update_or_create(  # DJANGO ORM: search for Alpaca and update it, or create it when it does not already exist.
                name="Alpaca",  # KEYWORD ARGUMENT: use the name field to identify the DataSource record.
                defaults={  # DICTIONARY: define the values Django should create or update on the Alpaca record.
                    "url": "https://alpaca.markets/",  # DICTIONARY KEY/VALUE: store Alpaca's public website URL, not an API credential.
                    "api_key_required": True,  # BOOLEAN: record that Alpaca requires API authentication.
                    "is_active": True,  # BOOLEAN: make Alpaca an active MarketPulse market-data source.
                },  # DICTIONARY: finish the defaults configuration.
            )  # METHOD CALL: finish update_or_create().
        )  # EXPRESSION: finish assigning the two returned values to alpaca_source and created.

        # ----------------------------------------------------
        # What update_or_create() means:
        #
        # Existing Alpaca record
        #         ↓
        # Update it
        #
        # No Alpaca record
        #         ↓
        # Create it
        #
        # This makes the command safe to run repeatedly.
        # ----------------------------------------------------

        # ====================================================
        # 4.2 DEACTIVATE OLD YAHOO FINANCE SOURCE
        # ====================================================

        yahoo_updated = (  # VARIABLE: store the number of Yahoo Finance database rows that Django changes.
            DataSource.objects  # MODEL MANAGER: start a Django ORM query using DataSource.
            .filter(  # QUERYSET METHOD: limit the query to matching database records.
                name="Yahoo Finance"  # KEYWORD ARGUMENT: only select the DataSource named Yahoo Finance.
            )  # METHOD CALL: finish the filter operation.
            .update(  # ORM UPDATE: change matching database rows directly.
                is_active=False  # BOOLEAN: mark Yahoo Finance inactive without deleting it.
            )  # METHOD CALL: finish the database update.
        )  # ASSIGNMENT: save the number of updated rows in yahoo_updated.

        # ----------------------------------------------------
        # Why update() instead of delete():
        #
        # Existing DataImport
        #       ↓
        # ForeignKey
        #       ↓
        # Yahoo Finance DataSource
        #
        # Keeping the DataSource protects older historical
        # database relationships.
        # ----------------------------------------------------

        # ====================================================
        # 4.3 DISPLAY WHETHER ALPACA WAS CREATED OR UPDATED
        # ====================================================

        if created:  # CONDITIONAL: run this block when update_or_create() tells us that Alpaca was newly created.
            self.stdout.write(  # METHOD CALL: write a message to the Terminal using Django's command output system.
                self.style.SUCCESS(  # METHOD CALL: format the Terminal message using Django's success style.
                    (  # PARENTHESES: group the multi-line string expression.
                        "Alpaca market-data source created "  # STRING: explain that a new provider record was created.
                        f"successfully. DataSource ID: "  # F-STRING: this string can contain Python expressions.
                        f"{alpaca_source.pk}"  # OBJECT ATTRIBUTE + F-STRING: insert the database primary key of the Alpaca DataSource.
                    )  # PARENTHESES: finish the message.
                )  # METHOD CALL: finish SUCCESS styling.
            )  # METHOD CALL: finish stdout.write().
        else:  # CONDITIONAL BRANCH: run this block when Alpaca already existed and was updated.
            self.stdout.write(  # METHOD CALL: send another status message to the Terminal.
                self.style.SUCCESS(  # METHOD CALL: display the message using Django's success formatting.
                    (  # PARENTHESES: group the multi-line text.
                        "Alpaca market-data source updated "  # STRING: explain that the existing record was updated.
                        f"successfully. DataSource ID: "  # F-STRING: text prepared to include a Python value.
                        f"{alpaca_source.pk}"  # OBJECT ATTRIBUTE: insert the Alpaca DataSource primary key.
                    )  # PARENTHESES: finish the message expression.
                )  # METHOD CALL: finish the success style.
            )  # METHOD CALL: finish writing to Terminal.

        # ====================================================
        # 4.4 DISPLAY YAHOO FINANCE STATUS
        # ====================================================

        if yahoo_updated:  # CONDITIONAL: a non-zero number is treated as True, meaning at least one Yahoo record was updated.
            self.stdout.write(  # METHOD CALL: write the Yahoo status to the Terminal.
                self.style.WARNING(  # METHOD CALL: use Django's warning style because an old provider has been disabled.
                    (  # PARENTHESES: group the multi-line message.
                        "Yahoo Finance remains in the database "  # STRING: explain that the record has not been deleted.
                        "for historical records but has been "  # STRING CONCATENATION: continue the explanation.
                        "marked inactive."  # STRING: explain the final database state.
                    )  # PARENTHESES: finish the text expression.
                )  # METHOD CALL: finish WARNING formatting.
            )  # METHOD CALL: finish Terminal output.
        else:  # CONDITIONAL BRANCH: this runs if no Yahoo Finance record existed or needed updating.
            self.stdout.write(  # METHOD CALL: write a normal informational message to Terminal.
                (  # PARENTHESES: group the multi-line string.
                    "No existing Yahoo Finance DataSource "  # STRING: explain that no matching provider was found.
                    "needed to be deactivated."  # STRING CONCATENATION: complete the informational message.
                )  # PARENTHESES: finish the text expression.
            )  # METHOD CALL: finish Terminal output.

        # ====================================================
        # 4.5 FINAL CONFIRMATION
        # ====================================================

        self.stdout.write(  # METHOD CALL: print the final command result to the Terminal.
            self.style.SUCCESS(  # METHOD CALL: format the final result as a successful operation.
                (  # PARENTHESES: group the message across multiple source-code lines.
                    "MarketPulse primary market-data provider "  # STRING: describe which configuration has been prepared.
                    "is now configured as Alpaca."  # STRING CONCATENATION: complete the confirmation.
                )  # PARENTHESES: finish the final message.
            )  # METHOD CALL: finish Django success formatting.
        )  # METHOD CALL: finish stdout.write().