"""
============================================================
DATA MANAGEMENT - FORM TESTS
============================================================

PURPOSE:

These tests check that the MarketPulse historical market-data
import form validates user input correctly.

The tests do NOT make a real request to Alpaca.

This is important because automated tests should not depend on:

- Internet availability
- Live Alpaca API responses
- API rate limits
- Real API credentials

The Alpaca DataSource created below is therefore only a test
database record used by DataImportForm.

============================================================
"""


# ============================================================
# 1. DJANGO TEST IMPORT
# ============================================================

# TestCase provides Django's testing framework and creates
# an isolated temporary test database for each test run.
from django.test import TestCase


# ============================================================
# 2. MARKETPULSE IMPORTS
# ============================================================

# DataImportForm is the form used by the Data tab when a user
# requests historical market data.
from .forms import DataImportForm


# DataSource identifies the external market-data provider
# associated with a historical data import.
from .models import DataSource


# ============================================================
# 3. DATA IMPORT FORM TESTS
# ============================================================

class DataTests(TestCase):


    # ========================================================
    # 3.1 TEST SETUP
    # ========================================================

    def setUp(self):
        """
        Create an Alpaca DataSource that can be reused by
        each test.

        This does not contact Alpaca.

        It only creates a temporary database record inside
        Django's test database.
        """

        self.alpaca_source = DataSource.objects.create(
            name="Alpaca",
            url="https://alpaca.markets/",
            api_key_required=True,
            is_active=True,
        )


    # ========================================================
    # 3.2 INVALID DATE RANGE
    # ========================================================

    def test_invalid_date_range_is_rejected(self):
        """
        The historical-data import form should reject a date
        range where the start date occurs after the end date.

        Example:

        Start:
            2 February 2026

        End:
            1 January 2026

        This validation happens before MarketPulse attempts
        to retrieve market data from Alpaca.
        """

        form = DataImportForm(
            data={
                "source":
                    self.alpaca_source.pk,

                "symbol":
                    "AAPL",

                "start_date":
                    "2026-02-02",

                "end_date":
                    "2026-01-01",
            }
        )


        # The form should be invalid because the start date
        # occurs after the requested end date.
        self.assertFalse(
            form.is_valid()
        )


    # ========================================================
    # 3.3 VALID DATE RANGE
    # ========================================================

    def test_valid_date_range_is_accepted(self):
        """
        A correctly ordered historical date range should pass
        the form's date validation.

        This still does not contact Alpaca because validating
        the Django form does not download market data.
        """

        form = DataImportForm(
            data={
                "source":
                    self.alpaca_source.pk,

                "symbol":
                    "AAPL",

                "start_date":
                    "2026-01-01",

                "end_date":
                    "2026-02-02",
            }
        )


        self.assertTrue(
            form.is_valid(),
            form.errors,
        )


    # ========================================================
    # 3.4 SYMBOL NORMALISATION
    # ========================================================

    def test_symbol_can_be_submitted_in_lowercase(self):
        """
        Users may enter a ticker using lowercase characters.

        The form should still accept the input if the remaining
        fields are valid.

        Symbol normalisation to uppercase can then happen in
        the form or import-processing layer.
        """

        form = DataImportForm(
            data={
                "source":
                    self.alpaca_source.pk,

                "symbol":
                    "aapl",

                "start_date":
                    "2026-01-01",

                "end_date":
                    "2026-02-02",
            }
        )


        self.assertTrue(
            form.is_valid(),
            form.errors,
        )