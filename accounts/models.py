"""
============================================================
ACCOUNTS - MODELS
============================================================
Framework mapping: settings.AUTH_USER_MODEL points here; all financial apps reference this User.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    ROLE_CHOICES=[('trader','Trader'),('reviewer','Reviewer'),('admin','Admin')]
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default='trader')
    email_verified=models.BooleanField(default=False)
class UserProfile(models.Model):
    RISK_CHOICES=[('conservative','Conservative'),('moderate','Moderate'),('aggressive','Aggressive')]
    MARKET_CHOICES=[('stocks','Stocks'),('etfs','ETFs'),('crypto','Cryptocurrency'),('forex','Forex')]
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    bio=models.TextField(max_length=500,blank=True); location=models.CharField(max_length=80,blank=True)
    trading_experience=models.PositiveIntegerField(default=0)
    risk_tolerance=models.CharField(max_length=20,choices=RISK_CHOICES,default='moderate')
    max_daily_loss=models.DecimalField(max_digits=12,decimal_places=2,default=100)
    preferred_markets=models.CharField(max_length=20,choices=MARKET_CHOICES,default='stocks')
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    def __str__(self): return f'{self.user.username} profile'
