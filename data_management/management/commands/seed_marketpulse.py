"""============================================================
SEED COMMAND
Framework mapping: creates the Yahoo Finance DataSource required by the import form.
============================================================"""
from django.core.management.base import BaseCommand
from data_management.models import DataSource
class Command(BaseCommand):
    def handle(self,*a,**k):
        obj,created=DataSource.objects.get_or_create(name='Yahoo Finance',defaults={'url':'https://finance.yahoo.com/','api_key_required':False,'is_active':True}); self.stdout.write(self.style.SUCCESS(f'Yahoo Finance source ready: {obj.pk}'))
