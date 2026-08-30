"""============================================================ RISK CALCULATOR TESTS ============================================================"""
from django.test import SimpleTestCase
from .calculators import calculate_position_size,calculate_stop_loss
class RiskTests(SimpleTestCase):
    def test_size(self):self.assertAlmostEqual(calculate_position_size(10000,.01,.05,50),40)
    def test_stop(self):self.assertAlmostEqual(calculate_stop_loss(100,.05),95)
