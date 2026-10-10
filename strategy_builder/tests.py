"""============================================================ STRATEGY FORM TESTS ============================================================"""

# ============================================================
# 1. IMPORTS
# ============================================================
from django.test import SimpleTestCase  # Import: I use Django's test class, which disallows database queries by default.
from .forms import StrategyCreateForm  # Relative import: I import the strategy form from this application's forms module.

# ============================================================
# 2. TEST CLASS
# ============================================================
class StrategyTests(SimpleTestCase):  # Class inheritance: I inherit Django's testing tools from SimpleTestCase.

    # --------------------------------------------------------
    # 2.1 CHECK INVALID PERIOD DATA
    # --------------------------------------------------------
    def test_period_validation(self):  # Method: The test runner discovers this test_ method; self refers to this test instance.
        f = StrategyCreateForm(data={  # Object creation and keyword argument: I bind the form to a dictionary of test inputs.
            'name': 'x',  # Dictionary entry and string: I provide a short strategy name.
            'description': '',  # Empty string: I leave the description blank.
            'symbol': 'AAPL',  # String value: I provide the asset symbol.
            'fast_period': 30,  # Integer value: I set the fast period higher than the slow period.
            'slow_period': 10,  # Integer value: I create the period combination this test expects to reject.
            'risk_per_trade': .01,  # Float value: I supply 0.01 for risk per trade.
            'stop_loss_pct': .05,  # Float value: I supply 0.05 for the stop-loss setting.
            'commission_pct': .001,  # Float value: I supply 0.001 for commission.
            'slippage_pct': .0005,  # Float value: I supply 0.0005 for slippage.
            'max_volume_pct': .02,  # Float value: I supply 0.02 for the volume limit.
            'max_daily_loss_pct': .03,  # Float value: I supply 0.03 for the daily-loss limit.
        })  # Closing delimiters: I finish the input dictionary and form-construction call.
        self.assertFalse(f.is_valid())  # Method calls and assertion: I validate the form and require the result to be False.