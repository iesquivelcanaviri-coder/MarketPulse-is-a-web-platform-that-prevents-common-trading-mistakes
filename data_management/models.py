"""
============================================================
DATA MANAGEMENT - MODELS
============================================================
Framework mapping: form/view/task track imports here; OHLCV observations are stored in core.MarketData.
"""
# ============================================================
# 1. IMPORTS
# ============================================================
from django.conf import settings  # I import access to the project's settings, including its user model.
from django.db import models  # I import Django's model fields and relationship tools.
from core.models import TimeStampedModel  # I import the shared base model whose definitions these classes inherit.
# ============================================================
# 2. DATA PROVIDER MODEL
# ============================================================
class DataSource(TimeStampedModel):  # I define a provider model that inherits from the shared base class.
    name = models.CharField(max_length=100, unique=True)  # I store a provider name of up to 100 characters and require uniqueness.
    url = models.URLField()  # I store a URL; this field does not make an HTTP request.
    api_key_required = models.BooleanField(default=False)  # I record whether credentials are required, defaulting to False.
    is_active = models.BooleanField(default=True)  # I record whether the provider is active, defaulting to True.
    # --------------------------------------------------------
    # 2.1 HUMAN-READABLE REPRESENTATION
    # --------------------------------------------------------
    def __str__(self):  # I define how this provider instance appears when converted to a string.
        return self.name  # I use its name as the readable representation.
# ============================================================
# 3. HISTORICAL IMPORT JOB MODEL
# ============================================================
class DataImport(TimeStampedModel):  # I define an import-job model using the same shared base class.
    # --------------------------------------------------------
    # 3.1 STATUS CHOICES
    # --------------------------------------------------------
    STATUS = [  # I create a list of stored-value and display-label pairs.
        ('pending', 'Pending'),  # I define the waiting status and its readable label.
        ('processing', 'Processing'),  # I define the running status and its readable label.
        ('completed', 'Completed'),  # I define the successful status and its readable label.
        ('failed', 'Failed'),  # I define the unsuccessful status and its readable label.
    ]  # I finish the choices list; it does not automatically move jobs between statuses.
    # --------------------------------------------------------
    # 3.2 USER AND PROVIDER RELATIONSHIPS
    # --------------------------------------------------------
    user = models.ForeignKey(  # I connect each import job to one user.
        settings.AUTH_USER_MODEL,  # I reference the user model configured by the project.
        on_delete=models.CASCADE,  # I let Django delete associated import jobs when their user is deleted.
        related_name='data_imports'  # I allow reverse access through user.data_imports.
    )  # I finish defining the user relationship.
    source = models.ForeignKey(  # I connect each import job to one provider.
        DataSource,  # I identify the related provider model.
        on_delete=models.PROTECT  # I prevent Django from deleting a provider referenced by import jobs.
    )  # I finish defining the provider relationship.
    # --------------------------------------------------------
    # 3.3 REQUESTED MARKET AND DATE RANGE
    # --------------------------------------------------------
    symbol = models.CharField(max_length=20)  # I store a symbol of up to 20 characters; this field does not uppercase it automatically.
    start_date = models.DateField()  # I store the requested historical start date.
    end_date = models.DateField()  # I store the requested historical end date.
    # --------------------------------------------------------
    # 3.4 JOB STATUS AND RESULT INFORMATION
    # --------------------------------------------------------
    status = models.CharField(  # I store the job's status as text.
        max_length=20,  # I allow up to 20 characters.
        choices=STATUS,  # I provide the supported values for model validation and form selection.
        default='pending'  # I start new jobs as pending when no status is supplied.
    )  # I finish defining the status field.
    records_imported = models.PositiveIntegerField(default=0)  # I store a nonnegative processed-record count, initially zero.
    error_message = models.TextField(blank=True)  # I store error text and allow it to be empty during validation.