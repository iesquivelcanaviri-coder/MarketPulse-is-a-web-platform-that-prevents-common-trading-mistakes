"""============================================================ API TESTS: verifies React health endpoint is publicly reachable. ============================================================"""

# ============================================================
# 1. DJANGO TESTING IMPORT
# ============================================================

from django.test import TestCase  # IMPORT: brings Django's TestCase class into this file so I can create automated Django tests.

# ============================================================
# 2. API TEST CLASS
# ============================================================

class ApiTests(TestCase):  # CLASS + INHERITANCE: creates my ApiTests class and inherits Django testing features from TestCase.

    # ========================================================
    # 3. HEALTH ENDPOINT TEST
    # ========================================================

    def test_health(self):  # METHOD: defines one automated test; "self" refers to the current ApiTests object.
        r=self.client.get('/api/health/'); self.assertEqual(r.status_code,200); self.assertEqual(r.json()['status'],'ok')  # ASSIGNMENT + METHOD CALL + ASSERTIONS: sends a GET request, stores the response in "r", checks HTTP 200, converts the JSON response to Python data, accesses the "status" dictionary value, and checks that it equals "ok".