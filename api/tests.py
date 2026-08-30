"""============================================================ API TESTS: verifies React health endpoint is publicly reachable. ============================================================"""
from django.test import TestCase
class ApiTests(TestCase):
    def test_health(self):
        r=self.client.get('/api/health/'); self.assertEqual(r.status_code,200); self.assertEqual(r.json()['status'],'ok')
