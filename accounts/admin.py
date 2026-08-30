"""============================================================
ACCOUNTS ADMIN
Framework mapping: makes custom User/UserProfile visible in `/admin/`.
============================================================"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User,UserProfile
admin.site.register(User,UserAdmin); admin.site.register(UserProfile)
