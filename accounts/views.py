"""============================================================
ACCOUNTS - VIEWS
Framework mapping: URLs call these handlers; forms validate data; templates render results.
============================================================"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from .forms import UserRegistrationForm,UserProfileForm
from .models import UserProfile
def register(request):
    form=UserRegistrationForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save(); UserProfile.objects.get_or_create(user=user); messages.success(request,'Account created. You can now log in.'); return redirect('accounts:login')
    return render(request,'accounts/register.html',{'form':form})
@login_required
def profile(request):
    obj,_=UserProfile.objects.get_or_create(user=request.user); form=UserProfileForm(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid(): form.save(); messages.success(request,'Profile updated.'); return redirect('accounts:profile')
    return render(request,'accounts/profile.html',{'form':form})
