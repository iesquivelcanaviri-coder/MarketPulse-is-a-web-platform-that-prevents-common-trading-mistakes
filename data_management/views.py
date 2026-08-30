"""============================================================
DATA MANAGEMENT VIEWS
Framework mapping: form → synchronous service or Celery task → import history template.
============================================================"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from .forms import DataImportForm
from .models import DataImport
from .tasks import import_market_data_task
from .utils import import_yahoo_finance_data
@login_required
def data_import(request):
    f=DataImportForm(request.POST or None)
    if request.method=='POST' and f.is_valid():
        j=f.save(commit=False); j.user=request.user; j.save()
        if settings.USE_CELERY: import_market_data_task.delay(j.pk); messages.info(request,'Import queued.')
        else:
            try:j.status='processing'; j.save(); j.records_imported=import_yahoo_finance_data(j.symbol,j.start_date,j.end_date); j.status='completed'; messages.success(request,f'Imported {j.records_imported} rows.')
            except Exception as e:j.status='failed'; j.error_message=str(e); messages.error(request,str(e))
            j.save()
        return redirect('data_management:history')
    return render(request,'data_management/import.html',{'form':f})
@login_required
def import_history(request):return render(request,'data_management/history.html',{'imports':DataImport.objects.filter(user=request.user).select_related('source').order_by('-created_at')})
