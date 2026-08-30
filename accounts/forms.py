"""
============================================================
ACCOUNTS - FORMS
Framework mapping: validates registration/profile data before saving accounts/models.py.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
User=get_user_model()
class UserRegistrationForm(UserCreationForm):
    email=forms.EmailField(required=True); first_name=forms.CharField(max_length=30,required=True); last_name=forms.CharField(max_length=30,required=True)
    class Meta: model=User; fields=('username','first_name','last_name','email','password1','password2')
    def clean_email(self):
        email=self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists(): raise forms.ValidationError('Email already registered.')
        return email
class UserProfileForm(forms.ModelForm):
    class Meta: model=UserProfile; fields=('bio','location','trading_experience','risk_tolerance','max_daily_loss','preferred_markets'); widgets={'bio':forms.Textarea(attrs={'rows':4})}
