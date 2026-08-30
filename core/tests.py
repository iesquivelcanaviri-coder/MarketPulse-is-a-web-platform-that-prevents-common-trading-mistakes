"""============================================================
CORE TESTS
Framework mapping: confirms Strategy uses rule_config without a reverse-relation clash.
============================================================"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Strategy
class CoreTests(TestCase):
    def test_rule_config(self):
        u=get_user_model().objects.create_user(username='u',password='ComplexPass123!'); s=Strategy.objects.create(user=u,name='S',rule_config={'risk':.01}); self.assertEqual(s.rule_config['risk'],.01)
