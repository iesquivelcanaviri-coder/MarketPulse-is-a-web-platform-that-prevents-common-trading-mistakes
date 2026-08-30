"""============================================================ STRATEGY ADMIN ============================================================"""
from django.contrib import admin
from .models import StrategyRule,BacktestTrade
admin.site.register(StrategyRule); admin.site.register(BacktestTrade)
# ============================================================
# STRATEGY LIBRARY - ADMIN
# ============================================================

from .models import StrategyLibraryItem


@admin.register(StrategyLibraryItem)
class StrategyLibraryItemAdmin(admin.ModelAdmin):

    # --------------------------------------------------------
    # Columns displayed in Django Admin
    # --------------------------------------------------------

    list_display = (
        "name",
        "category",
        "implementation_status",
        "is_active",
        "display_order",
    )


    # --------------------------------------------------------
    # Admin filters
    # --------------------------------------------------------

    list_filter = (
        "category",
        "implementation_status",
        "is_active",
    )


    # --------------------------------------------------------
    # Admin search
    # --------------------------------------------------------

    search_fields = (
        "name",
        "code",
        "description",
    )