"""
============================================================
MARKETPULSE - RISK MANAGEMENT TESTS
============================================================
PURPOSE:
These tests check the core mathematical calculations used by
the MarketPulse Risk workspace.
The current tests focus on:
1. Position sizing
2. Percentage-based stop-loss calculation
RISK WORKFLOW:
Trading Capital
    +
Maximum Risk Percentage
    +
Stop-Loss Distance
    +
Entry Price
    ↓
calculate_position_size()
    ↓
Risk-Constrained Position Size
Entry Price
    +
Stop-Loss Percentage
    ↓
calculate_stop_loss()
    ↓
Calculated Stop Price
WHY THESE TESTS MATTER:
The Risk page depends on these calculations when helping the
user estimate how large a hypothetical position can be while
remaining within a chosen maximum-loss budget.
These are unit tests only. They do not call Alpaca, PostgreSQL
or any external market-data service.
============================================================
"""  # Module docstring: explain the purpose of this test file.

# ============================================================
# 1. DJANGO TESTING IMPORT
# ============================================================
from django.test import SimpleTestCase  # Import: reuse Django's test class for tests without database access.

# ============================================================
# 2. RISK CALCULATOR IMPORTS
# ============================================================
from .calculators import (  # Relative import: load functions from this application's calculators module.
    calculate_position_size,  # Import the function that calculates position size.
    calculate_stop_loss,  # Import the function that calculates a stop price.
)  # Close the grouped import.

# ============================================================
# 3. TEST CLASS — GROUP RELATED CALCULATION TESTS
# ============================================================
class RiskCalculatorTests(SimpleTestCase):  # Inheritance: this class receives SimpleTestCase's testing tools.
    """
    ============================================================
    CORE RISK CALCULATION TESTS
    ============================================================
    These tests make sure the mathematical functions used by
    MarketPulse continue returning the expected values if the
    project is changed later.
    ============================================================
    """  # Class docstring: describe what this group of tests checks.

    # --------------------------------------------------------
    # 3.1 POSITION SIZE — ONE PERCENT RISK
    # --------------------------------------------------------
    def test_position_size_with_one_percent_risk(self):  # Method: define a test; self refers to this test instance.
        """
        A $10,000 account risking 1% has a $100 risk budget.
        Entry price:
            $50
        Stop distance:
            5%
        Risk per unit:
            $50 × 5% = $2.50
        Position size:
            $100 ÷ $2.50 = 40 units
        """  # Method docstring: explain the example's expected calculation.
        position_size = calculate_position_size(  # Assignment and function call: calculate and store the result.
            10000,  # First positional argument: trading capital of $10,000.
            0.01,  # Float literal: a risk fraction of 0.01 means 1%.
            0.05,  # Float literal: a stop-distance fraction of 0.05 means 5%.
            50,  # Integer literal: the entry price is $50.
        )  # Close the function call.
        self.assertAlmostEqual(  # Inherited method call: check that the result approximately equals the expected value.
            position_size,  # First argument: the actual result returned by the calculator.
            40,  # Second argument: the expected position size is 40 units.
        )  # Close the assertion; a failed comparison causes this test to fail.

    # --------------------------------------------------------
    # 3.2 POSITION SIZE — TWO PERCENT RISK
    # --------------------------------------------------------
    def test_position_size_with_two_percent_risk(self):  # Method: define another independently checked example.
        """
        This second example checks that the calculation also
        works when the user's risk budget is larger.
        Trading capital:
            $10,000
        Maximum risk:
            2% = $200
        Entry price:
            $100
        Stop distance:
            10%
        Risk per unit:
            $10
        Expected position:
            20 units
        """  # Method docstring: explain why this example should return 20 units.
        position_size = calculate_position_size(  # Function call: calculate position size using this example's inputs.
            10000,  # Trading capital: $10,000.
            0.02,  # Risk fraction: 0.02 means 2%, giving a $200 risk budget.
            0.10,  # Stop-distance fraction: 0.10 means 10%.
            100,  # Entry price: $100, giving $10 risk per unit at this stop distance.
        )  # Close the call and store its return value in position_size.
        self.assertAlmostEqual(  # Assertion: compare the calculated result with the expected answer.
            position_size,  # Actual result from the calculator.
            20,  # Expected result: $200 divided by $10 equals 20 units.
        )  # Close the assertion.

    # --------------------------------------------------------
    # 3.3 STOP PRICE — FIVE PERCENT BELOW ENTRY
    # --------------------------------------------------------
    def test_stop_loss_with_five_percent_distance(self):  # Method: define the five-percent stop-price test.
        """
        A 5% stop below a $100 entry price should create
        a stop price of $95.
        """  # Method docstring: explain the expected stop price.
        stop_price = calculate_stop_loss(  # Assignment and function call: calculate and store the stop price.
            100,  # First positional argument: the entry price is $100.
            0.05,  # Second positional argument: the stop distance is 5%.
        )  # Close the calculator call.
        self.assertAlmostEqual(  # Assertion: check the returned stop price.
            stop_price,  # Actual stop price returned by the function.
            95,  # Expected stop price: $100 minus $5 equals $95.
        )  # Close the assertion.

    # --------------------------------------------------------
    # 3.4 STOP PRICE — TEN PERCENT BELOW ENTRY
    # --------------------------------------------------------
    def test_stop_loss_with_ten_percent_distance(self):  # Method: define the ten-percent stop-price test.
        """
        A 10% stop below a $200 entry price should create
        a stop price of $180.
        """  # Method docstring: explain the expected answer for this example.
        stop_price = calculate_stop_loss(  # Function call: calculate the stop price for these inputs.
            200,  # Entry price: $200.
            0.10,  # Stop-distance fraction: 0.10 means 10%.
        )  # Close the call and store the result.
        self.assertAlmostEqual(  # Assertion: compare the actual and expected stop prices.
            stop_price,  # Actual calculated stop price.
            180,  # Expected stop price: $200 minus $20 equals $180.
        )  # Close the assertion.

    # --------------------------------------------------------
    # 3.5 STOP PRICE — SMALLER TWO PERCENT DISTANCE
    # --------------------------------------------------------
    def test_stop_loss_with_decimal_price(self):  # Preserve the original test name; the supplied price is the integer 50.
        """
        This test checks that the calculation also works with
        a decimal market price rather than only round numbers.
        Entry:
            $50
        Stop distance:
            2%
        Expected stop:
            $49
        """  # Preserve the original description; this example actually uses a whole-number entry price.
        stop_price = calculate_stop_loss(  # Function call: calculate the stop using a smaller percentage distance.
            50,  # Integer literal: the entry price is $50.
            0.02,  # Float literal: the stop distance is 2%.
        )  # Close the call and assign the result to stop_price.
        self.assertAlmostEqual(  # Assertion: check that the calculated stop matches the expected answer.
            stop_price,  # Actual stop price returned by the calculator.
            49,  # Expected stop price: $50 minus $1 equals $49.
        )  # Close the final assertion.