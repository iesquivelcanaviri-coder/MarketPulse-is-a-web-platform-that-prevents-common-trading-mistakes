"""============================================================
ACCOUNTS TESTS
Framework mapping: verifies the registration form uses the custom user model.
============================================================"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from .forms import UserRegistrationForm
class RegistrationTests(TestCase):
    def test_custom_user_registration(self):
        f=UserRegistrationForm(data={'username':'demo','first_name':'Demo','last_name':'User','email':'demo@example.com','password1':'ComplexPass123!','password2':'ComplexPass123!'})
        self.assertTrue(f.is_valid(),f.errors); f.save(); self.assertTrue(get_user_model().objects.filter(username='demo').exists())
