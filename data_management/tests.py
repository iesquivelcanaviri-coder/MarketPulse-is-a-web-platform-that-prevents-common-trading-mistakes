"""
DATA MANAGEMENT - FORM TESTS
Check historical import-form validation using Django's test database.
The Alpaca DataSource is a database fixture, not a live API connection.
Tests cover reversed dates, correctly ordered dates and lowercase symbols.
"""
# ============================================================
# 1. IMPORTS
# ============================================================
from django.test import TestCase  # I import Django's test class with database isolation support.
from .forms import DataImportForm  # I import the historical market-data form being tested.
from .models import DataSource  # I import the provider model needed by the form.
# ============================================================
# 2. TEST CLASS
# ============================================================
class DataTests(TestCase):  # I inherit Django's testing tools and assertion methods.
    # ========================================================
    # 2.1 SETUP BEFORE EACH TEST
    # ========================================================
    def setUp(self):  # I define the setup method that runs before each test.
        """Create an Alpaca provider record for the current test."""
        self.alpaca_source = DataSource.objects.create(  # I create and save a provider, then store it on this test instance.
            name="Alpaca",  # I give the provider its name.
            url="https://alpaca.markets/",  # I store its website address; this does not request the website.
            api_key_required=True,  # I mark the provider as requiring an API key.
            is_active=True,  # I make the provider active for form selection.
        )  # I finish creating the test provider.
    # ========================================================
    # 2.2 REJECT REVERSED DATES
    # ========================================================
    def test_invalid_date_range_is_rejected(self):  # I define a test method whose name starts with test_.
        """Expect the form to reject a start date after the end date."""
        form = DataImportForm(  # I construct the form to validate the supplied input.
            data={  # I supply a dictionary that binds values to the form.
                "source": self.alpaca_source.pk,  # I identify the provider using its database primary key.
                "symbol": "AAPL",  # I supply an uppercase ticker.
                "start_date": "2026-02-02",  # I intentionally supply a later start date.
                "end_date": "2026-01-01",  # I supply an earlier end date.
            }  # I finish the input dictionary.
        )  # I finish constructing the bound form.
        self.assertFalse(  # I require the validation result to be false.
            form.is_valid()  # I run form validation and obtain its Boolean result.
        )  # I finish the assertion.
    # ========================================================
    # 2.3 ACCEPT CORRECTLY ORDERED DATES
    # ========================================================
    def test_valid_date_range_is_accepted(self):  # I define the valid-input test.
        """Expect the form to accept correctly ordered dates."""
        form = DataImportForm(  # I construct another bound form.
            data={  # I supply the test's form values.
                "source": self.alpaca_source.pk,  # I select the provider created for this test.
                "symbol": "AAPL",  # I supply the ticker.
                "start_date": "2026-01-01",  # I supply the earlier date as the start.
                "end_date": "2026-02-02",  # I supply the later date as the end.
            }  # I finish the input dictionary.
        )  # I finish constructing the form.
        self.assertTrue(  # I require the validation result to be true.
            form.is_valid(),  # I run validation and pass its result to the assertion.
            form.errors,  # I provide form errors as the diagnostic message if the assertion fails.
        )  # I finish the assertion.
    # ========================================================
    # 2.4 ACCEPT A LOWERCASE SYMBOL
    # ========================================================
    def test_symbol_can_be_submitted_in_lowercase(self):  # I define the lowercase-input test.
        """Expect lowercase ticker input to be accepted with otherwise valid values."""
        form = DataImportForm(  # I construct the form for this input case.
            data={  # I supply its bound input values.
                "source": self.alpaca_source.pk,  # I select this test's provider.
                "symbol": "aapl",  # I intentionally supply the ticker in lowercase.
                "start_date": "2026-01-01",  # I supply a valid start date.
                "end_date": "2026-02-02",  # I supply a later end date.
            }  # I finish the input dictionary.
        )  # I finish constructing the form.
        self.assertTrue(  # I require the form to accept these values.
            form.is_valid(),  # I run validation and check its result.
            form.errors,  # I include validation errors in a failure message.
        )  # I finish the assertion.