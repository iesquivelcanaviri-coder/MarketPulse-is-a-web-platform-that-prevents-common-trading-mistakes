"""============================================================ ANALYSIS MODEL TEST: expected market regime choices remain available. ============================================================"""
from django.test import SimpleTestCase
from .models import MarketRegime
class AnalysisTests(SimpleTestCase):
    def test_regimes(self):self.assertTrue({'bull','bear','sideways','volatile'}.issubset({x for x,_ in MarketRegime.REGIMES}))
