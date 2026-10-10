"""
============================================================
MARKETPULSE - ANALYSIS TOOLS TESTS
============================================================

FILE PURPOSE:

This file tests important behaviour in the analysis_tools app.

This specific test checks that the expected MarketPulse market
regime choices are still available in MarketRegime.REGIMES.

EXPECTED MARKET REGIMES:

bull
bear
sideways
volatile


============================================================
FRAMEWORK / APPLICATION FLOW
============================================================

Django Test Runner
        ↓
analysis_tools/tests.py
        ↓
MarketRegime
        ↓
analysis_tools/models.py
        ↓
MarketRegime.REGIMES
        ↓
Extract stored regime values
        ↓
Compare against expected values
        ↓
assertTrue(...)
        ↓
Test passes or fails


============================================================
CONNECTION TO MARKETPULSE
============================================================

Market Data
        ↓
analysis_tools
        ↓
MarketRegime
        ↓
bull / bear / sideways / volatile
        ↓
Market Condition analysis
        ↓
Strategy / model decision support


============================================================
LECTURE CONNECTION
============================================================

Programming Language Features / Concepts used here:

1. Modules and imports
2. Classes
3. Inheritance
4. Methods
5. Objects and self
6. Sets
7. Set literals
8. Set comprehensions
9. Iteration
10. Tuple unpacking
11. Method calls
12. Boolean values
13. Assertions
14. Automated testing
15. Attribute access

These are building blocks used by Python and Django to organise,
execute, and test application behaviour.
============================================================
"""

# ============================================================
# 1. DJANGO TESTING IMPORT
# ============================================================

from django.test import SimpleTestCase  # Import Django's lightweight test class for tests that do not need database queries. [Concept: Module import]

# ============================================================
# 2. LOCAL APPLICATION IMPORT
# ============================================================

from .models import MarketRegime  # Import MarketRegime from this app's models.py file so its REGIMES choices can be tested. [Concept: Relative import / module reuse]

# ============================================================
# 3. ANALYSIS TEST CLASS
# ============================================================

class AnalysisTests(SimpleTestCase):  # Create a test class that inherits Django testing features from SimpleTestCase. [Concept: Class / inheritance]

    # ========================================================
    # 4. MARKET REGIME CHOICES TEST
    # ========================================================

    def test_regimes(self):  # Define one automated test method; Django recognises it because its name begins with "test_". [Concept: Method / self / naming convention]
        self.assertTrue({'bull', 'bear', 'sideways', 'volatile'}.issubset({x for x, _ in MarketRegime.REGIMES}))  # Check that all four required regime values exist inside MarketRegime.REGIMES. [Concept: Assertion / Boolean / set / set comprehension / tuple unpacking / method call]