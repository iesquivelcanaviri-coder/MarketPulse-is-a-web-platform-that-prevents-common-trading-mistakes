"""============================================================ DATA IMPORT FORM: browser → validation → DataImport model. ============================================================"""
# ============================================================
# 1. IMPORTS
# ============================================================
from django import forms  # I import Django's form classes, widgets and validation exception.
from .models import DataImport  # I import the model this form represents.
# ============================================================
# 2. MODEL-BASED IMPORT FORM
# ============================================================
class DataImportForm(forms.ModelForm):  # I inherit ModelForm so Django can build fields from DataImport.
    # --------------------------------------------------------
    # 2.1 MODEL, FIELDS AND WIDGETS
    # --------------------------------------------------------
    class Meta:  # I define the nested configuration class Django reads for this form.
        model = DataImport  # I connect the form to the DataImport model.
        fields = ('source', 'symbol', 'start_date', 'end_date')  # I choose the editable model fields and their order.
        widgets = {  # I define custom display widgets for selected fields.
            'start_date': forms.DateInput(  # I use a date input widget for the start date.
                attrs={'type': 'date'}  # I set the HTML input type to date.
            ),  # I finish the start-date widget.
            'end_date': forms.DateInput(  # I use a date input widget for the end date.
                attrs={'type': 'date'}  # I set this HTML input type to date too.
            )  # I finish the end-date widget.
        }  # I finish the widgets dictionary.
    # --------------------------------------------------------
    # 2.2 SYMBOL NORMALIZATION
    # --------------------------------------------------------
    def clean_symbol(self):  # I define the field-specific cleaning method Django calls for a valid symbol field.
        return self.cleaned_data['symbol'].strip().upper()  # I trim surrounding spaces and return an uppercase symbol.
    # --------------------------------------------------------
    # 2.3 DATE-RANGE VALIDATION
    # --------------------------------------------------------
    def clean(self):  # I define form-wide validation for the relationship between the dates.
        d = super().clean()  # I call the parent cleaning method and retain its cleaned-data dictionary.
        a = d.get('start_date')  # I read the cleaned start date, receiving None if it is absent.
        b = d.get('end_date')  # I read the cleaned end date, receiving None if it is absent.
        if a and b and a >= b:  # I check the ordering only when both dates exist; equal dates are also rejected.
            raise forms.ValidationError('End date must be later than start date.')  # I raise a form-wide validation error.
        return d  # I return the cleaned data when this date-range check passes.