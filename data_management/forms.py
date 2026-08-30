"""============================================================ DATA IMPORT FORM: browser → validation → DataImport model. ============================================================"""
from django import forms
from .models import DataImport
class DataImportForm(forms.ModelForm):
    class Meta: model=DataImport; fields=('source','symbol','start_date','end_date'); widgets={'start_date':forms.DateInput(attrs={'type':'date'}),'end_date':forms.DateInput(attrs={'type':'date'})}
    def clean_symbol(self):return self.cleaned_data['symbol'].strip().upper()
    def clean(self):
        d=super().clean(); a=d.get('start_date'); b=d.get('end_date')
        if a and b and a>=b: raise forms.ValidationError('End date must be later than start date.')
        return d
