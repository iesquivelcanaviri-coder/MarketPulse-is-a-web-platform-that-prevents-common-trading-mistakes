"""
============================================================
MARKETPULSE - STRATEGY LIBRARY SERVICE
============================================================

Framework mapping:

StrategyLibraryItem database
        ↓
get_grouped_strategy_library()
        ↓
strategy_builder/views.py
        +
data_management/views.py
        ↓
Django templates

This prevents the Data tab and Strategies tab from duplicating
the category-grouping logic.
============================================================
"""

from .models import StrategyLibraryItem


# ============================================================
# GROUP STRATEGIES BY CATEGORY
# ============================================================

def get_grouped_strategy_library():

    grouped_categories = []


    # --------------------------------------------------------
    # Maintain the exact academic category order
    # --------------------------------------------------------

    for category_code, category_label in (
        StrategyLibraryItem.CATEGORY_CHOICES
    ):

        items = list(
            StrategyLibraryItem.objects
            .filter(
                category=category_code,
                is_active=True,
            )
            .order_by(
                "display_order",
                "name",
            )
        )


        if items:

            grouped_categories.append(
                {
                    "code": category_code,
                    "label": category_label,
                    "items": items,
                }
            )


    return grouped_categories