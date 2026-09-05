"""
============================================================
MARKETPULSE - SEED MARKET DATA SOURCES
============================================================

FRAMEWORK MAPPING:

Django Management Command
    ↓
seed_marketpulse.py
    ↓
DataSource model
    ↓
PostgreSQL database
    ↓
MarketPulse Data tab


PURPOSE:

This command prepares the market-data provider used by
MarketPulse.

Alpaca is now the primary market-data provider.

The Alpaca API credentials are NOT stored in the database.
They are stored securely in environment variables and read
through Django settings.

Existing Yahoo Finance records are not deleted because older
DataImport records may still refer to them.

Instead, Yahoo Finance is marked inactive.

============================================================
"""


# ============================================================
# 1. DJANGO MANAGEMENT COMMAND IMPORT
# ============================================================

# BaseCommand is Django's standard class for creating custom
# commands that can be run through manage.py.
from django.core.management.base import BaseCommand


# ============================================================
# 2. MARKETPULSE MODEL IMPORT
# ============================================================

# DataSource stores information about external market-data
# providers that MarketPulse can use.
from data_management.models import DataSource


# ============================================================
# 3. SEED COMMAND
# ============================================================

class Command(BaseCommand):

    # This text appears when Django displays help information
    # for this management command.
    help = (
        "Creates or updates Alpaca as the primary MarketPulse "
        "market-data source and deactivates the old Yahoo "
        "Finance source."
    )


    # ========================================================
    # 4. COMMAND EXECUTION
    # ========================================================

    def handle(self, *args, **options):


        # ====================================================
        # 4.1 CREATE OR UPDATE ALPACA
        # ====================================================

        # update_or_create() makes the command safe to run more
        # than once.
        #
        # If Alpaca already exists, Django updates it.
        #
        # If Alpaca does not exist, Django creates it.
        alpaca_source, created = (
            DataSource.objects.update_or_create(

                name="Alpaca",

                defaults={

                    # This is only the public provider website.
                    #
                    # The actual API endpoints are configured
                    # separately in Django settings.
                    "url":
                        "https://alpaca.markets/",

                    # Alpaca requires authentication using an
                    # API key and secret key.
                    "api_key_required":
                        True,

                    # Alpaca is now the active market-data
                    # provider used by MarketPulse.
                    "is_active":
                        True,
                },
            )
        )


        # ====================================================
        # 4.2 DEACTIVATE OLD YAHOO FINANCE SOURCE
        # ====================================================

        # We deliberately do not delete Yahoo Finance.
        #
        # Older DataImport records may already reference the
        # Yahoo Finance DataSource through a database
        # relationship.
        #
        # Keeping the record preserves historical integrity,
        # while is_active=False prevents it from being treated
        # as the current primary provider.
        yahoo_updated = (
            DataSource.objects
            .filter(
                name="Yahoo Finance"
            )
            .update(
                is_active=False
            )
        )


        # ====================================================
        # 4.3 DISPLAY ALPACA RESULT
        # ====================================================

        if created:

            self.stdout.write(
                self.style.SUCCESS(
                    (
                        "Alpaca market-data source created "
                        f"successfully. DataSource ID: "
                        f"{alpaca_source.pk}"
                    )
                )
            )

        else:

            self.stdout.write(
                self.style.SUCCESS(
                    (
                        "Alpaca market-data source updated "
                        f"successfully. DataSource ID: "
                        f"{alpaca_source.pk}"
                    )
                )
            )


        # ====================================================
        # 4.4 DISPLAY YAHOO STATUS
        # ====================================================

        if yahoo_updated:

            self.stdout.write(
                self.style.WARNING(
                    (
                        "Yahoo Finance remains in the database "
                        "for historical records but has been "
                        "marked inactive."
                    )
                )
            )

        else:

            self.stdout.write(
                (
                    "No existing Yahoo Finance DataSource "
                    "needed to be deactivated."
                )
            )


        # ====================================================
        # 4.5 FINAL CONFIRMATION
        # ====================================================

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "MarketPulse primary market-data provider "
                    "is now configured as Alpaca."
                )
            )
        )