"""============================================================ STRATEGY FORM TESTS ============================================================"""
from django.test import SimpleTestCase
from .forms import StrategyCreateForm
class StrategyTests(SimpleTestCase):
    def test_period_validation(self):
        f=StrategyCreateForm(data={'name':'x','description':'','symbol':'AAPL','fast_period':30,'slow_period':10,'risk_per_trade':.01,'stop_loss_pct':.05,'commission_pct':.001,'slippage_pct':.0005,'max_volume_pct':.02,'max_daily_loss_pct':.03}); self.assertFalse(f.is_valid())
