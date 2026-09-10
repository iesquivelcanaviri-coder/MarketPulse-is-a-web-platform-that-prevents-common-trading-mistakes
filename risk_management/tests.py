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
"""


# ============================================================
# 1. DJANGO TESTING IMPORT
# ============================================================

# SimpleTestCase is appropriate because these tests only check
# mathematical Python functions and do not need the database.
from django.test import SimpleTestCase


# ============================================================
# 2. MARKETPULSE RISK CALCULATOR IMPORTS
# ============================================================

from .calculators import (
    calculate_position_size,
    calculate_stop_loss,
)


# ============================================================
# 3. RISK CALCULATOR TESTS
# ============================================================

class RiskCalculatorTests(SimpleTestCase):
    """
    ============================================================
    CORE RISK CALCULATION TESTS
    ============================================================

    These tests make sure the mathematical functions used by
    MarketPulse continue returning the expected values if the
    project is changed later.
    ============================================================
    """


    # ========================================================
    # 3.1 POSITION SIZE - ORIGINAL EXAMPLE
    # ========================================================

    def test_position_size_with_one_percent_risk(self):
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
        """

        position_size = calculate_position_size(
            10000,
            0.01,
            0.05,
            50,
        )

        self.assertAlmostEqual(
            position_size,
            40,
        )


    # ========================================================
    # 3.2 POSITION SIZE - SECOND EXAMPLE
    # ========================================================

    def test_position_size_with_two_percent_risk(self):
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
        """

        position_size = calculate_position_size(
            10000,
            0.02,
            0.10,
            100,
        )

        self.assertAlmostEqual(
            position_size,
            20,
        )


    # ========================================================
    # 3.3 STOP-LOSS - FIVE PERCENT
    # ========================================================

    def test_stop_loss_with_five_percent_distance(self):
        """
        A 5% stop below a $100 entry price should create
        a stop price of $95.
        """

        stop_price = calculate_stop_loss(
            100,
            0.05,
        )

        self.assertAlmostEqual(
            stop_price,
            95,
        )


    # ========================================================
    # 3.4 STOP-LOSS - TEN PERCENT
    # ========================================================

    def test_stop_loss_with_ten_percent_distance(self):
        """
        A 10% stop below a $200 entry price should create
        a stop price of $180.
        """

        stop_price = calculate_stop_loss(
            200,
            0.10,
        )

        self.assertAlmostEqual(
            stop_price,
            180,
        )


    # ========================================================
    # 3.5 SMALLER STOP DISTANCE
    # ========================================================

    def test_stop_loss_with_decimal_price(self):
        """
        This test checks that the calculation also works with
        a decimal market price rather than only round numbers.

        Entry:
            $50

        Stop distance:
            2%

        Expected stop:
            $49
        """

        stop_price = calculate_stop_loss(
            50,
            0.02,
        )

        self.assertAlmostEqual(
            stop_price,
            49,
        )